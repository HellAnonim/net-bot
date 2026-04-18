# net_bot

Unified network monitoring project extracted from three older workspace projects.

Единый проект для сетевого мониторинга, собранный из трёх старых workspace-проектов.

- `ip_tester` — SSH/TCP availability monitoring  
  `ip_tester` — мониторинг доступности SSH/TCP
- `proxy_tester` — Telegram proxy checks (MTProto / SOCKS5 / HTTP CONNECT)  
  `proxy_tester` — проверка Telegram-прокси (MTProto / SOCKS5 / HTTP CONNECT)
- `test_bot` — Telegram control bot  
  `test_bot` — Telegram-бот для управления

This repository is structured to be portable to GitHub as a single project.

Этот репозиторий подготовлен так, чтобы его можно было удобно выкладывать на GitHub как единый проект.

## Features / Возможности

- Telegram bot with simple menu:  
  Telegram-бот с простым меню:
  - `Test IP`
  - `Test Proxy`
  - `IP problems`
  - `Proxy problems`
- IP monitor with Telegram notifications on status changes  
  Мониторинг IP с Telegram-уведомлениями при смене статуса
- Proxy monitor with Telegram notifications on DOWN transitions  
  Мониторинг прокси с Telegram-уведомлениями при переходе в DOWN
- Shared project layout with `config/`, `state/`, `logs/`, and Python package code in `net_bot/`  
  Общая структура проекта с `config/`, `state/`, `logs/` и Python-пакетом `net_bot/`

## Project layout / Структура проекта

```text
net_bot/
  README.md
  .gitignore
  config/
    bot.example.json
    ip_monitor.example.json
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

## Configuration model / Модель конфигурации

The project separates public examples from local secrets.

Проект разделяет публичные примеры конфигурации и локальные секреты.

- committed to git / коммитится в git:
  - `config/*.example.json`
- local runtime files (ignored by git) / локальные runtime-файлы (игнорируются git):
  - `config/*.local.json`

The code looks for `*.local.json` first and falls back to `*.example.json`.

Код сначала ищет `*.local.json`, а если его нет — использует `*.example.json`.

`proxies.json` now contains both:

`proxies.json` теперь содержит и то, и другое:
- proxy target definitions  
  описание proxy-целей
- proxy notification settings (`target_chat`, `timezone`)  
  настройки уведомлений (`target_chat`, `timezone`)

Telegram token policy:

Политика по Telegram token:
- kept only in local `config/bot.json` / `config/bot.local.json` if you want  
  при желании хранится только в локальном `config/bot.json` / `config/bot.local.json`
- monitors use `NET_BOT_TELEGRAM_TOKEN` from environment  
  мониторы используют `NET_BOT_TELEGRAM_TOKEN` из переменной окружения
- example configs do not contain `bot_api_key`  
  example-конфиги не содержат `bot_api_key`

Telegram token may also be provided via environment variable:

Telegram token также можно передавать через переменную окружения:

```bash
export NET_BOT_TELEGRAM_TOKEN="<telegram-bot-token>"
```

## Run / Запуск

From project root:

Из корня проекта:

```bash
python3 -m net_bot.cli run-bot
python3 -m net_bot.cli run-ip-monitor
python3 -m net_bot.cli run-proxy-monitor
python3 -m net_bot.cli check-proxies
```

Or install as a local package and use the CLI entrypoint:

Или установить как локальный пакет и использовать CLI entrypoint:

```bash
pip install -e .
net-bot run-bot
```

## GitHub readiness notes / Замечания перед публикацией на GitHub

This project is safer to publish because local runtime configs are gitignored.

Этот проект безопаснее публиковать, потому что локальные runtime-конфиги игнорируются через git.

Before pushing publicly, still review:

Перед публичным push всё равно стоит проверить:

1. `config/proxies.example.json` — may still contain real infrastructure data if you copied it from production  
   `config/proxies.example.json` — может всё ещё содержать реальные данные инфраструктуры, если был скопирован из продакшена
2. `state/` and `logs/` — runtime data should usually stay out of the repo  
   `state/` и `logs/` — runtime-данные обычно не стоит хранить в репозитории
3. add optional polish if desired:  
   при желании можно добавить ещё немного полировки:
   - `LICENSE`
   - `pyproject.toml`
   - systemd unit examples
   - GitHub Actions / CI

## Why this merge is useful / Почему такое объединение полезно

The old workspace had three separate mini-projects with overlapping logic and duplicated Telegram/API handling. `net_bot` consolidates them into one project with:

В старом workspace было три отдельных мини-проекта с пересекающейся логикой и дублирующейся работой с Telegram/API. `net_bot` объединяет их в один проект с:

- one package  
  одним пакетом
- one CLI entrypoint  
  одной CLI-точкой входа
- one Telegram API client  
  одним клиентом Telegram API
- clearer repository structure  
  более понятной структурой репозитория
- example configs separated from local secrets  
  разделением example-конфигов и локальных секретов
