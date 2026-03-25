# Delivery Boy

## RU

Headless Python-сервис, который периодически читает публичные Telegram-каналы через web-страницы `https://t.me/s/<channel>`, находит новые посты и пересылает их в ваш Telegram-чат или группу через Telegram Bot API.

### Возможности MVP

- Берет список каналов из `channels.yaml`
- Загружает публичные каналы через Telegram Web без Telegram-аккаунта
- Извлекает текст новых постов и ссылку на оригинал
- Сохраняет уже отправленные посты в SQLite по ключу `channel username + post id`
- Не отправляет дубли
- Хранит дату последней успешной проверки каждого канала
- Логирует запуск, проверки каналов, найденные посты, отправки и ошибки в stdout и файл
- Работает как обычный headless background service под `systemd`

### Стек

- Python 3.12
- `python-telegram-bot`
- `httpx`
- `BeautifulSoup4`
- `SQLite`
- `APScheduler`
- `systemd`

### Структура проекта

```text
src/delivery_boy/
  app.py
  config.py
  logging_setup.py
  models.py
  services/
  storage/
  telegram_web/
tests/
deploy/
```

### Быстрый старт локально

1. Создайте виртуальное окружение:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

2. Установите зависимости:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

3. Подготовьте конфиги:

```bash
cp .env.example .env
cp channels.yaml.example channels.yaml
```

4. Заполните `.env`:

- `TELEGRAM_BOT_TOKEN` - токен вашего бота
- `TELEGRAM_CHAT_ID` - ID личного чата, группы или forum-supergroup
- `TELEGRAM_MESSAGE_THREAD_ID` - ID топика, если нужно отправлять в конкретный topic; иначе оставьте пустым
- при необходимости скорректируйте `POLL_INTERVAL_SECONDS`, `DATABASE_PATH`, `LOG_FILE_PATH`

Пример:

```env
TELEGRAM_BOT_TOKEN=123456789:replace_me
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_MESSAGE_THREAD_ID=73
```

5. Заполните `channels.yaml`:

```yaml
channels:
  - username: durov
  - username: telegram
```

6. Запустите сервис:

```bash
python -m delivery_boy.app
```

### Тесты

```bash
pytest
```

### Запуск на VPS через systemd

Пример ниже предполагает путь `/opt/delivery-boy` и пользователя `deliveryboy`.

1. Скопируйте проект на сервер в `/opt/delivery-boy`
2. Создайте пользователя:

```bash
sudo useradd --system --home /opt/delivery-boy --shell /usr/sbin/nologin deliveryboy
sudo chown -R deliveryboy:deliveryboy /opt/delivery-boy
```

3. Создайте виртуальное окружение и установите проект:

```bash
cd /opt/delivery-boy
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

4. Создайте рабочие файлы конфигурации:

```bash
cp .env.example .env
cp channels.yaml.example channels.yaml
mkdir -p var/data var/log
```

5. Отредактируйте `.env` и `channels.yaml`
6. Установите unit-файл:

```bash
sudo cp deploy/delivery-boy.service /etc/systemd/system/delivery-boy.service
sudo systemctl daemon-reload
sudo systemctl enable --now delivery-boy
```

7. Проверьте статус:

```bash
sudo systemctl status delivery-boy
sudo journalctl -u delivery-boy -f
```

### Как проверить, что бот реально пересылает новые посты

1. Добавьте бота в целевой чат или группу
2. Убедитесь, что у бота есть право отправлять сообщения
3. Укажите в `channels.yaml` 1-2 публичных канала с новыми публикациями
4. Запустите сервис и следите за логами:

```bash
tail -f var/log/delivery-boy.log
```

5. В логах должны появиться строки вида:

- `Starting delivery-boy service.`
- `Checking channel=...`
- `Channel=... fetched_posts=... new_posts=...`
- `Forwarded post channel=... post_id=...`

6. В Telegram должны прийти сообщения формата:

- имя канала
- полный текст поста или безопасно обрезанная версия
- ссылка `Original: https://t.me/<channel>/<post_id>`

### Ограничения MVP

