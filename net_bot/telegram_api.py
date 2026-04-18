from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


class TelegramClient:
    def __init__(self, token: str):
        self.token = token

    def request(self, method: str, data: dict[str, Any], timeout: int = 35) -> dict[str, Any]:
        payload = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=payload,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def send_message(self, chat_id: int | str, text: str, reply_markup: dict[str, Any] | None = None) -> None:
        data: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
        self.request("sendMessage", data)
