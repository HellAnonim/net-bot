# net_bot

Unified network monitoring project extracted from three older workspace projects:

- `ip_tester` — SSH/TCP availability monitoring
- `proxy_tester` — Telegram proxy checks (MTProto / SOCKS5 / HTTP CONNECT)
- `test_bot` — Telegram control bot

This repository is structured to be portable to GitHub as a single project.

## Features

- Telegram bot with simple menu:
  - `Test IP`
  - `Test Proxy`
  - `IP problems`
  - `Proxy problems`
- IP monitor with Telegram notifications on status changes
- Proxy monitor with Telegram notifications on DOWN transitions
- Shared project layout with `config/`, `state/`, `logs/`, and Python package code in `net_bot/`

## Project layout

```text
net_bot/
  README.md
  .gitignore
  config/
    bot.example.json
    ip_monitor.example.json
    proxy_notify.example.json
    proxies.example.json
    *.local.json          # local secrets / real infra, gitignored
  logs/
  state/
  net_bot/
    __init__.py
    bot_app.py
    cli.py
    config.py
    ip_monitor.py
    proxy_monitor.py
    telegram_api.py
```

## Configuration model

The project now separates public examples from local secrets:

- committed to git:
  - `config/*.example.json`
- local runtime files (ignored by git):
  - `config/*.local.json`

The code looks for `*.local.json` first and falls back to `*.example.json`.

Telegram token policy:
- kept only in local `config/bot.json` / `config/bot.local.json` if you want
- monitors use `NET_BOT_TELEGRAM_TOKEN` from environment
- example configs do not contain `bot_api_key`

Telegram token may also be provided via environment variable:

```bash
export NET_BOT_TELEGRAM_TOKEN="<telegram-bot-token>"
```

## Run

From project root:

```bash
python3 -m net_bot.cli run-bot
python3 -m net_bot.cli run-ip-monitor
python3 -m net_bot.cli run-proxy-monitor
python3 -m net_bot.cli check-proxies
```

Or install as a local package and use the CLI entrypoint:

```bash
pip install -e .
net-bot run-bot
```

## GitHub readiness notes

This project is now safer to publish because local runtime configs are gitignored.

Before pushing publicly, still review:

1. `config/proxies.example.json` — may still contain real infrastructure data if you copied it from production
2. `state/` and `logs/` — runtime data should usually stay out of the repo
3. add optional polish if desired:
   - `LICENSE`
   - `pyproject.toml`
   - systemd unit examples
   - GitHub Actions / CI

## Why this merge is useful

The old workspace had three separate mini-projects with overlapping logic and duplicated Telegram/API handling. `net_bot` consolidates them into one project with:

- one package
- one CLI entrypoint
- one Telegram API client
- clearer repository structure
- example configs separated from local secrets
