# SETUP.md — Local Development Setup
Document Type: Workflow
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Canonical Status: Canonical
Dependencies: env.example; ARCHITECTURE.md; SECURITY_BASELINE.md

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Node.js 18+ (for frontend development)
- Docker and Docker Compose (optional, for containerized development)

## Quick Start (Native Python)

### 1. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools
```

### 3. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Minimum required variables:
```bash
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=consultantpro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 4. Initialize Database

```bash
# Create database (if not exists)
createdb consultantpro

# Run migrations
cd src
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

Access at:
- API: http://localhost:8000/api/v1/
- API Docs: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

## Quick Start (Docker)

```bash
docker compose up --build
```

Server available at http://localhost:8000

## Frontend Setup (Optional)

```bash
cd src/frontend
npm install
npm run dev
```

Frontend available at http://localhost:3000

## Verification Checklist

Run these commands to verify setup:

```bash
# Linting
make lint

# Tests
make test

# OpenAPI spec generation
make openapi

# Full verification
make verify
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check connection settings in `.env`
- Ensure database exists: `psql -l`

### Migration Issues
- Reset migrations: `python manage.py migrate --fake-zero` (CAUTION: development only)
- Check migration status: `python manage.py showmigrations`

### Import Errors
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check PYTHONPATH includes `src/` directory

## Next Steps

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system overview
2. Review [REPO_MAP.md](REPO_MAP.md) for codebase structure
3. Check [../TODO.md](../TODO.md) for current development priorities
4. See [API documentation](http://localhost:8000/api/docs/) for endpoint reference
