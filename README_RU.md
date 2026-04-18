# net_bot

Проект для сетевого мониторинга.

- `ip_tester` — мониторинг доступности SSH/TCP
- `proxy_tester` — проверка Telegram-прокси (MTProto / SOCKS5 / HTTP CONNECT)
- `test_bot` — Telegram-бот для управления

## Возможности

- Telegram-бот с простым меню:
  - `Test IP`
  - `Test Proxy`
  - `IP problems`
  - `Proxy problems`
- Мониторинг IP с Telegram-уведомлениями при смене статуса
- Мониторинг прокси с Telegram-уведомлениями при переходе в DOWN
- Общая структура проекта с `config/`, `state/`, `logs/` и Python-пакетом `net_bot/`

## Структура проекта

```text
net_bot/
  README.md
  README_RU.md
  .gitignore
  config/
    bot.example.json
    ip_monitor.example.json
    proxies.example.json
    *.local.json          # локальные секреты / реальная инфраструктура, игнорируются git
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

## Модель конфигурации

Проект разделяет публичные примеры конфигурации и локальные секреты.

- коммитится в git:
  - `config/*.example.json`
- локальные runtime-файлы (игнорируются git):
  - `config/*.local.json`

Код сначала ищет `*.local.json`, а если его нет — использует `*.example.json`.

`proxies.json` теперь содержит и то, и другое:
- описание proxy-целей
- настройки уведомлений (`target_chat`, `timezone`)

Политика по Telegram token:
- при желании хранится только в локальном `config/bot.json` / `config/bot.local.json`
- мониторы используют `NET_BOT_TELEGRAM_TOKEN` из переменной окружения
- example-конфиги не содержат `bot_api_key`

Telegram token также можно передавать через переменную окружения:

```bash
export NET_BOT_TELEGRAM_TOKEN="<telegram-bot-token>"
```

## Запуск

Из корня проекта:

```bash
python3 -m net_bot.cli run-bot
python3 -m net_bot.cli run-ip-monitor
python3 -m net_bot.cli run-proxy-monitor
python3 -m net_bot.cli check-proxies
```

Или установить как локальный пакет и использовать CLI entrypoint:

```bash
pip install -e .
net-bot run-bot
```

## Замечания перед публикацией на GitHub

Этот проект безопаснее публиковать, потому что локальные runtime-конфиги игнорируются через git.

Перед публичным push всё равно стоит проверить:

1. `config/proxies.example.json` — может всё ещё содержать реальные данные инфраструктуры, если был скопирован из продакшена
2. `state/` и `logs/` — runtime-данные обычно не стоит хранить в репозитории
3. при желании можно добавить ещё немного полировки:
   - `LICENSE`
   - `pyproject.toml`
   - systemd unit examples
   - GitHub Actions / CI

