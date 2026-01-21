# REPO_MAP.md — Repository Structure Map
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active

## Repository Structure

```
/
├── README.md                     # Project overview and quickstart
├── CONTRIBUTING.md               # Development workflow and standards
├── CHANGELOG.md                  # Release history
├── P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md                       # Development roadmap
├── SECURITY.md                   # Security policy and reporting
├── Makefile                      # Build orchestration (setup, lint, test, verify)
├── pyproject.toml                # Python tooling config (ruff, black, pytest)
├── requirements.txt              # Python production dependencies
├── requirements-dev.txt          # Python development dependencies
├── docker-compose.yml            # Docker orchestration for local development
├── Dockerfile                    # Container image definition
├── .env.example                  # Environment variable template
│
├── src/                          # Application source code
│   ├── manage.py                 # Django management script
│   ├── config/                   # Django project configuration
│   │   ├── settings.py           # Django settings
│   │   ├── urls.py               # Root URL routing
│   │   ├── health.py             # Health check endpoints
│   │   └── sentry_middleware.py  # Sentry integration
│   │
│   ├── modules/                  # Business domain modules
│   │   ├── firm/                 # Multi-tenant foundation
│   │   ├── auth/                 # Authentication & authorization
│   │   ├── crm/                  # CRM (leads, prospects, proposals)
│   │   ├── clients/              # Client management & portal
│   │   ├── projects/             # Projects & tasks
│   │   ├── finance/              # Billing & invoicing
│   │   ├── documents/            # Document management
│   │   ├── pricing/              # Pricing engine
│   │   ├── delivery/             # Delivery templates
│   │   ├── recurrence/           # Recurrence engine
│   │   ├── orchestration/        # Workflow orchestration
│   │   ├── automation/           # Marketing automation
│   │   ├── communications/       # Messages & conversations
│   │   ├── email_ingestion/      # Email ingestion & triage
│   │   ├── calendar/             # Calendar & scheduling
│   │   ├── sms/                  # SMS messaging
│   │   ├── webhooks/             # Webhook platform
│   │   ├── marketing/            # Marketing primitives
│   │   ├── support/              # Support ticketing
│   │   ├── onboarding/           # Client onboarding
│   │   ├── knowledge/            # Knowledge management
│   │   ├── jobs/                 # Background jobs
│   │   ├── snippets/             # Text snippets
│   │   ├── accounting_integrations/  # QuickBooks, Xero
│   │   ├── esignature/           # DocuSign integration
│   │   └── ad_sync/              # Active Directory sync
│   │
│   ├── api/                      # API configuration and utilities
│   ├── frontend/                 # React + TypeScript frontend
│   │   ├── src/                  # Frontend source code
│   │   ├── public/               # Static assets
│   │   ├── package.json          # Node dependencies
│   │   └── vite.config.ts        # Vite build configuration
│   │
│   └── tests/                    # Test suites
│       ├── integration/          # Integration tests
│       └── unit/                 # Unit tests
│
├── docs/                         # Documentation (Diátaxis framework)
│   ├── README.md                 # Documentation map and index
│   ├── codingconstitution.md    # Comprehensive governance rules
│   ├── REPO_MAP.md               # This file
│   ├── 01-tutorials/             # Learning-oriented tutorials
│   ├── 02-how-to/                # Problem-solving guides
│   ├── 03-reference/             # Technical reference material
│   │   ├── requirements/         # Canonical requirements
│   │   ├── api/                  # API reference
│   │   └── policies/             # Policies and standards
│   ├── 04-explanation/           # Understanding-oriented docs
│   │   ├── implementations/      # Implementation documentation
│   │   └── security/             # Security architecture docs
│   ├── 05-decisions/             # Architecture Decision Records
│   ├── 06-user-guides/           # End-user documentation
│   └── runbooks/                 # Operational runbooks
│
├── scripts/                      # Utility scripts
│   └── verify-repo.sh            # Repository health check
│
└── .github/                      # GitHub configuration
    └── workflows/                # CI/CD pipelines
        ├── ci.yml                # Main CI pipeline
        └── docs.yml              # Documentation validation
```

## Module Structure Pattern

Each Django module follows this structure:

```
modules/<module_name>/
├── __init__.py
├── models.py                     # Database models
├── serializers.py                # DRF serializers
├── views.py                      # API views/viewsets
├── urls.py                       # URL routing
├── admin.py                      # Django admin config
├── permissions.py                # Custom permissions
├── services.py                   # Business logic (optional)
├── tasks.py                      # Background tasks (optional)
├── migrations/                   # Database migrations
│   └── __init__.py
└── tests/                        # Module tests
    ├── __init__.py
    ├── test_models.py
    ├── test_serializers.py
    ├── test_views.py
    └── test_permissions.py
```

## Key Files by Purpose

### Configuration
- `src/config/settings.py` - Django settings (database, middleware, installed apps)
- `.env.example` - Environment variable template
- `pyproject.toml` - Python tooling configuration

### Build & Deployment
- `Makefile` - Build orchestration
- `docker-compose.yml` - Local development environment
- `Dockerfile` - Production container image

### Documentation
- `docs/README.md` - Documentation index
- `docs/codingconstitution.md` - Governance rules
- `docs/REPO_MAP.md` - This file

### Quality & Testing
- `pytest.ini` - pytest configuration
- `.github/workflows/ci.yml` - CI/CD pipeline
- `scripts/verify-repo.sh` - Repository health check

## Dependency Flow

```
Frontend (React)
    ↓ HTTP/REST
API Layer (Django REST Framework)
    ↓
Views/ViewSets
    ↓
Serializers (validation)
    ↓
Services (business logic)
    ↓
Models (ORM)
    ↓
PostgreSQL (with RLS)
```

## Cross-Cutting Concerns

### Multi-Tenancy
- Enforced in middleware (sets firm context)
- RLS policies at database level
- QuerySet filtering in views

### Audit Logging
- `modules/core/audit/` - Audit infrastructure
- Logs sensitive operations (metadata only)
- Immutable append-only logs

### Authentication
- JWT tokens (access + refresh)
- OAuth/SAML providers (Google, Microsoft)
- MFA support (TOTP)

### Integrations
- External APIs wrapped in service classes
- Webhook handlers with signature verification
- OAuth connection management

See individual module READMEs for detailed information.
