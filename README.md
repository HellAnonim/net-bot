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

This project uses configuration files from the `config/` directory.

The application looks for local runtime configs first:
- `*.local.json`

If a local file is missing, it falls back to the corresponding example file:
- `*.example.json`

### `config/bot.example.json`

Telegram bot configuration.

Purpose:
- defines which Telegram chat is allowed to use the bot
- can optionally provide a bot token for local bot runtime

Main fields:
- `allowed_chat_id` — Telegram chat ID allowed to interact with the bot
- `bot_api_key` — optional Telegram bot token

Notes:
- for public repositories, keep this file as an example only
- for local usage, create `config/bot.local.json`

### `config/ip_monitor.example.json`

IP monitor configuration.

Purpose:
- defines which IP addresses should be checked
- defines how the TCP availability check is performed
- defines where notifications should be sent

Main fields:
- `ips` — list of IP addresses to monitor
- `target_chat` — Telegram chat ID that receives monitor notifications
- `port` — TCP port to check
- `timezone` — timezone used for timestamps and quiet hours
- `quiet_start` — quiet hours start (hour)
- `quiet_end` — quiet hours end (hour)
- `rounds` — number of check rounds before final status is decided
- `interval_seconds` — delay between rounds
- `timeout_seconds` — timeout for a single TCP connection attempt

Notes:
- IP monitor notifications use `NET_BOT_TELEGRAM_TOKEN`
- typical use case: SSH availability monitoring on port `22`

### `config/proxies.example.json`

Proxy monitor configuration.

Purpose:
- defines proxy targets to test
- defines how proxy checks are performed
- defines where proxy notifications should be sent

Top-level fields:
- `targets` — list of proxy definitions
- `timeout_seconds` — timeout for a single proxy check
- `rounds` — number of rounds
- `interval_seconds` — delay between rounds
- `target_chat` — Telegram chat ID for proxy notifications
- `timezone` — timezone used in notification timestamps

Each target in `targets` may include:
- `name` — human-readable proxy name
- `type` — proxy type: `mtproto`, `socks5`, or `http`
- `host` — proxy host or IP
- `port` — proxy port
- `enabled` — whether the target should be checked

Additional fields by type:

For `mtproto`:
- `secret` — optional MTProto secret

For `socks5`:
- `username` — optional username
- `password` — optional password

For `http`:
- `username` — optional username
- `password` — optional password

Notes:
- proxy monitor notifications use `NET_BOT_TELEGRAM_TOKEN`
- MTProto checks are network-level probes, not full Telegram client authorization

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
