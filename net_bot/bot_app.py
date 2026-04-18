from __future__ import annotations

import logging
import socket
import time
import urllib.error
from pathlib import Path

from .config import BotConfig, load_bot_config
from .formatters import format_ip_problems_from_state, format_proxy_problems_from_report
from .ip_monitor import IPMonitor
from .proxy_monitor import ProxyMonitor
from .telegram_api import TelegramAPIError, TelegramClient

logger = logging.getLogger(__name__)


class BotActionError(RuntimeError):
    pass

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
        self.config: BotConfig = load_bot_config(root / "config" / "bot.local.json")
        self.telegram = TelegramClient(self.config.bot_api_key)
        self.ip_monitor = IPMonitor(
            config_path=root / "config" / "ip_monitor.local.json",
            state_path=root / "state" / "ip-monitor-state.json",
            down_log_path=root / "logs" / "ip-monitor-down.log",
        )
        self.proxy_monitor = ProxyMonitor(
            targets_config=root / "config" / "proxies.local.json",
            notify_config=root / "config" / "proxies.local.json",
            report_path=root / "state" / "proxy-report.json",
            prev_report_path=root / "state" / "proxy-report.prev.json",
            down_log_path=root / "logs" / "proxy-monitor-down.log",
        )

    def format_ip_problems(self) -> str:
        return format_ip_problems_from_state(self.root / "state" / "ip-monitor-state.json")

    def format_proxy_problems(self) -> str:
        return format_proxy_problems_from_report(self.root / "state" / "proxy-report.json")

    def handle_start(self, chat_id: int) -> None:
        self.telegram.send_message(chat_id, "Выбери действие:", REPLY_KEYBOARD)

    def _run_ip_check(self, chat_id: int) -> None:
        logger.info("Manual IP check requested by chat_id=%s", chat_id)
        self.telegram.send_message(chat_id, "Запускаю IP Tester...", REPLY_KEYBOARD)
        self.ip_monitor.run()
        self.telegram.send_message(chat_id, self.format_ip_problems(), REPLY_KEYBOARD)

    def _run_proxy_check(self, chat_id: int) -> None:
        logger.info("Manual proxy check requested by chat_id=%s", chat_id)
        self.telegram.send_message(chat_id, "Запускаю Proxy Tester...", REPLY_KEYBOARD)
        self.proxy_monitor.run_tester()
        self.telegram.send_message(chat_id, self.format_proxy_problems(), REPLY_KEYBOARD)

    def _send_ip_problems(self, chat_id: int) -> None:
        self.telegram.send_message(chat_id, self.format_ip_problems(), REPLY_KEYBOARD)

    def _send_proxy_problems(self, chat_id: int) -> None:
        self.telegram.send_message(chat_id, self.format_proxy_problems(), REPLY_KEYBOARD)

    def handle_text(self, chat_id: int, text: str) -> None:
        text = text.strip()
        actions = {
            "Test IP": self._run_ip_check,
            "Test Proxy": self._run_proxy_check,
            "IP problems": self._send_ip_problems,
            "Proxy problems": self._send_proxy_problems,
        }
        action = actions.get(text)
        if action:
            action(chat_id)
            return
        self.telegram.send_message(chat_id, "Нажми кнопку ниже.", REPLY_KEYBOARD)

    def run(self) -> None:
        logger.info("Starting Telegram bot polling")
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
                    if chat_id != self.config.allowed_chat_id:
                        logger.warning("Ignoring update from unauthorized chat_id=%s", chat_id)
                        continue
                    try:
                        if msg.get("text") == "/start":
                            self.handle_start(chat_id)
                        else:
                            self.handle_text(chat_id, msg.get("text") or "")
                    except TelegramAPIError:
                        logger.exception("Telegram API error while handling message for chat_id=%s", chat_id)
                    except Exception:
                        logger.exception("Unexpected error while handling message for chat_id=%s", chat_id)
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                logger.debug("Temporary polling condition: %s", exc)
                time.sleep(2)
                continue
            except TelegramAPIError:
                logger.exception("Telegram API polling failure")
                time.sleep(3)
                continue
            except Exception:
                logger.exception("Unexpected polling loop failure")
                time.sleep(3)
                continue
            time.sleep(1)
