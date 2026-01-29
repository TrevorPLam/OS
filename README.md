# OS

Operating system for professional services with TypeScript-first architecture.

## Installation

```bash
# Install all dependencies (monorepo)
pnpm install
```

## Usage

### Development

```bash
# Run all development servers
pnpm dev

# Build all packages and apps
pnpm build

# Run linter across all packages
pnpm lint

# Type check across all packages
pnpm type-check

# Run tests
pnpm test
```

### Individual Packages

```bash
# Web app
cd apps/web
pnpm dev

# API Gateway
cd services/api-gateway
pnpm dev

# Django Backend (legacy, being migrated)
cd services/api-service/backend
python manage.py runserver
```

## Project Structure

This monorepo follows a TypeScript-first architecture:

```
apps/
  web/              # React + Vite frontend application
packages/
  ui/               # Shared UI components
  utils/            # Shared utilities
  contracts/        # Zod schemas + types (source of truth)
  api-sdk/          # Generated client SDK from contracts
  config/           # Shared configs (eslint, prettier, typescript)
services/
  api-gateway/      # TypeScript backend (canonical)
  api-service/      # Django backend (legacy, being migrated)
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `GATEWAY_PORT` - API Gateway port (default: 3000)
- `DJANGO_BACKEND_URL` - Django backend URL (default: http://localhost:8000)
- `ALLOWED_ORIGINS` - CORS allowed origins
- `VITE_SENTRY_DSN` - Sentry DSN for frontend error tracking
- `VITE_TRACKING_KEY` - Analytics tracking key

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

Proprietary - See [LICENSE](LICENSE) for details.
