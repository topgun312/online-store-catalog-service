# online-store-catalog-service

## Назначение

Микросервис каталога товаров. Администратор управляет товарами через
Telegram-бота (фото + подпись = название), покупатели смотрят каталог в браузере
или в Telegram Mini App.

Основные возможности:

- CRUD товаров и категорий через REST API;
- загрузка изображений товаров в S3-совместимое хранилище (MinIO);
- пагинация и фильтрация каталога по категории;
- админ-панель в Telegram-боте;
- Telegram Mini App и обычная веб-страница каталога;
- миграции Alembic, тестовые данные, линтеры и интеграционные тесты.


## Архитектура

```
Telegram / браузер / Mini App
              │
              ▼
   ┌──────────────────────────────────┐
   │ gateway — Traefik                │
   │ :3000  /        → frontend       │
   │ :8081  /webhook → bot            │
   │ :8000  /api     → backend        │
   └───────┬───────────┬──────────────┘
           │           │
           ▼           ▼
     frontend       bot ───────▶ Redis (FSM)
           │           │
           └─────┬─────┘
                 │ HTTP
                 ▼
            backend
             │     │
             ▼     ▼
       PostgreSQL  MinIO (S3)
```

| Сервис | Стек | Порт | Назначение |
|---|---|---|---|
| `gateway` | Traefik 3.6 | 3000, 8000, 8081 | единая точка входа и балансировка реплик |
| `backend` | FastAPI, SQLAlchemy async, Alembic | 8000 (внутренний) | REST API, PostgreSQL, MinIO |
| `bot` | aiogram 3.x, httpx | 8081 (внутренний) | админ-панель и кнопка Mini App |
| `frontend` | Next.js 15, React 19, TypeScript | 3000 (внутренний) | каталог товаров |
| `postgres` | PostgreSQL 15 | 5432 (внутренний) | товары и категории |
| `minio` | MinIO (S3 API) | 9000, 9001 (внутренний) | изображения товаров |
| `redis` | Redis 7 | 6379 (внутренний) | FSM-состояние бота |

Backend построен по onion-архитектуре:
`api → services → unit_of_work → repositories → models`. Бот не обращается к БД
и S3 напрямую — только к backend по HTTP.

В Docker Compose gateway публикует порты `3000`, `8000` и `8081`. Gateway сам
обнаруживает реплики `backend`, `frontend` и `bot` через Docker provider.
`bot-init` — one-shot сервис: регистрирует webhook один раз, реплики `bot` не
меняют его при старте и остановке.

## Технологии

| Слой | Технологии |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2 (async), asyncpg, Alembic, aiobotocore, loguru |
| Bot | Python 3.11+, aiogram 3.x, httpx, pydantic-settings, loguru |
| Frontend | Node.js 20+, Next.js 15, React 19, TypeScript, ESLint |
| Gateway | Traefik 3.6, Docker provider |
| Инфраструктура | Docker, Docker Compose, PostgreSQL 15, MinIO, Redis 7 |
| Инструменты | uv, pytest, ruff, black, isort, GNU Make |

## Структура

```
backend/
├── alembic/             # миграции
├── scripts/             # init bucket, seed-изображения
├── src/
│   ├── api/             # роутеры и сервисы
│   ├── database/        # подключение к PostgreSQL
│   ├── models/          # SQLAlchemy-модели
│   ├── repositories/    # доступ к данным
│   ├── schemas/         # Pydantic-схемы и фильтры
│   ├── storage/         # абстракция S3/MinIO
│   └── utils/           # UoW, репозитории, вспомогательные функции
├── tests/               # интеграционные тесты
└── deploy/              # docker-compose для dev-инфраструктуры

bot/
├── config_data/         # настройки из .env
├── handlers/            # команды и сценарии админ-панели
├── keyboards/           # inline-клавиатуры
├── middleware/          # проверка администратора
├── states/              # FSM-состояния
└── utils/               # HTTP-клиент backend

frontend/
├── app/                 # страницы и layout
├── components/          # карточки, пагинация, фильтры
└── lib/                 # API-клиент и типы
```

## Запуск с Docker

### Требования

