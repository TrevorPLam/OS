# Local Development Setup

Complete guide for setting up your local development environment.

## Prerequisites

- **Python 3.11** - Backend runtime
- **Node.js 20** - Frontend runtime
- **PostgreSQL 15** - Database (or Docker)
- **Docker** (optional) - For local services

## Initial Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd OS
```

### 2. Install Dependencies
```bash
make setup
```

This installs:
- Backend Python dependencies
- Frontend Node.js dependencies

### 3. Environment Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Required environment variables:
- `KMS_BACKEND=local`
- `LOCAL_KMS_MASTER_KEY=local-test-key` (dev only)
- Database connection settings
- Other service configurations

### 4. Database Setup

Run migrations:
```bash
make -C backend migrate
```

Load fixtures (optional):
```bash
make -C backend fixtures
```

### 5. Start Development Servers

```bash
make dev
```

This starts:
- Backend API server (typically `http://localhost:8000`)
- Frontend dev server (typically `http://localhost:5173`)

## Development Commands

### Backend
```bash
make -C backend migrate      # Run migrations
make -C backend fixtures     # Load test data
make -C backend openapi      # Generate OpenAPI spec
```

### Frontend
```bash
make -C frontend test        # Run unit tests
make -C frontend e2e         # Run E2E tests
```

### Full Stack
```bash
make lint                    # Run linters
make test                    # Run all tests
make verify                  # Full CI suite (light)
make verify SKIP_HEAVY=0    # Full CI suite (all checks)
```

## Development Workflow

1. **Create/Update Task** - See `.repo/tasks/TODO.md`
2. **Make Changes** - Follow three-pass workflow
3. **Run Tests** - `make test`
4. **Lint** - `make lint`
5. **Verify** - `make verify`
6. **Commit** - Link to task, include filepaths

## Troubleshooting

### Database Issues
- Ensure PostgreSQL is running
- Check `.env` database settings
- Run `make -C backend migrate` again

### Port Conflicts
- Backend default: 8000
- Frontend default: 5173
- Check if ports are in use

### Dependency Issues
- Run `make setup` again
- Check Python/Node versions
- Clear caches if needed

## Next Steps

- Read [Development Guide](README.md)
- Review [Contributing Guidelines](contributing.md)
- Check [Code Standards](standards.md)
