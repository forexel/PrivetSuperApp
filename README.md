# PrivetSuperApp

Клиентское приложение “Привет Супер”: FastAPI API + React/Vite SPA, выдаваемая из API. Здесь же миграции Alembic и docker‑скрипты.

Что внутри:
- **Backend**: `server/app` (`/api/v1`).
- **Frontend (SPA)**: `server/frontend`, отдаётся FastAPI из `server/app/main.py`.
- **Migrations**: `server/alembic`.
- **Docker**: `docker/docker-compose.yml` (контейнер `apps-privet_super_api`).

---

## 1. Требования

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12+ | Backend (FastAPI) |
| Node.js | 20+ | Frontend build (Vite) |
| PostgreSQL | 14+ | База данных |
| Docker | optional | Локальный запуск из контейнера |

If you rely on optional features (Redis, MinIO, Capacitor, etc.) consult the `/docker` folder.

---

## 2. Backend + Frontend (`server/`)

```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

Create an environment file `server/.env` (only `KEY=VALUE` pairs). Start from the template if you like:

```bash
cp server/.env.example server/.env
```

Then adjust the values:

```
APP_NAME=PrivetSuperApp
ENV=dev
SECRET_KEY=replace_me_with_random_64_chars
DATABASE_URL=postgresql+psycopg://privet:privet@localhost:5432/privetdb
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:5174
MASTER_SECRET_KEY=replace_me_master_secret
MASTER_ACCESS_MIN=120
```

Apply migrations:

```bash
alembic upgrade head
```

Run the API (serves SPA too):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger: <http://127.0.0.1:8000/docs>.

---

## 3. Frontend (SPA) отдельно

### 3.1 Client App (`server/frontend`)

```bash
cd server/frontend
npm install
npm run dev  # default port 5173
```

`server/frontend/.env` already points `VITE_API_BASE=/api/v1` (see `server/frontend/.env.example`).

Build commands:

```bash
npm run build
npm run preview
```

Copy the generated `dist/` to your hosting bucket/CDN when deploying.

---

## 4. Фичи клиента (кратко)

- Счета (user_invoices) с заглушкой оплаты: экран выбора счетов, успех/ошибка оплаты.
- Счета скрываются после `due_date` (обычно это +3 дня).
- Блок счетов на главной: “К оплате / Всего”.
- Устройства клиента + фото из MinIO (галерея, просмотр).
- Чекбокс согласия с условиями при регистрации, ссылка на `/terms.pdf`.

## 5. Структура проекта

```
server/
├── app/                  # API
├── alembic/              # migrations
└── frontend/             # SPA (client)
```

For more detail see `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS.md`, and `docs/FILE_STRUCTURE.md`.

---

## 6. Docker запуск

Контейнер по умолчанию:
- API + SPA: `apps-privet_super_api` (порт `8200` → `8000` внутри)

Команды:
```bash
docker compose -f docker/docker-compose.yml up -d --build apps_privet_super_api
```

## 7. Helpful Commands

```bash
# Backend format & lint
ruff check server/app
ruff format server/app

# Run type checking
mypy server/app

# Frontend lint (consumer)
npm run lint --prefix server/frontend

# Build all
npm run build --prefix server/frontend
```

---

## 8. Deployment Notes

- Serve the backend behind TLS (Caddy, Nginx, Cloudflare Tunnel, etc.).
- Point `privetsuper.ru` to the backend (SPA отдаётся из API).
- Configure CORS in `server/.env` with the production domains.
- Rotate `SECRET_KEY` in production.
- Keep Alembic migrations in sync across environments (`alembic revision --autogenerate` for changes, review before applying).

---

## 9. Troubleshooting

- **Frontends cannot reach API**: check backend port (8000 by default) and `VITE_API_BASE=/api/v1`.
- **Stale UI**: clear Service Worker cache (если PWA).

---

Happy hacking! For deeper design notes jump to `docs/ARCHITECTURE.md`.
