# Wardeum 🛡️

**Умная защита Telegram-чатов от спама, рейдов и скама.**

---

## Быстрый старт

### 1. Подготовка

```bash
# Клонируй репозиторий
git clone https://github.com/yourusername/wardeum.git
cd wardeum

# Создай .env из примера
cp .env.example .env
# Отредактируй .env: добавь BOT_TOKEN, ADMIN_IDS, SECRET_KEY
```

### 2. Разработка (без Docker)

**Бот:**
```bash
pip install -r requirements.txt
python -m bot.main
```

**API:**
```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Фронтенд (Mini App):**
```bash
cd frontend
npm install
npm run dev
# Открой http://localhost:5173
```

### 3. Продакшен (Docker)

```bash
# Собери фронтенд
cd frontend && npm run build && cp -r dist/* ../nginx/html/ && cd ..

# Запусти все сервисы
docker compose up -d

# Просмотр логов
docker compose logs -f
```

---

## Структура проекта

```
wardeum/
├── bot/                    # Python aiogram 3 бот
│   ├── handlers/           # Обработчики событий
│   ├── middlewares/        # Throttle, обязательная подписка
│   ├── services/           # GIF-капча, ИИ, Anti-Raid, Network
│   └── database/           # SQLAlchemy модели и DB
├── api/                    # FastAPI бэкенд для Mini App
│   ├── routers/            # auth, chats, subscription, blacklist, admin
│   ├── schemas/            # Pydantic схемы
│   └── middleware/         # Telegram initData auth
├── frontend/               # React + Vite + TailwindCSS Mini App
│   └── src/
│       ├── pages/          # Home, ChatSettings, Subscription, Blacklist, Admin
│       ├── components/     # Navbar (pill), UI-компоненты
│       ├── hooks/          # useTelegram, useApi
│       ├── store/          # Zustand
│       └── api/            # Axios client
├── nginx/                  # Reverse proxy конфиг
├── Dockerfile.bot
├── Dockerfile.api
├── docker-compose.yml
└── .env.example
```

---

## Тарифы

| Тариф | Цена | Чатов | Функции |
|-------|------|-------|---------|
| **Лайт** | 150 ₽/мес | 2 | GIF-капча, фильтр ссылок, стоп-слова, Чистый чат |
| **Про** | 400 ₽/мес | 5 | + ИИ-цензор Gemini, Anti-Raid со скорингом |
| **Корпоративный** | 800 ₽/мес | 10 | + Wardeum Network, White-label боты |

Первые **3 дня Pro** — бесплатно при первом подключении.

---

## Переменные окружения

| Переменная | Описание | Обязательная |
|-----------|----------|--------------|
| `BOT_TOKEN` | Токен бота от @BotFather | ✅ |
| `ADMIN_IDS` | ID суперадминов через запятую | ✅ |
| `SECRET_KEY` | Ключ для HMAC-валидации initData | ✅ |
| `WEBAPP_URL` | HTTPS URL мини-апп | ✅ |
| `GEMINI_API_KEY` | Ключ Google AI Studio (для Pro+) | ⚠️ |
| `WEBHOOK_URL` | URL вебхука (пустой = polling) | — |
| `DATABASE_URL` | SQLite путь (по умолчанию) | — |

---

## API Endpoints

### Авторизация
Все запросы требуют заголовок:
```
Authorization: tg <initData>
```
где `initData` — строка из `Telegram.WebApp.initData`.

### Основные эндпоинты
```
GET  /api/me                     Профиль пользователя
GET  /api/chats                  Список чатов
POST /api/chats                  Добавить чат
PUT  /api/chats/{id}/settings    Обновить настройки
GET  /api/subscription/plans     Тарифы
POST /api/subscription/promo     Промокод
POST /api/subscription/key       Ключ активации
GET  /api/blacklist              Чёрный список
```

### Суперадмин
```
GET  /api/admin/stats            Статистика
POST /api/admin/keys             Генерация ключей
POST /api/admin/promo            Создание промокода
PUT  /api/admin/force-sub        Настройка обяз. подписки
```

---

## Технологии

- **Bot**: Python 3.12, aiogram 3, Pillow, numpy, Google Generative AI
- **API**: FastAPI, SQLAlchemy 2.0 async, SQLite (aiosqlite)
- **Frontend**: React 18, Vite, TailwindCSS, @telegram-apps/sdk, Zustand
- **DevOps**: Docker, Docker Compose, Nginx
