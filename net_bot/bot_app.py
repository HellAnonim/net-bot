from __future__ import annotations

import json
import socket
import time
import urllib.error
from datetime import datetime
from pathlib import Path

from .config import load_bot_config
from .ip_monitor import IPMonitor
from .proxy_monitor import ProxyMonitor
from .telegram_api import TelegramClient

REPLY_KEYBOARD = {
    "keyboard": [
        [{"text": "Test IP"}, {"text": "Test Proxy"}],
        [{"text": "IP problems"}, {"text": "Proxy problems"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}


class NetBot:
    def __init__(self, root: Path):
        self.root = root
        self.config = load_bot_config(root / "config" / "bot.local.json")
        self.telegram = TelegramClient(self.config["bot_api_key"])
        self.ip_monitor = IPMonitor(
            config_path=root / "config" / "ip_monitor.local.json",
            state_path=root / "state" / "ip-monitor-state.json",
            down_log_path=root / "logs" / "ip-monitor-down.log",
        )
        self.proxy_monitor = ProxyMonitor(
            targets_config=root / "config" / "proxies.local.json",
            notify_config=root / "config" / "proxy_notify.local.json",
            report_path=root / "state" / "proxy-report.json",
            prev_report_path=root / "state" / "proxy-report.prev.json",
            down_log_path=root / "logs" / "proxy-monitor-down.log",
        )

    def _fmt_ts(self, raw: str) -> str:
        if not raw:
            return "unknown time"
        try:
            return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M")
        except Exception:
            return raw

    def format_ip_problems(self) -> str:
        state_path = self.root / "state" / "ip-monitor-state.json"
        if not state_path.exists():
            return "Последняя проверка IP: данные не найдены"
        data = json.loads(state_path.read_text(encoding="utf-8"))
        servers = data.get("servers", {})
        if not servers:
            return "Последняя проверка IP: данные не найдены"
        latest_raw = max((info.get("last_check", "") for info in servers.values()), default="")
        latest = self._fmt_ts(latest_raw)
        down = [ip for ip, info in servers.items() if info.get("status") == "DOWN" and info.get("last_check", "") == latest_raw]
        lines = [f"Последняя проверка IP ({latest}):"]
        lines.extend([f"- недоступен сервер {ip}" for ip in sorted(down)] or ["- проблем не обнаружено"])
        return "\n".join(lines)

    def format_proxy_problems(self) -> str:
        report_path = self.root / "state" / "proxy-report.json"
        if not report_path.exists():
            return "Последняя проверка proxy: данные не найдены"
        data = json.loads(report_path.read_text(encoding="utf-8"))
        checked_at = data.get("checked_at")
        ts = datetime.fromtimestamp(checked_at).strftime("%Y-%m-%d %H:%M") if checked_at else "unknown time"
        targets = data.get("targets", [])
        down = [t for t in targets if t.get("status") != "UP"]
        lines = [f"Последняя проверка proxy ({ts}):"]
        if not down:
            lines.append("- проблем не обнаружено")
        else:
            for t in down:
                lines.append(f"- недоступен {t.get('type')} {t.get('host')}:{t.get('port')}")
        return "\n".join(lines)

    def handle_start(self, chat_id: int) -> None:
        self.telegram.send_message(chat_id, "Выбери действие:", REPLY_KEYBOARD)

    def handle_text(self, chat_id: int, text: str) -> None:
        text = text.strip()
        if text == "Test IP":
            self.telegram.send_message(chat_id, "Запускаю IP Tester...", REPLY_KEYBOARD)
            self.ip_monitor.run()
            self.telegram.send_message(chat_id, self.format_ip_problems(), REPLY_KEYBOARD)
            return
        if text == "Test Proxy":
            self.telegram.send_message(chat_id, "Запускаю Proxy Tester...", REPLY_KEYBOARD)
            self.proxy_monitor.run_tester()
            self.telegram.send_message(chat_id, self.format_proxy_problems(), REPLY_KEYBOARD)
            return
        if text == "IP problems":
            self.telegram.send_message(chat_id, self.format_ip_problems(), REPLY_KEYBOARD)
            return
        if text == "Proxy problems":
            self.telegram.send_message(chat_id, self.format_proxy_problems(), REPLY_KEYBOARD)
            return
        self.telegram.send_message(chat_id, "Нажми кнопку ниже.", REPLY_KEYBOARD)

    def run(self) -> None:
        offset = None
        while True:
            try:
                params: dict[str, int] = {"timeout": 30}
                if offset is not None:
                    params["offset"] = offset
                res = self.telegram.request("getUpdates", params, timeout=35)
                for upd in res.get("result", []):
                    offset = upd["update_id"] + 1
                    if "message" not in upd:
                        continue
                    msg = upd["message"]
                    chat_id = msg.get("chat", {}).get("id")
                    if chat_id != self.config["allowed_chat_id"]:
                        continue
                    if msg.get("text") == "/start":
                        self.handle_start(chat_id)
                    else:
                        self.handle_text(chat_id, msg.get("text") or "")
            except (TimeoutError, socket.timeout, urllib.error.URLError):
                time.sleep(2)
                continue
            except Exception:
                time.sleep(3)
                continue
            time.sleep(1)
