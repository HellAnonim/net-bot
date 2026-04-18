from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def fmt_iso_ts(raw: str) -> str:
    if not raw:
        return "unknown time"
    try:
        return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw


def format_ip_problems_from_state(state_path: Path) -> str:
    if not state_path.exists():
        return "Последняя проверка IP: данные не найдены"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    servers = data.get("servers", {})
    if not servers:
        return "Последняя проверка IP: данные не найдены"
    latest_raw = max((info.get("last_check", "") for info in servers.values()), default="")
    latest = fmt_iso_ts(latest_raw)
    down = [ip for ip, info in servers.items() if info.get("status") == "DOWN" and info.get("last_check", "") == latest_raw]
    lines = [f"Последняя проверка IP ({latest}):"]
    lines.extend([f"- недоступен сервер {ip}" for ip in sorted(down)] or ["- проблем не обнаружено"])
    return "\n".join(lines)


def format_proxy_problems_from_report(report_path: Path) -> str:
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
