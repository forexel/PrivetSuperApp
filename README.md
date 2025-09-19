# PrivetSuperApp Monorepo

This repository hosts everything required to run the PrivetSuper platform:

- **FastAPI backend** in `server/app` serving the public consumer API (`/api/v1`) and the new master-only contour (`/api/master`).
- **Consumer frontend** (React/Vite) in `server/frontend` for privetsuper.ru.
- **Master portal frontend** (React/Vite) in `server/frontend-master` for master.privetsuper.ru.
- **Alembic migrations** and deployment tooling in `server/alembic`, `deploy/`, `docker/`.

Use this document as the single place to bootstrap a local environment or understand the moving parts.

---

## 1. Requirements

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12+ | Required for the FastAPI backend |
| Node.js | 20+ | Needed to build both frontends |
| PostgreSQL | 14+ | Primary database |
| Poetry/pip | optional | We use `pip` in the examples |

If you rely on optional features (Redis, MinIO, Capacitor, etc.) consult the `/docker` folder.

---

## 2. Backend Setup (`server/`)

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

Apply migrations (includes the new `master_users` table):

```bash
alembic upgrade head
```

Run the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger is available at <http://127.0.0.1:8000/docs>. The master contour lives at `/api/master/auth/*`.

---

## 3. Frontend Setup

Both frontends are standard Vite projects.

### 3.1 Consumer App (`server/frontend`)

```bash
cd server/frontend
npm install
npm run dev  # default port 5173
```

`server/frontend/.env` already points `VITE_API_BASE=/api/v1` (see `server/frontend/.env.example`), so requests are proxied to the backend.

### 3.2 Master Portal (`server/frontend-master`)

```bash
cd server/frontend-master
npm install
npm run dev -- --port 5174
```

`server/frontend-master/.env` sets `VITE_API_BASE=/api/master`. After a successful login the app shows an empty workspace with three placeholder tabs on top (ready for the upcoming contract-confirmation flows).

Build commands:

```bash
npm run build      # in each frontend folder
npm run preview    # optional static preview
```

Copy the generated `dist/` to your hosting bucket/CDN when deploying.

---

## 4. Master Auth API Cheat Sheet

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/master/auth/login` | POST | Form-encoded login (`username` = email, `password`) → returns JWT |
| `/api/master/auth/me` | GET | Returns the authenticated master profile |

The login endpoint follows the OAuth2 password grant (FastAPI `OAuth2PasswordRequestForm`). The master frontend stores the token in `localStorage` under `master_access_token`.

### Creating a Master Account

Use the `create_master` helper once you have a Python shell:

```bash
cd server
source .venv/bin/activate
python
```

```python
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.database import engine
from app.master_api.crud import create_master

async def bootstrap():
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        await create_master(session, email="admin@master.test", password="ChangeMe123")

import asyncio
asyncio.run(bootstrap())
```

Alternatively, seed via Alembic or SQL (`INSERT INTO master_users ...`).

---

## 5. Project Structure (excerpt)

```
server/
├── app/
│   ├── api/v1/           # consumer API routers
│   ├── master_api/       # master-only JWT auth router, models, deps
│   ├── core/             # config, db, security utilities
│   └── main.py           # FastAPI application wiring
├── alembic/              # migrations (master_users add-on lives here)
├── frontend/             # privetsuper.ru React app
└── frontend-master/      # master.privetsuper.ru React app
```

For more detail see `docs/ARCHITECTURE.md`, `docs/REQUIREMENTS.md`, and `docs/FILE_STRUCTURE.md`.

---

## 6. Helpful Commands

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
npm run build --prefix server/frontend-master
```

---

## 7. Deployment Notes

- Serve the backend behind TLS (Caddy, Nginx, Cloudflare Tunnel, etc.).
- Point `privetsuper.ru` to the `server/frontend/dist` bundle and `master.privetsuper.ru` to `server/frontend-master/dist`.
- Configure CORS in `server/.env` with the production domains.
- Rotate both `SECRET_KEY` and `MASTER_SECRET_KEY` in production.
- Keep Alembic migrations in sync across environments (`alembic revision --autogenerate` for changes, review before applying).

---

## 8. Troubleshooting

- **401 on master login**: ensure the user exists in `master_users`, password hashed via `create_master`, and `MASTER_SECRET_KEY` matches between backend and master frontend.
- **Migrations missing pgcrypto**: the `20250918_01` migration enables the extension. Grant the role `CREATE` rights or enable manually (`CREATE EXTENSION pgcrypto;`).
- **Frontends cannot reach API**: double-check the backend port (8000 by default) and that `VITE_API_BASE` points to `/api/v1` or `/api/master`.
- **Token expired**: `MASTER_ACCESS_MIN` defaults to 120 minutes; adjust in `server/.env` as needed.

---

Happy hacking! For deeper design notes jump to `docs/ARCHITECTURE.md`.
