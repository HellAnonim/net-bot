from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .config import load_proxy_notify_config, load_proxy_targets_config
from .telegram_api import TelegramClient


@dataclass
class CheckResult:
    name: str
    ptype: str
    host: str
    port: int
    ok: bool
    latency_ms: int | None
    detail: str


def _validate_mtproto_secret(secret: str | None) -> tuple[bool, str]:
    if not secret:
        return True, "no secret provided"
    s = secret.strip().lower().replace("0x", "")
    if len(s) not in (32, 34, 64):
        return False, "invalid secret length"
    try:
        bytes.fromhex(s)
        return True, "secret format ok"
    except Exception:
        return False, "secret is not hex"


async def _tcp_connect(host: str, port: int, timeout: float) -> tuple[bool, int | None, str, tuple[asyncio.StreamReader, asyncio.StreamWriter] | None]:
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        latency = int((time.perf_counter() - started) * 1000)
        return True, latency, "tcp connected", (reader, writer)
    except Exception as e:
        return False, None, f"tcp failed: {e}", None


async def check_mtproto(target: dict[str, Any], timeout: float) -> CheckResult:
    name = target.get("name", "mtproto")
    host, port = target["host"], int(target["port"])
    secret_ok, secret_msg = _validate_mtproto_secret(target.get("secret"))
    if not secret_ok:
        return CheckResult(name, "mtproto", host, port, False, None, secret_msg)
    ok, latency, detail, conn = await _tcp_connect(host, port, timeout)
    if conn:
        _, w = conn
        w.close()
        await w.wait_closed()
    return CheckResult(name, "mtproto", host, port, ok, latency, f"{detail}; {secret_msg}")


async def check_socks5(target: dict[str, Any], timeout: float) -> CheckResult:
    name = target.get("name", "socks5")
    host, port = target["host"], int(target["port"])
    username = target.get("username")
    password = target.get("password")
    ok, latency, detail, conn = await _tcp_connect(host, port, timeout)
    if not ok or not conn:
        return CheckResult(name, "socks5", host, port, False, latency, detail)
    r, w = conn
    try:
        w.write(b"\x05\x01\x02" if username and password else b"\x05\x01\x00")
        await w.drain()
        resp = await asyncio.wait_for(r.readexactly(2), timeout=timeout)
        if resp[0] != 0x05:
            return CheckResult(name, "socks5", host, port, False, latency, "invalid socks version")
        method = resp[1]
        if method == 0x02:
            if not (username and password):
                return CheckResult(name, "socks5", host, port, False, latency, "auth required")
            ub = username.encode()
            pb = password.encode()
            w.write(bytes([0x01, len(ub)]) + ub + bytes([len(pb)]) + pb)
            await w.drain()
            aresp = await asyncio.wait_for(r.readexactly(2), timeout=timeout)
            if aresp[1] != 0x00:
                return CheckResult(name, "socks5", host, port, False, latency, "auth failed")
        elif method != 0x00:
            return CheckResult(name, "socks5", host, port, False, latency, f"unsupported method {method}")
        return CheckResult(name, "socks5", host, port, True, latency, "handshake ok")
    except Exception as e:
        return CheckResult(name, "socks5", host, port, False, latency, f"handshake failed: {e}")
    finally:
        w.close()
        await w.wait_closed()


async def check_http(target: dict[str, Any], timeout: float) -> CheckResult:
    name = target.get("name", "http")
    host, port = target["host"], int(target["port"])
    username = target.get("username")
    password = target.get("password")
    ok, latency, detail, conn = await _tcp_connect(host, port, timeout)
    if not ok or not conn:
        return CheckResult(name, "http", host, port, False, latency, detail)
    r, w = conn
    try:
        headers = [
            "CONNECT api.telegram.org:443 HTTP/1.1",
            "Host: api.telegram.org:443",
            "Proxy-Connection: Keep-Alive",
        ]
        if username and password:
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers.append(f"Proxy-Authorization: Basic {token}")
        req = "\r\n".join(headers) + "\r\n\r\n"
        w.write(req.encode())
        await w.drain()
        line = await asyncio.wait_for(r.readline(), timeout=timeout)
        if not line:
            return CheckResult(name, "http", host, port, False, latency, "no response")
        status_line = line.decode(errors="ignore").strip()
        if " 200 " in status_line:
            return CheckResult(name, "http", host, port, True, latency, status_line)
        if " 407 " in status_line:
            return CheckResult(name, "http", host, port, False, latency, "proxy auth required/failed")
        return CheckResult(name, "http", host, port, False, latency, status_line)
    except Exception as e:
        return CheckResult(name, "http", host, port, False, latency, f"connect probe failed: {e}")
    finally:
        w.close()
        await w.wait_closed()


