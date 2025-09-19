# PrivetSuperApp — Repository Structure

_Last refreshed: 2025-09-18_

Use this map when navigating the codebase or planning new modules. Paths are relative to the repository root.

```
PrivetSuperApp/
├── README.md                 # Main project guide
├── docs/                     # Design & reference documentation
│   ├── ARCHITECTURE.md       # High-level system overview
│   ├── REQUIREMENTS.md       # Tooling and environment requirements
│   ├── ERD.md                # Entity relationship draft/notes
│   ├── FILE_STRUCTURE.md     # (this file)
│   ├── DATABASE_SCHEMA.sql   # Reference-only schema snapshot
│   ├── db_schema.sql         # Legacy schema dump (keep for history)
│   └── Makefile              # Helpers for generating docs/diagrams
│
├── server/                   # All backend & frontend sources
│   ├── alembic/              # Migration tooling
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/         # Individual migration scripts
│   ├── app/                  # FastAPI application package
│   │   ├── api/
│   │   │   ├── v1/           # Consumer REST endpoints (auth, users, etc.)
│   │   │   └── __init__.py
│   │   ├── core/             # Config, security, database session helpers
│   │   ├── models/           # SQLAlchemy models for core domain
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic (mailers, users, tickets)
│   │   ├── routers/          # Legacy routers (to be folded into api/)
│   │   ├── web/              # Static templates / assets if needed
│   │   ├── main.py           # FastAPI entry point
│   │   └── master_api/       # (planned) dedicated master contour package
│   ├── frontend/             # Consumer React/Vite application
│   │   ├── src/
│   │   │   ├── modules/      # Feature modules (auth, devices, tickets,...)
│   │   │   ├── shared/       # API wrapper, hooks, utilities
│   │   │   ├── styles/       # Global stylesheet bundle
│   │   │   └── main.tsx      # SPA bootstrap
│   │   ├── public/           # Static assets copied into build
│   │   ├── package.json
│   │   └── vite.config.ts
│   ├── frontend-master/      # (planned) master portal SPA
│   ├── requirements.txt      # Backend dependency lock
│   ├── pyproject.toml        # Tooling (ruff, mypy, isort, etc.)
│   ├── package.json          # Root-level npm helpers (if any)
│   ├── smoke.py              # Quick backend health check
│   └── test_smoke.py         # Smoke tests (pytest)
│
├── deploy/                   # Systemd units, Caddyfile, deployment scripts
├── docker/                   # Dockerfiles and compose definitions
├── scripts/                  # Utility shell scripts / maintenance helpers
├── alembic/                  # Top-level legacy folder (kept for history)
└── bootstrap_client.sh       # Legacy bootstrap helper
```

## Notes

- Items marked **(planned)** are placeholders for the upcoming master portal implementation. Update this file when those directories are added.
- Any secrets (`.env`, certificates) must remain outside version control.
- Tests currently live alongside feature modules. Split into dedicated `tests/` packages when the suite grows.

Keep this file in sync with structural changes to avoid stale documentation.
