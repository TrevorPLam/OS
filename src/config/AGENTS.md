# AGENTS.md — Config Directory (Django Settings)

Last Updated: 2026-01-06
Applies To: `src/config/`

## Purpose

Django configuration: settings, URLs, middleware, and application-wide utilities.

## Key Components

| File | Purpose |
|------|---------|
| `settings.py` | Django settings (557 LOC) |
| `urls.py` | URL routing configuration |
| `asgi.py` | ASGI application entry |
| `wsgi.py` | WSGI application entry |
| `csp_middleware.py` | Content Security Policy |
| `csp_report.py` | CSP violation reporting |
| `env_validator.py` | Environment variable validation |
| `error_handlers.py` | Custom error handlers |
| `exceptions.py` | Custom exception classes |
| `filters.py` | DRF filter backends |
| `health.py` | Health check endpoints |
| `pagination.py` | Custom pagination classes |
| `permissions.py` | Global permission classes |
| `query_guards.py` | Query scoping guards |
| `sentry.py` | Sentry error tracking |
| `sentry_middleware.py` | Sentry middleware |
| `throttling.py` | Rate limiting classes |

## Settings Overview

### Environment Variables

```python
# REQUIRED
DJANGO_SECRET_KEY          # No fallback, app fails without it
DATABASE_URL               # PostgreSQL connection

# OPTIONAL with defaults
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

### Installed Apps Order

1. Django core apps
2. Third-party (DRF, allauth, etc.)
3. Business modules (`modules.*`)

### Middleware Chain

```python
MIDDLEWARE = [
    "SecurityMiddleware",           # Security headers
    "CSPMiddleware",                # Content Security Policy
    "CorsMiddleware",               # CORS handling
    "SessionMiddleware",
    "CommonMiddleware",
    "CsrfViewMiddleware",
    "AuthenticationMiddleware",
    "AllAuthMiddleware",            # django-allauth
    "FirmContextMiddleware",        # Multi-tenant context
    "AuditMiddleware",              # Request auditing
]
```

## URL Structure

```python
# API v1 (current)
/api/v1/auth/              # Authentication
/api/v1/firm/              # Firm management
/api/v1/portal/            # Client portal (CRITICAL BOUNDARY)
/api/v1/crm/               # CRM (staff only)
/api/v1/clients/           # Clients (staff only)
/api/v1/projects/          # Projects
/api/v1/finance/           # Finance
/api/v1/documents/         # Documents
# ... more module routes

# Public (no auth)
/api/v1/public/            # Public endpoints (shares, file requests)

# Webhooks
/api/v1/finance/stripe/webhook/
/api/v1/finance/square/webhook/

# Admin
/admin/                    # Django admin

# Health
/health/                   # Health check
/ready/                    # Readiness check

# Docs
/api/schema/               # OpenAPI schema
/api/docs/                 # Swagger UI
/api/redoc/                # ReDoc
```

## Query Guards

`query_guards.py` enforces firm scoping:

```python
from config.query_guards import require_firm_scope

@require_firm_scope
def my_view(request):
    # Guaranteed to have request.firm
    pass
```

## Health Checks

```python
# /health/ - Basic health
{
    "status": "healthy",
    "timestamp": "..."
}

# /ready/ - Readiness (DB, cache)
{
    "status": "ready",
    "database": "ok",
    "cache": "ok"
}
```

## Error Handling

Custom handlers in `error_handlers.py`:

```python
# 404 - Returns JSON for API, HTML for browser
# 500 - Logs to Sentry, returns safe error
# 503 - Maintenance mode
```

## CSP Configuration

`csp_middleware.py` sets Content Security Policy headers:

```python
# Report-only in development
# Enforced in production
# Violations reported to /csp-report/
```
