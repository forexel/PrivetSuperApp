-- =============================================================
-- NOTE: REFERENCE-ONLY SCHEMA SNAPSHOT
-- This project uses Alembic migrations in ./server/alembic as the
-- single source of truth for the database schema. Do NOT apply this
-- file directly to a live database.
-- Enum/type names here (e.g., ticket_status) may differ from runtime
-- types created by Alembic (e.g., ticket_status_t). Running this file
-- can lead to duplicate/Conflicting types and migration failures.
-- Keep for documentation, or delete if it causes confusion.
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";




# Documentation
- [Architecture Reference](./ARCHITECTURE.md)

# PrivetSuperApp — Architecture Reference

## Overview

PrivetSuperApp is designed as a scalable and maintainable web application with a clear separation between the frontend and backend layers. The architecture emphasizes modularity, security, and performance.

---

## System Components

### Frontend

- **Framework:** React with TypeScript for type safety and developer experience.
- **Build Tool:** Vite for fast development and optimized builds.
- **State Management:** TanStack Query for server state synchronization.
- **Form Handling:** React Hook Form combined with Zod for validation.
- **Routing:** React Router for client-side navigation.
- **Styling:** CSS modules and global styles for consistent UI.

### Backend

**Schema source of truth:** Database changes are managed exclusively via Alembic migrations under `server/alembic`. The root-level `DATABASE_SCHEMA.sql` is a reference snapshot only and must not be executed against live databases; applying it can create duplicate enums/types and break migrations.

- **Framework:** FastAPI for asynchronous, high-performance APIs.
- **Database:** PostgreSQL with SQLAlchemy 2.0 ORM for data modeling and migrations.
- **Migrations:** Alembic for schema version control.
- **Authentication:** JWT tokens (access and refresh) with sessions stored in the database.
- **Storage:** MinIO or S3-compatible service for media and document storage.
- **Caching & Rate Limiting:** Optional Redis integration.

---

## Directory Structure

```
.
├── server/                      # Backend source code
│   ├── app/
│   │   ├── main.py              # Application entrypoint
│   │   ├── core/                # Configuration, security, logging
│   │   ├── db/                  # Database setup and migrations
│   │   ├── models/              # ORM models
│   │   ├── schemas/             # Pydantic models for validation
│   │   ├── repositories/        # Data access layer
│   │   ├── services/            # Business logic (auth, email, storage)
│   │   ├── api/                 # API routes and dependencies
│   │   └── utils/               # Helper utilities
│   ├── tests/                   # Backend tests
│   ├── pyproject.toml           # Python dependencies and tooling
│   ├── alembic.ini              # Alembic configuration
│   └── .env.example             # Environment variables template
│
├── client/                      # Frontend source code
│   ├── src/
│   │   ├── app/                 # Router and query client setup
│   │   ├── shared/              # Reusable components, hooks, types
│   │   ├── modules/             # Feature modules (auth, profile, devices, etc.)
│   │   ├── widgets/             # UI widgets
│   │   └── styles/              # Global styles and variables
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── docker/                      # Docker configurations and compose files
│
├── ARCHITECTURE.md              # This document
└── README.md                    # Project overview and setup instructions
```

---

## Authentication Flow

- Users authenticate using JWT tokens.
- Access tokens have a short lifespan.
- Refresh tokens are stored in a sessions table in the database.
- Backend validates tokens and manages session lifecycle.
- Frontend stores tokens securely and handles token refresh transparently.

---

## API Design

- RESTful API with versioning (`/api/v1/`).
- Endpoints grouped by domain (auth, profile, devices, tickets, support, faq, pages).
- Dependency injection for common concerns (authentication, pagination).
- Pydantic models for request validation and response serialization.

---

## Storage Strategy

- Media files and documents are uploaded directly to S3-compatible storage using presigned URLs.
- Backend manages presigned URL generation and access permissions.
- MinIO can be used for local development and testing.

---

## Development Workflow

1. Launch infrastructure with Docker Compose (Postgres, MinIO, Redis optional).
2. Run backend FastAPI server with Alembic migrations applied.
3. Start frontend Vite development server with proxy configuration to backend.
4. Use environment variables to configure API endpoints and secrets.

---

## Future Enhancements

- Implement comprehensive testing suites for backend and frontend.
- Add real-time capabilities using WebSockets or server-sent events.
- Integrate analytics and monitoring tools.
- Expand support for mobile clients via Capacitor or React Native.

---

## Contact and Support

For questions or contributions, please reach out via the support channels defined in the application or project repository.

---

*End of Architecture Reference*


cat > src/shared/api/http.ts << 'JS'
import axios from 'axios';

// Base URL points to FastAPI backend; VITE_API_BASE_URL should include protocol + host + port.
const baseURL = (import.meta as any).env?.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// If your backend is namespaced (e.g., "/api"), append it here once:
const api = axios.create({ baseURL: baseURL });

// Attach access token from localStorage (key: "access_token").
api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('access_token');
    if (token && !config.headers?.Authorization) {
      (config.headers as any).Authorization = `Bearer ${token}`;
    }
  } catch {}
  return config;
});

export default api;
JS

