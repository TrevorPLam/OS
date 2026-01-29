# OS API Gateway

TypeScript API gateway that wraps the Django backend, following the FIRST standard.

## Architecture

This gateway serves as a transition layer:
- **Initially**: Proxies all API requests to Django backend
- **Gradually**: Migrates modules from Django to TypeScript
- **Eventually**: All API logic runs in TypeScript, Django is archived

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm 8+
- Django backend running (default: http://localhost:8000)

### Environment Variables

Create a `.env` file in the root of the OS repo:

```env
# Django Backend
DJANGO_BACKEND_URL=http://localhost:8000

# Gateway Configuration
GATEWAY_PORT=3000
NODE_ENV=development

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Development

```bash
# Install dependencies (from OS repo root)
pnpm install

# Run gateway in development mode
cd services/api-gateway
pnpm dev
```

The gateway will start on port 3000 and proxy all `/api/*` requests to Django.

### Building

```bash
pnpm build
pnpm start
```

## Migration Strategy

As modules are migrated from Django to TypeScript:

1. **Implement the module** in `src/routes/` or `src/modules/`
2. **Add route registration** in `src/routes/index.ts`
3. **Update contracts** in `packages/contracts/` to match the new API
4. **Test thoroughly** before removing Django proxy
5. **Remove Django code** once migration is complete

## Current Status

- ✅ Gateway structure created
- ✅ Django proxy configured
- ⏳ Modules ready for migration
- ⏳ Contracts need to be populated from Django API

## Health Check

```bash
curl http://localhost:3000/health
```

Returns:
```json
{
  "status": "ok",
  "service": "api-gateway",
  "timestamp": "2026-01-28T..."
}
```
