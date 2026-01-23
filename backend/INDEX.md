# Backend Directory Index

**File**: `backend/INDEX.md`

This file catalogs the contents of the `backend/` directory. See [root `INDEX.md`](../INDEX.md) for repository overview.

## Directory Structure

### Core Files
- `manage.py` - Django management script
- `Makefile` - Backend-specific build commands
- `permissions.py` - Permission utilities
- `job_guards.py` - Job queue guards
- `AGENT.md` - Folder-level agent guide

### `api/` - API Endpoints
API endpoints organized by domain (Django REST Framework viewsets):
- `api/assets/` - Asset management endpoints
- `api/clients/` - Client management endpoints
- `api/crm/` - CRM endpoints (leads, prospects, deals)
- `api/documents/` - Document management endpoints
- `api/finance/` - Finance and billing endpoints
- `api/portal/` - Client portal endpoints
- `api/projects/` - Project management endpoints
- `api/webhooks/` - Webhook endpoints

### `config/` - Django Configuration
- `settings.py` - Main Django settings
- `urls.py` - URL routing
- `wsgi.py` - WSGI application
- `asgi.py` - ASGI application
- `permissions.py` - Permission classes
- `pagination.py` - Pagination utilities
- `throttling.py` - Rate limiting
- `health.py` - Health check endpoints
- `database.py` - Database configuration
- `sentry.py` - Sentry error tracking
- `env_validator.py` - Environment variable validation
- `error_handlers.py` - Error handling
- `exceptions.py` - Custom exceptions
- `filters.py` - Filter utilities
- `query_guards.py` - Query protection
- `query_monitoring.py` - Query monitoring
- Middleware: `csp_middleware.py`, `sentry_middleware.py`, `csp_report.py`

### `modules/` - Domain Modules
Domain modules with firm-scoped multi-tenancy. Each module contains models, views, serializers, urls, and migrations.

**Foundation Modules:**
- `modules/core/` - Shared platform/core utilities (platform layer)
- `modules/firm/` - Firm/tenant foundation

**Business Modules:**
- `modules/auth/` - Authentication
- `modules/clients/` - Client management
- `modules/crm/` - CRM (leads, prospects, deals)
- `modules/finance/` - Finance and billing
- `modules/projects/` - Project management
- `modules/documents/` - Document management
- `modules/calendar/` - Calendar functionality
- `modules/communications/` - Messaging
- `modules/automation/` - Automation workflows
- `modules/marketing/` - Marketing automation
- `modules/support/` - Support/ticketing
- `modules/knowledge/` - Knowledge system
- `modules/onboarding/` - Client onboarding
- `modules/pricing/` - Pricing engine
- `modules/delivery/` - Delivery templates
- `modules/recurrence/` - Recurrence engine
- `modules/orchestration/` - Orchestration engine

**Integration Modules:**
- `modules/accounting_integrations/` - Accounting integrations
- `modules/ad_sync/` - Active Directory sync
- `modules/esignature/` - E-signature integration
- `modules/integrations/` - Native integrations
- `modules/webhooks/` - Webhook platform

**Infrastructure Modules:**
- `modules/assets/` - Asset management
- `modules/jobs/` - Job queue
- `modules/email_ingestion/` - Email ingestion
- `modules/sms/` - SMS messaging
- `modules/snippets/` - Text snippets
- `modules/tracking/` - Site tracking

### `templates/` - Django Templates
- `404.html` - 404 error page
- `500.html` - 500 error page
- `503.html` - 503 service unavailable page

## Navigation

- [Root `INDEX.md`](../INDEX.md) - Repository master index
- [`frontend/INDEX.md`](../frontend/INDEX.md) - Frontend directory index
- [`tests/INDEX.md`](../tests/INDEX.md) - Tests directory index

## See Also

- `backend/AGENT.md` - What agents may do in this directory
- [`.repo/policy/BESTPR.md`](../.repo/policy/BESTPR.md) - Backend best practices
- [`.repo/policy/BOUNDARIES.md`](../.repo/policy/BOUNDARIES.md) - Module boundary rules
