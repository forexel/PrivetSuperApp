# PrivetSuperApp — Requirements Guide

This document collects all tooling, runtime and configuration requirements for running or developing the project. Use it alongside `README.md` and `docs/ARCHITECTURE.md` when preparing new environments.

---

## 1. System & Tooling

| Component | Recommended Version | Notes |
|-----------|--------------------|-------|
| **Operating System** | Linux (Ubuntu 22.04+), macOS 13+, Windows 11 | Any OS that supports Python 3.12 and Node 20. Linux is used in CI/CD. |
| **Python** | 3.12.x | Backend (FastAPI) and Alembic migrations. |
| **Node.js** | 20.x (LTS) | Required for the React/Vite frontend(s). `npm` ships with Node. |
| **PostgreSQL** | 14.x or 15.x | Main database. Make sure the extension `pgcrypto` is available (needed for UUID generation). |
| **Redis** *(optional)* | 7.x | Only required if you enable caching, rate limiting, or background job features. |
| **Docker / Docker Compose** *(optional)* | Latest | Used for local infrastructure or deployments with containers. |

### Python toolchain

- `pip`, `virtualenv` (or `pyenv` / `poetry` if desired)
- `alembic` (installed via `requirements.txt`)
- `ruff`, `mypy` for linting/type checking (already specified in `pyproject.toml`)

### Node toolchain

- `npm` (bundled with Node). Yarn/Pnpm work but the repo ships with `package-lock.json`.
- Vite CLI commands (`npm run dev`, `npm run build`, etc.)

---

## 2. Backend Dependencies

All backend dependencies live in `server/requirements.txt` (executed under Python 3.12). Highlights:

- **fastapi**, **uvicorn** — web framework and ASGI server
- **sqlalchemy**, **asyncpg/psycopg** — database ORM/driver
- **alembic** — migrations
- **python-jose**, **passlib[bcrypt]** — JWTs & password hashing
- **pydantic**, **pydantic-settings** — request/response validation & settings

Ensure system packages for PostgreSQL headers (`libpq-dev` on Debian/Ubuntu, `postgresql@14` on Homebrew) are installed if building wheels locally.

---

## 3. Frontend Dependencies

Both consumer and master frontends use the same stack:

- React 19
- React Router 7
- React Hook Form + Zod
- Vite + TypeScript

Dependencies are declared in each `package.json` under `server/frontend/` (consumer) and `server/frontend-master/` (master portal, planned). Run `npm install` in each folder after installing Node.

---

## 4. Environment Variables

Create `server/.env` based on the template below. Only `KEY=VALUE` pairs are supported.

```
APP_NAME=PrivetSuperApp
ENV=dev
SECRET_KEY=<random 64+ chars>
DATABASE_URL=postgresql+psycopg://privet:privet@localhost:5432/privetdb
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MASTER_SECRET_KEY=<separate secret for master contour>
MASTER_ACCESS_MIN=120
```

Optional additions:

- `SMTP_*` settings if mailer is enabled.
- `REDIS_URL` if caching or background tasks are introduced.
- `S3_ENDPOINT`, `S3_ACCESS_KEY_ID`, etc., for object storage integrations.

### Frontend environment files

- `server/frontend/.env` → `VITE_API_BASE=/api/v1`
- `server/frontend-master/.env` *(planned)* → `VITE_API_BASE=/api/master`

These values can point to absolute URLs (e.g., `https://api.privetsuper.ru/api/v1`) in production.

---

## 5. Database

- Default database name in local setups: `privetdb`
- Run `alembic upgrade head` once the `.env` is prepared.
- The migration `20250918_01_master_users.py` requires the `pgcrypto` extension. Grant the role permission (`CREATE EXTENSION`) or enable it manually.

---

## 6. Testing & Quality Checks

Recommended commands (installed via `pyproject.toml` and `package.json`):

```bash
# Backend
ruff check server/app
ruff format server/app
pytest  # once tests are added
mypy server/app

# Frontend
npm run lint --prefix server/frontend
npm run build --prefix server/frontend
npm run build --prefix server/frontend-master  # when the master app lands
```

---

Keep this document up to date when introducing new infrastructure components (queues, search engines, etc.) or when raising version baselines.