- Docker и Docker Compose;
- Telegram-токен от [@BotFather](https://t.me/BotFather);
- заполненный `bot/.env`.

### Полный запуск

Перед запуском заполните `bot/.env`:

```dotenv
BOT_TOKEN=123456789:AA...your-bot-token
ADMIN_IDS=111111111
WEBAPP_URL=https://catalog.example.com
WEBHOOK_URL=https://bot.example.com
WEBHOOK_SECRET=your-webhook-secret
```

`WEBHOOK_URL` указывается без `/webhook` — бот добавит путь сам.
`BACKEND_URL` и `REDIS_URL` для контейнера задаются в `docker-compose.yml`.

Запуск:

```bash
make up
docker compose ps
```

`make up` поднимает gateway, PostgreSQL, MinIO, Redis, применяет миграции,
создаёт бакет, регистрирует webhook и запускает `backend`, `frontend`, `bot`.

Адреса:

- каталог: <http://localhost:3000>;
- Swagger UI: <http://localhost:8000/docs>;
- healthcheck: <http://localhost:8000/api/healthz/>.

Остановка:

```bash
make down    # остановить, volumes сохранить
```

### Тестовые данные и картинки

```bash
make seed-docker
make seed-image-docker
```

`seed-docker` добавляет тестовые категории и товары в PostgreSQL, а
`seed-image-docker` загружает для них placeholder-изображения в MinIO. Команды
нужно выполнять после `make up`.

### Масштабирование

```bash
make scale    # backend=3, frontend=2, bot=2
```

`backend`, `frontend` и `bot` не публикуют host-порты: gateway распределяет
запросы между живыми репликами.

## Запуск без Docker

Backend, frontend и bot запускаются на хосте, PostgreSQL, MinIO и Redis — в
Docker через `backend/deploy/docker-compose.dev.yaml`.

### Требования

- [uv](https://docs.astral.sh/uv/) для backend и bot;
- Node.js 20+ и npm для frontend;
- GNU Make;
- `psql` (пакет `postgresql-client`);
- заполненный `bot/.env`.

### 1. Создать env-файлы

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
cp bot/.env.example bot/.env
```

В `bot/.env` заполните `BOT_TOKEN`, `ADMIN_IDS` и `WEBHOOK_SECRET`.
`WEBAPP_URL` и `WEBHOOK_URL` добавьте после запуска ngrok на шаге 6.

### 2. Поднять инфраструктуру

```bash
make infra-up
```

Будут доступны PostgreSQL на `localhost:5432`, MinIO на `localhost:9000`
(консоль — `localhost:9001`) и Redis на `localhost:6379`.

### 3. Применить миграции и загрузить тестовые данные

```bash
make migrate
make seed
make seed-images
```

`make seed` добавляет тестовые категории и товары, `make seed-images` загружает
для них placeholder-изображения в MinIO.

### 4. Запустить backend

Терминал 1:

```bash
make api
```

Проверка:

```bash
curl http://localhost:8000/api/healthz/
curl http://localhost:8000/api/v1/product/
```

### 5. Запустить frontend

Терминал 2:

```bash
make frontend
```

Каталог: <http://localhost:3000>.

### 6. Установить и запустить ngrok

Установка для Debian/Ubuntu:

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok
```

Либо через snap:

```bash
sudo snap install ngrok
```

Сохраните токен из личного кабинета ngrok:

```bash
ngrok config add-authtoken <NGROK_AUTHTOKEN>
```

Запустите два туннеля в разных терминалах:

```bash
ngrok http 3000
ngrok http 8081
```

Если бесплатный тариф не разрешает два одновременных процесса, запустите оба
туннеля одним агентом. Добавьте в `~/.config/ngrok/ngrok.yml`:

```yaml
version: "3"
agent:
  authtoken: <NGROK_AUTHTOKEN>
tunnels:
  frontend:
    proto: http
    addr: 3000
  webhook:
    proto: http
    addr: 8081
```

И запустите:

```bash
ngrok start frontend webhook
```

Полученные HTTPS-адреса укажите в `bot/.env`:

```dotenv
WEBAPP_URL=https://frontend-xxxx.ngrok-free.app
WEBHOOK_URL=https://bot-xxxx.ngrok-free.app
```

`WEBAPP_URL` — адрес туннеля на `:3000`, `WEBHOOK_URL` — адрес туннеля на `:8081`.

### 7. Запустить bot

Терминал 3:

```bash
make bot
```

Проверка: `/start` → кнопка «Открыть каталог», у администратора —
«Админ-панель».

### Остановка

Остановите процессы `make api`, `make frontend` и `make bot`, затем:

```bash
make infra-down
```

## Очистка volumes

Полный Docker-стек:

```bash
docker compose --profile bot down -v
```

Dev-инфраструктура для локального запуска:

```bash
docker compose -f backend/deploy/docker-compose.dev.yaml down -v
```

`down -v` удаляет контейнеры вместе с named volumes PostgreSQL, MinIO и Redis.
`make down` останавливает стек, но volumes сохраняет. Не используйте
`docker volume prune` или `docker system prune --volumes`: они удаляют volumes
других проектов на машине.

## Порядок тестирования

### 1. Линтеры

```bash
make lint
cd frontend && npm run lint
```

`make lint` запускает для `backend` и `bot`:

- `isort` — сортировка импортов;
- `black` — форматирование;
- `ruff` — линтинг с автоисправлением безопасных замечаний.

### 2. Интеграционные тесты backend

Для тестов нужен PostgreSQL:

```bash
make infra-up
make test
```

`make test` запускает интеграционные тесты backend через `pytest`.

### 3. Проверка запущенного стека

```bash
curl -fsS http://localhost:3000/ >/dev/null
curl -fsS http://localhost:8000/api/healthz/
curl -fsS http://localhost:8000/api/v1/product/
```

Для Docker-стека дополнительно:

```bash
docker compose ps
```

Все контейнеры должны быть в состоянии `healthy`, а `migrate` и `minio-init` —
успешно завершены.

### 4. Проверка бота

Отправьте боту `/start`. Должны появиться кнопка «Открыть каталог», а у
администратора — «Админ-панель». Создайте тестовый товар и проверьте, что он
появился в каталоге.
