from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class BotConfig:
    bot_api_key: str
    allowed_chat_id: int


@dataclass(frozen=True)
class IPMonitorConfig:
    ips: list[str]
    target_chat: str
    bot_api_key: str
    port: int
    timezone: str
    quiet_start: int
    quiet_end: int
    rounds: int
    interval_seconds: int
    timeout_seconds: int


@dataclass(frozen=True)
class ProxyNotifyConfig:
    target_chat: str
    timezone: str
    bot_api_key: str


@dataclass(frozen=True)
class ProxyTarget:
    name: str
    type: str
    host: str
    port: int
    enabled: bool = True
    username: str | None = None
    password: str | None = None
    secret: str | None = None


@dataclass(frozen=True)
class ProxyTargetsConfig:
    targets: list[ProxyTarget]
    timeout_seconds: int
    rounds: int
    interval_seconds: int
    target_chat: str
    timezone: str


def resolve_config_path(path: Path) -> Path:
    if path.exists():
        return path
    if path.name.endswith('.local.json'):
        fallback = path.with_name(path.name.replace('.local.json', '.example.json'))
        if fallback.exists():
            return fallback
    return path


def load_json(path: Path) -> dict[str, Any]:
    path = resolve_config_path(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ConfigError(f"Config not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e}") from e


def require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"Config field '{key}' must be a non-empty string")
    return value


def require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"Config field '{key}' must be an integer")
    return value


def load_ip_monitor_config(path: Path) -> IPMonitorConfig:
    data = load_json(path)
    ips = data.get("ips")
    if not isinstance(ips, list) or not all(isinstance(ip, str) for ip in ips):
        raise ConfigError("Config field 'ips' must be a list of strings")

    bot_api_key = os.environ.get("NET_BOT_TELEGRAM_TOKEN")
    if not isinstance(bot_api_key, str) or not bot_api_key:
        raise ConfigError("Set NET_BOT_TELEGRAM_TOKEN for IP monitor notifications")

    rounds = data.get("rounds", 5)
    interval_seconds = data.get("interval_seconds", 60)
    timeout_seconds = data.get("timeout_seconds", 3)
    if not isinstance(rounds, int) or rounds < 1:
        raise ConfigError("Config field 'rounds' must be an integer >= 1")
    if not isinstance(interval_seconds, int) or interval_seconds < 0:
        raise ConfigError("Config field 'interval_seconds' must be an integer >= 0")
    if not isinstance(timeout_seconds, int) or timeout_seconds < 1:
        raise ConfigError("Config field 'timeout_seconds' must be an integer >= 1")

    return IPMonitorConfig(
        ips=ips,
        target_chat=require_str(data, "target_chat"),
        bot_api_key=bot_api_key,
        port=require_int(data, "port"),
        timezone=require_str(data, "timezone"),
        quiet_start=require_int(data, "quiet_start"),
        quiet_end=require_int(data, "quiet_end"),
        rounds=rounds,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
    )


def load_proxy_targets_config(path: Path) -> ProxyTargetsConfig:
    data = load_json(path)
    raw_targets = data.get("targets", [])
    if not isinstance(raw_targets, list):
        raise ConfigError("Config field 'targets' must be a list")

    targets: list[ProxyTarget] = []
    for idx, raw in enumerate(raw_targets, start=1):
        if not isinstance(raw, dict):
            raise ConfigError(f"Config target #{idx} must be an object")
        targets.append(
            ProxyTarget(
                name=str(raw.get("name", f"target-{idx}")),
                type=str(raw.get("type", "")).strip(),
                host=require_str(raw, "host"),
                port=require_int(raw, "port"),
                enabled=bool(raw.get("enabled", True)),
                username=raw.get("username") if isinstance(raw.get("username"), str) else None,
                password=raw.get("password") if isinstance(raw.get("password"), str) else None,
                secret=raw.get("secret") if isinstance(raw.get("secret"), str) else None,
            )
        )

    return ProxyTargetsConfig(
        targets=targets,
        timeout_seconds=int(data.get("timeout_seconds", 5)),
        rounds=int(data.get("rounds", 1)),
        interval_seconds=int(data.get("interval_seconds", 1)),
        target_chat=require_str(data, "target_chat"),
        timezone=require_str(data, "timezone"),
    )


def load_proxy_notify_config(path: Path) -> ProxyNotifyConfig:
    data = load_json(path)
    bot_api_key = os.environ.get("NET_BOT_TELEGRAM_TOKEN")
    if not isinstance(bot_api_key, str) or not bot_api_key:
        raise ConfigError("Set NET_BOT_TELEGRAM_TOKEN for proxy monitor notifications")
    return ProxyNotifyConfig(
        target_chat=require_str(data, "target_chat"),
        timezone=require_str(data, "timezone"),
        bot_api_key=bot_api_key,
    )


def load_bot_config(path: Path) -> BotConfig:
    data = load_json(path)
    token = os.environ.get("NET_BOT_TELEGRAM_TOKEN") or data.get("bot_api_key")
    if not isinstance(token, str) or not token:
        raise ConfigError("Config field 'bot_api_key' must be a non-empty string (or set NET_BOT_TELEGRAM_TOKEN)")
    return BotConfig(
        bot_api_key=token,
        allowed_chat_id=require_int(data, "allowed_chat_id"),
    )
