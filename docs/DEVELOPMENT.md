# Development

## Backend (Django)

Commands (from repo root):
- `make dev` runs `backend` and `frontend` dev servers
- `make lint` runs ruff and black checks
- `make test` runs pytest
- `make verify` runs lint, typecheck, tests, and OpenAPI checks

Backend-specific:
- `make -C backend migrate`
- `make -C backend fixtures`
- `make -C backend openapi`

## Frontend (Vite)

Commands (from repo root):
- `make dev` runs Vite dev server
- `make -C frontend test` runs unit tests + typecheck
- `make -C frontend e2e` runs Playwright tests

## Environment variables

Use `.env` locally and keep secrets out of git. Copy from `.env.example` and fill in values.