- Только публичные каналы `t.me/s/...`
- Без Telegram user account
- Без MTProto и Telethon
- Без приватных каналов
- Без web UI и админ-панели
- Без сложных media albums
- Если Telegram Web временно недоступен или поменяет HTML-разметку, парсер может потребовать обновления

## EN

A headless Python service that periodically reads public Telegram channels from `https://t.me/s/<channel>`, detects new posts, and forwards them to your Telegram chat or group through the Telegram Bot API.

### MVP features

- Reads the channel list from `channels.yaml`
- Polls public Telegram channels through Telegram Web without a Telegram account
- Extracts new post text and the original link
- Stores forwarded posts in SQLite using `channel username + post id`
- Avoids duplicate sends
- Stores the last successful check timestamp for every channel
- Logs startup, channel checks, discovered posts, sends, and errors to stdout and a file
- Runs as a simple headless background service under `systemd`

### Stack

- Python 3.12
- `python-telegram-bot`
- `httpx`
- `BeautifulSoup4`
- `SQLite`
- `APScheduler`
- `systemd`

### Project layout

```text
src/delivery_boy/
  app.py
  config.py
  logging_setup.py
  models.py
  services/
  storage/
  telegram_web/
tests/
deploy/
```

### Local quick start

1. Create a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

3. Prepare config files:

```bash
cp .env.example .env
cp channels.yaml.example channels.yaml
```

4. Fill in `.env`:

- `TELEGRAM_BOT_TOKEN` - your bot token
- `TELEGRAM_CHAT_ID` - your private chat ID, group ID, or forum supergroup ID
- `TELEGRAM_MESSAGE_THREAD_ID` - the topic/thread ID if you want to send into a specific forum topic; otherwise leave it empty
- optionally adjust `POLL_INTERVAL_SECONDS`, `DATABASE_PATH`, `LOG_FILE_PATH`

Example:

```env
TELEGRAM_BOT_TOKEN=123456789:replace_me
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_MESSAGE_THREAD_ID=73
```

5. Fill in `channels.yaml`:

```yaml
channels:
  - username: durov
  - username: telegram
```

6. Run the service:

```bash
python -m delivery_boy.app
```

### Tests

```bash
pytest
```

### VPS deployment with systemd

The example below assumes `/opt/delivery-boy` and a `deliveryboy` user.

1. Copy the project to `/opt/delivery-boy`
2. Create the service user:

```bash
sudo useradd --system --home /opt/delivery-boy --shell /usr/sbin/nologin deliveryboy
sudo chown -R deliveryboy:deliveryboy /opt/delivery-boy
```

3. Create the virtual environment and install the project:

```bash
cd /opt/delivery-boy
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

4. Create runtime config files:

```bash
cp .env.example .env
cp channels.yaml.example channels.yaml
mkdir -p var/data var/log
```

5. Edit `.env` and `channels.yaml`
6. Install the unit file:

```bash
sudo cp deploy/delivery-boy.service /etc/systemd/system/delivery-boy.service
sudo systemctl daemon-reload
sudo systemctl enable --now delivery-boy
```

7. Check the service:

```bash
sudo systemctl status delivery-boy
sudo journalctl -u delivery-boy -f
```

### How to verify real forwarding

1. Add the bot to the target chat or group
2. Make sure the bot can send messages there
3. Put one or two active public channels into `channels.yaml`
4. Start the service and watch the logs:

```bash
tail -f var/log/delivery-boy.log
```

5. Expected log lines include:

- `Starting delivery-boy service.`
- `Checking channel=...`
- `Channel=... fetched_posts=... new_posts=...`
- `Forwarded post channel=... post_id=...`

6. Telegram should receive messages that contain:

- the channel name
- the full post text or a safely trimmed version
- an `Original: https://t.me/<channel>/<post_id>` link

### MVP limitations

- Public channels only via `t.me/s/...`
- No Telegram user account
- No MTProto or Telethon
- No private channels
- No web UI or admin panel
- No complex media album forwarding
- If Telegram Web is temporarily unavailable or its HTML changes, the parser may need an update
