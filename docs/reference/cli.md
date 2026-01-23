# CLI Reference

Command-line interface documentation for UBOS.

## CLI Overview

UBOS provides command-line tools for:
- Development tasks
- Database management
- Testing
- Deployment

## Make Commands

### Setup
```bash
make setup          # Install dependencies
```

### Development
```bash
make dev            # Start dev servers
make lint           # Run linters
make test           # Run tests
make verify         # Full CI suite
```

### Backend
```bash
make -C backend migrate      # Run migrations
make -C backend fixtures     # Load fixtures
make -C backend openapi       # Generate OpenAPI spec
```

### Frontend
```bash
make -C frontend test        # Run unit tests
make -C frontend e2e         # Run E2E tests
```

## Django Management Commands

### Database
```bash
python manage.py migrate
python manage.py makemigrations
python manage.py createsuperuser
```

### Development
```bash
python manage.py runserver
python manage.py shell
python manage.py test
```

## Scripts

See `scripts/` directory for additional automation scripts:
- `archive-task.py` - Archive completed tasks
- `promote-task.sh` - Promote tasks from backlog
- `governance-verify.sh` - Verify governance compliance

## Related Documentation

- [Development Guide](../development/README.md) - Development commands
- [Local Setup](../development/local-setup.md) - Local development
- [Operations](../operations/README.md) - Operational commands
