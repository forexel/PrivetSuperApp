# PrivetSuperApp — Architecture Reference

_Last updated: 2025-09-18_

This document summarizes the technical architecture of the PrivetSuper monorepo. It should help new contributors navigate the codebase, understand the separation between the consumer product and the new master portal, and know where to hook additional functionality.

---

## 1. High-Level View

```
┌────────────────────┐        ┌────────────────────┐
│  consumer browser  │◀──────▶│  server/frontend   │
│ (privetsuper.ru)   │   SPA  │  (React + Vite)    │
└────────────────────┘        └────────────────────┘
              ▲                          │
              │                          ▼
              │                  `/api/v1/*`
              │                          ▼
┌────────────────────┐        ┌────────────────────┐
│  master browser    │◀──────▶│ server/frontend-   │
│ (master.privet… )  │   SPA  │ master (React)     │
└────────────────────┘        └────────────────────┘
              ▲                          │
              │                          ▼
              │                  `/api/master/*`
              │                          ▼
              │          ┌────────────────────────┐
              └──────────│  FastAPI backend        │
                         │  server/app/main.py     │
                         │  Alembic migrations     │
                         │  PostgreSQL (psycopg3)  │
                         └────────────────────────┘
```

Both frontends are static builds deployed separately, but they talk to the same FastAPI instance. The backend exposes two logical surfaces:

1. `/api/v1` — consumer APIs (auth, devices, tickets, support, etc.).
2. `/api/master` — master-only authentication contour (isolated router, JWT secrets).

---

## 2. Backend Layout (`server/app`)

| Module | Purpose |
|--------|---------|
| `app/main.py` | Instantiates `FastAPI`, enables CORS, mounts the consumer router (`/api/v1`) and the master router (`/api/master`). Also serves the consumer SPA assets under `/` in production builds. |
| `app/core/` | Cross-cutting concerns: configuration, database session factory (`database.py`), password hashing, JWT utilities. The `settings` module reads from `server/.env`. |
| `app/master_api/` | New master contour. Contains models, CRUD helpers, JWT security, FastAPI dependencies, and the router. |
| `app/api/v1/` | Existing consumer API routers grouped by domain (`auth`, `users`, `tickets`, etc.). |
| `app/models/` | Declarative SQLAlchemy models for consumer domain. Master user model lives in `app/master_api/models.py` to keep the contour isolated. |
| `app/services/` | Business logic classes invoked by routers. |

### Database

- SQLAlchemy 2.x async (`AsyncSession`) with psycopg3 driver.
- Alembic migrations under `server/alembic/versions/` are the single source of truth.
- The migration `20250918_01_master_users.py` introduces the `master_users` table and ensures `pgcrypto` is available for UUID generation.

`master_users` schema:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `email` | text | Lowercased, unique |
| `password_hash` | text | Bcrypt hashed via `passlib` |
| `is_active` | bool | Enables temporary blocking |
| `created_at` / `updated_at` | timestamptz | Managed by DB defaults |

### Auth Flows

- **Consumer (`/api/v1`)** uses existing JWT access + refresh tokens managed in `core/security.py`.
- **Master (`/api/master`)** issues a single short-lived access token (no refresh yet). Token payload contains `sub` and `email` and is signed with `MASTER_SECRET_KEY`.
- `app/master_api/deps.py` provides `get_current_master` to guard master-only endpoints.

---

## 3. Frontends

### 3.1 Consumer SPA (`server/frontend`)

- React 19, React Router 7, TanStack Query, React Hook Form, Zod.
- Entry point `src/main.tsx` bootstraps router + query client.
- Global styles in `src/styles/*`. Auth screens reuse `forms.css` & `style.css`.
- API helper `src/shared/api.ts` handles token refresh using `/api/v1/auth/refresh`.
- Build command: `npm run build` ⇒ `dist/` served by backend `StaticFiles` or CDN.

### 3.2 Master SPA (`server/frontend-master`)

- Minimal Vite project mirroring the consumer login look & feel.
- Uses only `react`, `react-hook-form`, `zod` for the authentication form.
- Shares CSS copied from the consumer app (`src/styles/style.css`, `src/styles/forms.css`).
- API helper `src/shared/api.ts` posts to `/api/master/auth/login` with form-encoded credentials and stores `master_access_token` in `localStorage`.
- After login, navigation header with three placeholder tabs is rendered (ready for future modules like contract confirmation).

Environment configuration:

```
server/frontend/.env         -> VITE_API_BASE=/api/v1
server/frontend-master/.env  -> VITE_API_BASE=/api/master
```

Both apps use relative paths so they work behind the same domain via path proxying or separate subdomains.

---

## 4. Deployment Model

1. **Backend**: Deploy `server/app` behind gunicorn/uvicorn workers (`uvicorn app.main:app`). Static consumer assets can be served from the backend if copied to `server/frontend/dist` on the same host. Configure TLS using Caddy/Nginx.
2. **Consumer SPA**: Build to `server/frontend/dist` and upload to CDN or serve from backend.
3. **Master SPA**: Build to `server/frontend-master/dist` and deploy separately (e.g. S3 bucket + CloudFront pointing at `master.privetsuper.ru`).
4. **Secrets**: Maintain independent `SECRET_KEY` and `MASTER_SECRET_KEY`. Update `.env` files in CI/CD pipelines.
5. **Database**: Run Alembic migrations as part of deployment (`alembic upgrade head`). Ensure `pgcrypto` extension is installed.

---

## 5. Future Work

- Extend `/api/master` with contract-confirmation endpoints.
- Replace placeholder tabs with real pages (e.g., dashboard, contract queue, archive).
- Add refresh tokens for master accounts if long-lived sessions are required.
- Consolidate shared UI components between consumer and master frontends (move to a shared package or Nx workspace if duplication grows).
- Harden security with IP restriction/MFA for master accounts.

---

## 6. Reference

- Backend entry point: `server/app/main.py`
- Master model definition: `server/app/master_api/models.py`
- Master login router: `server/app/master_api/router.py`
- Migration: `server/alembic/versions/20250918_01_master_users.py`
- Master login page: `server/frontend-master/src/modules/auth/LoginPage.tsx`

For database diagrams and historical context, check `docs/ERD.md` and `docs/DATABASE_SCHEMA.sql` (reference only).

---

_Questions or corrections? Create an issue or update this file._