async def check_target(target: dict[str, Any], timeout: float) -> CheckResult:
    ptype = str(target.get("type", "")).lower().strip()
    if ptype == "mtproto":
        return await check_mtproto(target, timeout)
    if ptype == "socks5":
        return await check_socks5(target, timeout)
    if ptype == "http":
        return await check_http(target, timeout)
    return CheckResult(target.get("name", "unknown"), ptype or "unknown", target.get("host", "?"), int(target.get("port", 0)), False, None, "unsupported type")


async def run_checks(config: dict[str, Any]) -> dict[str, Any]:
    timeout = float(config.get("timeout_seconds", 5))
    rounds = int(config.get("rounds", 1))
    interval = float(config.get("interval_seconds", 1))
    targets = list(config.get("targets", []))
    active_targets = [t for t in targets if t.get("enabled", True)]
    all_rounds: list[list[CheckResult]] = []
    if not active_targets:
        return {"checked_at": int(time.time()), "rounds": rounds, "targets": []}
    for i in range(rounds):
        results = await asyncio.gather(*(check_target(t, timeout) for t in active_targets))
        all_rounds.append(results)
        if i < rounds - 1:
            await asyncio.sleep(interval)
    agg = []
    by_name: dict[str, list[CheckResult]] = {}
    for round_res in all_rounds:
        for r in round_res:
            by_name.setdefault(r.name, []).append(r)
    for name, vals in by_name.items():
        ok = any(v.ok for v in vals)
        latencies = [v.latency_ms for v in vals if v.latency_ms is not None]
        agg.append({
            "name": name,
            "type": vals[0].ptype,
            "host": vals[0].host,
            "port": vals[0].port,
            "status": "UP" if ok else "DOWN",
            "best_latency_ms": min(latencies) if latencies else None,
            "details": [v.detail for v in vals],
        })
    return {"checked_at": int(time.time()), "rounds": rounds, "targets": agg}


class ProxyMonitor:
    def __init__(self, targets_config: Path, notify_config: Path, report_path: Path, prev_report_path: Path, down_log_path: Path):
        self.targets_config = targets_config
        self.notify_config = notify_config
        self.report_path = report_path
        self.prev_report_path = prev_report_path
        self.down_log_path = down_log_path

    def _append_down_log(self, down: list[dict], checked_at_iso: str) -> None:
        if not down:
            return
        with self.down_log_path.open("a", encoding="utf-8") as f:
            for t in down:
                addr = f"{t['host']}:{t['port']}"
                proto = t.get("type", "unknown")
                f.write(f'"{addr}" - "{proto}" - "{checked_at_iso}"\n')

    def run_tester(self) -> dict[str, Any]:
        cfg = load_proxy_targets_config(self.targets_config)
        report = asyncio.run(run_checks(cfg))
        if self.report_path.exists():
            self.prev_report_path.write_text(self.report_path.read_text(encoding="utf-8"), encoding="utf-8")
        self.report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def build_message(self) -> str:
        notify_config = load_proxy_notify_config(self.notify_config)
        tz = ZoneInfo(notify_config["timezone"])
        data = json.loads(self.report_path.read_text(encoding="utf-8"))
        targets = data.get("targets", [])
        down = [t for t in targets if t.get("status") != "UP"]
        checked_at_iso = datetime.now(tz).isoformat()
        now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        manual_mode = os.environ.get("NET_BOT_PROXY_MANUAL") == "1"
        self._append_down_log(down, checked_at_iso)
        if not down:
            return ""
        if not manual_mode and self.prev_report_path.exists():
            try:
                prev = json.loads(self.prev_report_path.read_text(encoding="utf-8"))
                prev_targets = {t["name"]: t.get("status") for t in prev.get("targets", [])}
                changed_down = [t for t in down if prev_targets.get(t["name"]) != "DOWN"]
                if not changed_down:
                    return ""
                down = changed_down
            except Exception:
                pass
        lines = [f"Proxy-тест сообщает: не работают {len(down)} прокси ({now})"]
        for t in down:
            lines.append(f"- {t['type']} {t['host']}:{t['port']} ({t['name']})")
        return "\n".join(lines)

    def notify_if_needed(self) -> None:
        cfg = load_proxy_notify_config(self.notify_config)
        msg = self.build_message()
        if msg:
            TelegramClient(cfg["bot_api_key"]).send_message(cfg["target_chat"], msg)
