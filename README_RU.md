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

Проект использует конфигурационные файлы из каталога `config/`.

Сначала приложение пытается использовать локальные runtime-конфиги:
- `*.local.json`

Если локального файла нет, используется соответствующий example-файл:
- `*.example.json`

### `config/bot.example.json`

Конфигурация Telegram-бота.

Назначение:
- определяет, какой Telegram-чат имеет право работать с ботом
- при необходимости может содержать bot token для локального запуска бота

Основные поля:
- `allowed_chat_id` — ID Telegram-чата, которому разрешено работать с ботом
- `bot_api_key` — необязательный Telegram bot token

Примечания:
- для публичного репозитория этот файл должен оставаться только примером
- для локального использования лучше создать `config/bot.local.json`

### `config/ip_monitor.example.json`

Конфигурация IP monitor.

Назначение:
- определяет, какие IP-адреса нужно проверять
- определяет, как именно выполняется TCP-проверка доступности
- определяет, куда отправлять уведомления

Основные поля:
- `ips` — список IP-адресов для мониторинга
- `target_chat` — ID Telegram-чата для уведомлений monitor
- `port` — TCP-порт для проверки
- `timezone` — таймзона для времени и quiet hours
- `quiet_start` — час начала quiet hours
- `quiet_end` — час окончания quiet hours
- `rounds` — количество раундов проверки перед финальным статусом
- `interval_seconds` — пауза между раундами
- `timeout_seconds` — timeout одной TCP-попытки

Примечания:
- IP monitor использует `NET_BOT_TELEGRAM_TOKEN` для отправки уведомлений
- типовой сценарий — проверка доступности SSH на порту `22`

### `config/proxies.example.json`

Конфигурация proxy monitor.

Назначение:
- определяет список proxy-целей для проверки
- определяет параметры самих proxy-проверок
- определяет, куда отправлять уведомления по proxy

Поля верхнего уровня:
- `targets` — список proxy-описаний
- `timeout_seconds` — timeout одной proxy-проверки
- `rounds` — количество раундов
- `interval_seconds` — пауза между раундами
- `target_chat` — ID Telegram-чата для proxy-уведомлений
- `timezone` — таймзона для времени в уведомлениях

Каждый объект в `targets` может содержать:
- `name` — человекочитаемое имя прокси
- `type` — тип прокси: `mtproto`, `socks5` или `http`
- `host` — хост или IP прокси
- `port` — порт прокси
- `enabled` — нужно ли проверять эту цель

Дополнительные поля по типам:

Для `mtproto`:
- `secret` — необязательный MTProto secret

Для `socks5`:
- `username` — необязательное имя пользователя
- `password` — необязательный пароль

Для `http`:
- `username` — необязательное имя пользователя
- `password` — необязательный пароль

Примечания:
- proxy monitor использует `NET_BOT_TELEGRAM_TOKEN` для отправки уведомлений
- проверки MTProto — это сетевые probe-проверки, а не полная авторизация Telegram-клиента

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
