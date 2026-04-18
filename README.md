# net_bot

Network monitoring project.

`net_bot` combines three practical functions in one repository:

- IP availability monitoring over TCP
- proxy monitoring for Telegram-related proxy types
- a Telegram bot for manual checks and quick status lookup

## What the project does

The project can:

- check a list of servers on a TCP port (for example, SSH on port `22`)
- check proxies of these types:
  - `mtproto`
  - `socks5`
  - `http` (`CONNECT` probe)
- send Telegram notifications when monitored targets go down
- provide a simple Telegram bot menu for manual checks

## Main components

- `net_bot/ip_monitor.py` — IP/TCP monitor
- `net_bot/proxy_monitor.py` — proxy checker and notifier
- `net_bot/bot_app.py` — Telegram bot
- `net_bot/cli.py` — CLI entrypoint
- `net_bot/telegram_api.py` — minimal Telegram API client
- `net_bot/config.py` — config loading and validation

## Repository structure

```text
net_bot/
  README.md
  README_RU.md
  .gitignore
  pyproject.toml
  LICENSE
  config/
    bot.example.json
    ip_monitor.example.json
    proxies.example.json
    *.local.json
  logs/
  state/
  systemd/
  net_bot/
```

## Configuration

The repository uses two config layers:

- example configs committed to git:
  - `config/*.example.json`
- local runtime configs ignored by git:
  - `config/*.local.json`

The code tries `*.local.json` first and falls back to `*.example.json`.

### Telegram token

Use environment variable for monitors:

```bash
export NET_BOT_TELEGRAM_TOKEN="<telegram-bot-token>"
```

The bot itself can also use local `config/bot.local.json` if needed.

### Config files

- `config/bot.example.json` — Telegram bot settings
- `config/ip_monitor.example.json` — IP monitor settings
- `config/proxies.example.json` — proxy targets and proxy notification settings

### Proxy config

`proxies.json` contains both:

- proxy target definitions
- proxy notification settings such as `target_chat` and `timezone`

## Running the project

From the repository root:

```bash
python3 -m net_bot.cli run-bot
python3 -m net_bot.cli run-ip-monitor
python3 -m net_bot.cli run-proxy-monitor
python3 -m net_bot.cli check-proxies
```

Or install locally:

```bash
pip install -e .
net-bot run-bot
```

## Telegram bot commands and actions

The Telegram bot provides a simple keyboard with these actions:

- `Test IP` — run the IP monitor manually
- `Test Proxy` — run the proxy monitor manually
- `IP problems` — show the latest IP issues from saved state
- `Proxy problems` — show the latest proxy issues from saved state

## State and logs

Runtime files are stored in:

- `state/` — latest reports and monitor state
- `logs/` — down-event logs

These files are operational data and should normally stay local.

## systemd examples

The `systemd/` directory contains example service and timer units for:

- Telegram bot
- IP monitor
- proxy monitor

Use them as templates for deployment.

## Typical deployment flow

1. Copy example configs to local configs
2. Fill in real targets and chat settings
3. Set `NET_BOT_TELEGRAM_TOKEN`
4. Test manually with CLI commands
5. Enable systemd services/timers if needed

## Notes

- `mtproto` checks are network-level probes, not full Telegram client authorization
- proxy checks are focused on practical reachability and handshake validation
- runtime files in `state/` and `logs/` are not intended for public repository content