# Архитектура проекта

## Слои

1. API (Routers)
   - Валидация входных данных
   - Маршрутизация запросов
   - Форматирование ответов

2. Services
   - Бизнес-логика
   - Координация репозиториев
   - Транзакции

3. Repositories/Models
   - Работа с БД
   - ORM модели
   - Миграции

## Аутентификация

- JWT токены (HS256)
  - access_token: {sub, typ: "access", exp: 15min}
  - refresh_token: {sub, typ: "refresh", exp: 30d}
- Хранение refresh сессий в БД
- Ротация токенов при refresh

## Зависимости

- get_db(): Async Session
- get_current_user(): Current User
- Централизованная security scheme (Bearer)

## База данных

- Миграции через Alembic
- Синхронизация моделей SQLAlchemy
- Референсная схема в DATABASE_SCHEMA.sql
# PrivetSuperApp — Architecture Reference

## Overview
FastAPI backend + (planned) React/Vite frontend. The backend is modular, async, and driven by Alembic migrations. This doc reflects the **current** contracts and DB after our latest changes (devices public read/search, ticket statuses, users.has_subscription).

---

## System Components

### Backend
- **Framework:** FastAPI (ASGI) + Uvicorn
- **DB/ORM:** PostgreSQL + SQLAlchemy 2.0 (async) + Alembic
- **Auth:** JWT (access), Passlib (argon2/bcrypt)
- **Config:** `python-dotenv`, explicit `server/.env`
- **Docs:** Swagger UI (`/docs`), OpenAPI JSON (`/openapi.json`)

### Frontend (next phase)
- **Stack:** React + TypeScript, Vite, React Router, TanStack Query, RHF + Zod
- **API client:** Axios with Bearer token from localStorage

---

## Directory Structure (high level)
```
.
├── server/                      # Backend sources
│   ├── app/
│   │   ├── main.py              # App entrypoint (loads server/.env)
│   │   ├── core/                # config, security, db, deps
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic I/O models
│   │   ├── services/            # Business logic
│   │   └── api/v1/              # Routers (users/auth, devices, tickets, admin)
│   ├── alembic/                 # Alembic env + versions
│   ├── alembic.ini              # Alembic config (uses $DATABASE_URL)
│   └── requirements.txt
├── docs/                        # Docs & generated snapshots
│   ├── ARCHITECTURE.md          # This document
│   ├── ERD.md                   # Mermaid ER diagram
│   ├── FILE_TREE.md             # File tree snapshot
│   ├── db_schema.sql            # Schema snapshot (reference-only)
│   └── Makefile                 # helper targets (dump/openapi/tree)
└── README.md
```

---

## API Design (v1)
- Versioned under `/api/v1/`.
- Grouped by domain: `auth`, `user`, `devices`, `tickets`, `admin`, `default`.
- **Auth in Swagger:** click *Authorize* → *bearerAuth* → paste the token from `/api/v1/auth/login`.

### Devices (as agreed)
- `GET /api/v1/devices/{id}` — **public**, full device info
- `GET /api/v1/devices/search` — **public**, returns list of `{id, title}`; filters: `user_id?`, `device_id?`, `title?`, `brand?`, `model?`, `serial_number?`
- `GET /api/v1/devices/my` — **auth**, only current user's devices, list of `{id, title}`
- `POST /api/v1/devices` — **public**, requires explicit `user_id` in payload
- `PATCH /api/v1/devices/{id}` — **public**, updates device by id

### Tickets
- Statuses: `new` → `in_progress` → `completed` (+ `rejected`)
- `POST /api/v1/tickets/` (auth), `GET /api/v1/tickets/` (auth), `GET /api/v1/tickets/{id}` (auth)
- `PATCH /api/v1/tickets/{id}` (auth), `PATCH /api/v1/tickets/{id}/status` (auth)

### Users/Auth
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
- `GET /api/v1/user/me`, `POST /api/v1/user/change-password`, `DELETE /api/v1/user`

---

## Database (source of truth: Alembic)
- Migrations live in `server/alembic/versions`.
- We also keep a **reference-only** snapshot at `docs/db_schema.sql` (do **not** apply to live DB).
- Key recent changes:
  - `users.has_subscription` (BOOLEAN NOT NULL, default false)
  - `tickets.status` extended to: `new`, `in_progress`, `completed`, `rejected`

See: `docs/ERD.md` for ER diagram.

---

## Configuration
- Backend loads env from `server/.env` (explicit path):
  - `DATABASE_URL`, `SECRET_KEY`, `CORS_ALLOW_ORIGINS`, etc.
- CORS configured from env; dev may use `*`, prod must be restricted.

---

## Build & Ops
- **Run dev:** `uvicorn app.main:app --reload`
- **Migrate:** `alembic upgrade head`
- **Dump schema:** `make -C docs dump-schema`
- **Export OpenAPI:** `make -C docs openapi`
- **Update file tree:** `make -C docs tree` (macOS/Linux) / manual on Windows

---

## Future Enhancements
- Tests (unit/integration) for services and routers
- WebSockets/SSE for realtime updates
- CI/CD with migrations and health checks
- Observability (logging/metrics/traces)