from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bot_app import NetBot
from .ip_monitor import IPMonitor
from .proxy_monitor import ProxyMonitor, run_checks
from .config import load_proxy_targets_config
import asyncio


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified net bot: Telegram bot + IP monitor + proxy monitor")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent), help="Project root")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run-bot", help="Run Telegram bot")
    sub.add_parser("run-ip-monitor", help="Run IP monitor once")
    sub.add_parser("run-proxy-monitor", help="Run proxy monitor once and notify")
    sub.add_parser("check-proxies", help="Run proxy checks and print JSON report")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    root = Path(args.root).resolve()

    if args.command == "run-bot":
        NetBot(root).run()
        return

    if args.command == "run-ip-monitor":
        IPMonitor(
            config_path=root / "config" / "ip_monitor.local.json",
            state_path=root / "state" / "ip-monitor-state.json",
            down_log_path=root / "logs" / "ip-monitor-down.log",
        ).run()
        return

    if args.command == "run-proxy-monitor":
        monitor = ProxyMonitor(
            targets_config=root / "config" / "proxies.local.json",
            notify_config=root / "config" / "proxy_notify.local.json",
            report_path=root / "state" / "proxy-report.json",
            prev_report_path=root / "state" / "proxy-report.prev.json",
            down_log_path=root / "logs" / "proxy-monitor-down.log",
        )
        monitor.run_tester()
        monitor.notify_if_needed()
        return

    if args.command == "check-proxies":
        cfg = load_proxy_targets_config(root / "config" / "proxies.local.json")
        report = asyncio.run(run_checks(cfg))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
