# Onboarding

This guide gets you from zero to a running dev environment.

## Prerequisites

- Python 3.11
- Node.js 20
- Docker (optional, for services)

## First-time setup

1. Install dependencies:
   - `make setup`

2. Start the dev servers:
   - `make dev`

## Where to look

- Backend API: `backend/`
- Frontend app: `frontend/`
- Shared tests: `tests/`

## Common commands

- `make lint`
- `make test`
- `make verify` (local CI suite)
- `make ci` (alias used by CI)
