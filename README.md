# Universal Username Checker Bot

Telegram-бот для проверки доступности юзернеймов на нескольких платформах + AI-генератор ников.

## Поддерживаемые платформы

- **Telegram** (приблизительно, через публичную страницу)
- **Roblox** (официальный API)
- **GitHub** (официальный API)
- **Steam** (vanity URL)
- **Minecraft** (Mojang + NameMC fallback)

Discord временно отключён (нет нормального публичного API без токенов).

## Возможности

- Быстрая проверка одного ника сразу на всех платформах
- AI-генерация вариантов ников по описанию (Groq / OpenAI-совместимые API)
- Лимиты для бесплатных пользователей (настраиваются)
- SQLite для учёта использования
- Красивые inline-кнопки

## Что нужно от тебя

1. **Токен бота** от [@BotFather](https://t.me/BotFather)
2. (Опционально) API-ключ для AI — рекомендуется [Groq](https://console.groq.com) (бесплатный и быстрый)

## Установка и запуск

### 1. Скачай / склонируй проект

```bash
cd username_checker_bot
```

### 2. Создай виртуальное окружение (рекомендуется)

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# или
venv\Scripts\activate      # Windows
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Настрой .env

Скопируй пример:

```bash
cp .env.example .env
```

Открой `.env` и вставь:

```env
BOT_TOKEN=твой_токен_от_BotFather

# Опционально для AI
AI_API_KEY=gsk_...          # ключ от Groq
AI_API_BASE=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile

FREE_CHECKS_PER_DAY=15
FREE_AI_GENERATIONS_PER_DAY=5
ADMIN_IDS=твой_telegram_id
```

### 5. Запуск локально

```bash
python bot.py
```

Бот должен ответить в Telegram.

## Деплой (чтобы работал 24/7)

### Самый простой вариант — Railway

1. Зарегистрируйся на [railway.app](https://railway.app)
2. New Project → Deploy from GitHub (залей этот код в репозиторий)
3. Добавь переменные окружения (BOT_TOKEN и остальные)
4. Deploy

Railway даёт кредиты, для небольшого бота хватает надолго.

### Альтернативы

- **Fly.io**
- **Koyeb** (хороший free tier без sleep)
- **Amvera** (удобно платить рублями)
- Любой VPS (Timeweb, FirstVDS, Hetzner и т.д.) + systemd / docker

## Структура проекта

```
username_checker_bot/
├── bot.py                 # Главный файл
├── requirements.txt
├── .env.example
├── checkers/
│   ├── base.py
│   ├── telegram.py
│   ├── roblox.py
│   ├── github.py
│   ├── steam.py
│   ├── minecraft.py
│   └── discord.py
└── utils/
    ├── db.py
    └── ai_generator.py
```

## Важные замечания

- Проверка Telegram не 100% точная (Telegram не даёт официального публичного API для availability). Для максимальной точности позже можно добавить Telethon + user-аккаунт.
- Roblox, GitHub, Minecraft — очень точные.
- AI работает только если указан `AI_API_KEY`. Без него используется простой rule-based генератор.
- Не злоупотребляй массовыми проверками — платформы могут временно банить IP.

## Что можно улучшить потом

- Добавить Discord (через токены / прокси)
- Instagram / TikTok / X (сложнее, нужны прокси)
- Мониторинг освобождающихся ников (sniper)
- Оплата через Telegram Stars
- Bulk-проверка списков
- Webhook вместо polling

---

Если что-то не запускается — пришли ошибку, разберёмся.
