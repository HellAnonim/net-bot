from __future__ import annotations

import json
import os
import socket
import time
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import IPMonitorConfig, load_ip_monitor_config
from .telegram_api import TelegramClient

logger = logging.getLogger(__name__)


class IPMonitor:
    def __init__(self, config_path: Path, state_path: Path, down_log_path: Path):
        self.config_path = config_path
        self.state_path = state_path
        self.down_log_path = down_log_path

    def _in_quiet_hours(self, tz: ZoneInfo, quiet_start: int, quiet_end: int) -> bool:
        h = datetime.now(tz).hour
        return h >= quiet_start or h < quiet_end

    def _tcp_check_once(self, ip: str, port: int, timeout_seconds: int) -> bool:
        try:
            with socket.create_connection((ip, port), timeout=timeout_seconds):
                return True
        except Exception:
            return False

    def _load_state(self, ips: list[str]) -> dict:
        state = {"servers": {ip: {"status": "UNKNOWN"} for ip in ips}}
        if not self.state_path.exists():
            return state
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return state
        existing = raw.get("servers", {}) if isinstance(raw, dict) else {}
        for ip in ips:
            if isinstance(existing.get(ip), dict):
                state["servers"][ip] = existing[ip]
        return state

    def _save_state(self, state: dict) -> None:
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log_down_servers(self, down_ips: list[str], checked_at_iso: str) -> None:
        if not down_ips:
            return
        with self.down_log_path.open("a", encoding="utf-8") as f:
            for ip in down_ips:
                f.write(f'"{ip}" - "{checked_at_iso}"\n')

    def run(self) -> dict:
        config: IPMonitorConfig = load_ip_monitor_config(self.config_path)
        ips = config.ips
        port = config.port
        tz = ZoneInfo(config.timezone)
        rounds = config.rounds
        interval_seconds = config.interval_seconds
        timeout_seconds = config.timeout_seconds
        logger.info("Starting IP monitor: ips=%s port=%s rounds=%s", len(ips), port, rounds)

        state = self._load_state(ips)
        servers = state.setdefault("servers", {})
        for ip in ips:
            servers.setdefault(ip, {"status": "UNKNOWN"})

        fail_counts = {ip: 0 for ip in ips}
        for i in range(rounds):
            for ip in ips:
                if not self._tcp_check_once(ip, port, timeout_seconds):
                    fail_counts[ip] += 1
            if i < rounds - 1:
                time.sleep(interval_seconds)

        quiet = self._in_quiet_hours(tz, config.quiet_start, config.quiet_end)
        checked_at_iso = datetime.now(tz).isoformat()
        down_now: list[str] = []
        messages: list[str] = []

        for ip in ips:
            new_status = "DOWN" if fail_counts[ip] == rounds else "UP"
            old_status = servers[ip].get("status", "UNKNOWN")
            servers[ip]["last_check"] = checked_at_iso
            servers[ip]["last_fail_count"] = fail_counts[ip]
            servers[ip]["status"] = new_status

            if new_status == "DOWN":
                down_now.append(ip)

            manual_mode = os.environ.get("NET_BOT_IP_MANUAL") == "1"
            should_notify_down = new_status == "DOWN" if manual_mode else old_status in {"UP", "UNKNOWN"} and new_status == "DOWN"
            should_notify_up = old_status == "DOWN" and new_status == "UP"

            if not quiet:
                now_label = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
                if should_notify_down:
                    messages.append(f"IP-тест сообщает: не работает сервер {ip} ({now_label})")
                elif should_notify_up:
                    messages.append(f"IP-тест сообщает: сервер {ip} снова доступен ({now_label})")

        self._save_state(state)
        self._log_down_servers(down_now, checked_at_iso)

        if messages:
            tg = TelegramClient(config.bot_api_key)
            for text in messages:
                tg.send_message(config.target_chat, text)

        logger.info("IP monitor finished: down=%s notifications=%s", len(down_now), len(messages))
        return state
