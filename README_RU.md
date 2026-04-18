# net_bot

Проект для сетевого мониторинга.

`net_bot` объединяет в одном репозитории три практические задачи:

- мониторинг доступности IP/серверов по TCP
- мониторинг прокси для Telegram-сценариев
- Telegram-бот для ручных проверок и быстрого просмотра статуса

## Что делает проект

Проект умеет:

- проверять список серверов по TCP-порту (например, SSH на порту `22`)
- проверять прокси следующих типов:
  - `mtproto`
  - `socks5`
  - `http` (`CONNECT` probe)
- отправлять Telegram-уведомления, когда мониторируемые цели становятся недоступны
- давать простой Telegram-интерфейс для ручных проверок

## Основные компоненты

- `net_bot/ip_monitor.py` — мониторинг IP/TCP
- `net_bot/proxy_monitor.py` — проверка прокси и отправка уведомлений
- `net_bot/bot_app.py` — Telegram-бот
- `net_bot/cli.py` — CLI-точка входа
- `net_bot/telegram_api.py` — минимальный клиент Telegram API
- `net_bot/config.py` — загрузка и валидация конфигов

## Структура репозитория

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

## Конфигурация

В репозитории используется два слоя конфигов:

- example-конфиги, которые хранятся в git:
  - `config/*.example.json`
- локальные runtime-конфиги, которые игнорируются git:
  - `config/*.local.json`

Код сначала пытается использовать `*.local.json`, а если таких файлов нет — берёт `*.example.json`.

### Telegram token

Для мониторов токен лучше передавать через переменную окружения:

```bash
export NET_BOT_TELEGRAM_TOKEN="<telegram-bot-token>"
```

Сам бот при необходимости может использовать и локальный `config/bot.local.json`.

### Файлы конфигурации

- `config/bot.example.json` — настройки Telegram-бота
- `config/ip_monitor.example.json` — настройки IP-монитора
- `config/proxies.example.json` — список прокси и настройки уведомлений для proxy monitor

### Конфиг прокси

`proxies.json` содержит и то, и другое:

- описание proxy-целей
- настройки уведомлений, например `target_chat` и `timezone`

## Запуск проекта

Из корня репозитория:

```bash
python3 -m net_bot.cli run-bot
python3 -m net_bot.cli run-ip-monitor
python3 -m net_bot.cli run-proxy-monitor
python3 -m net_bot.cli check-proxies
```

Или установить локально:

```bash
pip install -e .
net-bot run-bot
```

## Действия Telegram-бота

Telegram-бот даёт простую клавиатуру со следующими действиями:

- `Test IP` — вручную запустить IP monitor
- `Test Proxy` — вручную запустить proxy monitor
- `IP problems` — показать последние проблемы по IP из сохранённого state
- `Proxy problems` — показать последние проблемы по proxy из сохранённого state

## State и логи

Runtime-файлы хранятся в:

- `state/` — последние отчёты и состояние мониторинга
- `logs/` — логи событий DOWN

Это рабочие данные, и обычно их стоит хранить только локально.

## Примеры systemd

В каталоге `systemd/` лежат примеры unit-файлов для:

- Telegram-бота
- IP monitor
- proxy monitor

Их можно использовать как шаблоны для развёртывания.

## Типовой сценарий развёртывания

1. Скопировать example-конфиги в local-конфиги
2. Заполнить реальные цели и настройки чата
3. Задать `NET_BOT_TELEGRAM_TOKEN`
4. Проверить всё вручную через CLI-команды
5. При необходимости включить systemd service/timer

## Примечания

- проверки `mtproto` — это сетевые probe-проверки, а не полная авторизация Telegram-клиента
- проверки proxy ориентированы на практическую доступность и корректность handshake
- runtime-файлы в `state/` и `logs/` не предназначены для публичного содержимого репозитория
