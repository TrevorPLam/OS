# ConsultantPro - Multi-Firm SaaS Platform

**Privacy-first architecture with tiered governance for multi-tenant service based firms.**

---

## Overview

ConsultantPro is a multi-tenant SaaS platform designed for service based firms. The platform emphasizes strict tenant isolation and privacy.

**Core goals:**
- Firm-level tenant isolation and privacy by default
- Audited break-glass access with strict oversight
- Transparent, honest CI and schema management

---

## Documentation

- **Getting Started:** [`docs/01-tutorials/getting-started.md`](docs/01-tutorials/getting-started.md) - Complete setup tutorial
- **Architecture:** [`docs/04-explanation/architecture-overview.md`](docs/04-explanation/architecture-overview.md) - System design and concepts
- **Platform Capabilities:** [`docs/03-reference/platform-capabilities.md`](docs/03-reference/platform-capabilities.md) - Feature inventory (what exists and what's missing)
- **Documentation Index:** [`docs/README.md`](docs/README.md) - Organized by type (tutorials, how-to, reference, explanation)
- **API Reference:** [`docs/03-reference/api-usage.md`](docs/03-reference/api-usage.md) - Complete API documentation
- **Dependency Reference:** [`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md) - Major dependency purposes and upgrade considerations
- **Deployment Guide:** [`docs/02-how-to/production-deployment.md`](docs/02-how-to/production-deployment.md) - Production deployment
- **Changelog:** [`CHANGELOG.md`](CHANGELOG.md) - Release history and changes
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md) - Development workflow
- **Security:** [`SECURITY.md`](SECURITY.md) - Security policy and reporting

---

## 🚀 Quickstart (Local Development)

**For complete setup instructions, see [Getting Started Tutorial](docs/01-tutorials/getting-started.md)**

### Prerequisites

- Python 3.11+
- PostgreSQL 15+

### Quick Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure Environment

Set the required environment variables (see [Production Deployment Guide](docs/02-how-to/production-deployment.md) for production-ready values):

```bash
export DJANGO_SECRET_KEY="dev-secret-key"
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export POSTGRES_DB=consultantpro
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend Error Tracking (Sentry)

The frontend uses Sentry for error tracking. Configure the following Vite environment variables when running the frontend build or dev server:

```bash
export VITE_SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
export VITE_SENTRY_TRACES_SAMPLE_RATE="0.1"
```

If `VITE_SENTRY_DSN` is omitted, Sentry is disabled in the frontend.

### Site & Event Tracking Configuration

Enable the new tracking pipeline with the following environment variables:

```bash
# Backend ingestion
export TRACKING_PUBLIC_KEY="public-demo-key"               # Shared with the JS snippet
export TRACKING_INGEST_ENABLED=True
export TRACKING_INGEST_RATE_LIMIT_PER_MINUTE=300
export TRACKING_MAX_PROPERTIES_BYTES=16384

# Frontend snippet (Vite)
export VITE_TRACKING_KEY="public-demo-key"
export VITE_TRACKING_FIRM_SLUG="demo-firm"
export VITE_TRACKING_ENDPOINT="http://localhost:8000/api/v1/tracking/collect/"
```

Usage (frontend):

```ts
import { createTrackingClient } from './tracking'

const tracker = createTrackingClient({
  endpoint: import.meta.env.VITE_TRACKING_ENDPOINT!,
  firmSlug: import.meta.env.VITE_TRACKING_FIRM_SLUG!,
  trackingKey: import.meta.env.VITE_TRACKING_KEY!,
})

tracker.setConsent('granted')
tracker.trackPageView()
tracker.trackEvent('cta_click', { variant: 'hero' })
```

### Run the App

```bash
cd src
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Load sample data

Populate the database with a deterministic fixture set (firms, users, clients, projects, documents, invoices):

```bash
make fixtures
```

### API Docs

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

---

## 🐳 Quickstart (Docker)

```bash
docker compose up --build
```

The Django server will be available at http://localhost:8000.

---

## 🔒 Platform Architecture

### Multi-Tenant Model

- **Firm-level tenant isolation** - Hard boundaries between firms
- **Platform privacy enforcement** - Platform staff cannot read customer content by default
- **Break-glass access** - Audited emergency access with time limits and reason tracking
- **Client portal containment** - Default-deny for portal users
- **End-to-end encryption** - Coming Soon (E2EE infrastructure dependency)
- **Immutable audit logs** - All critical actions tracked with metadata only

### Roles

**Platform:**
- Platform Operator: metadata-only access
- Break-Glass Operator: rare, audited content access

**Firm:**
- Firm Master Admin (Owner): full control, overrides
- Firm Admin: granular permissions
- Staff: least privilege, permissions enabled explicitly

**Client:**
- Portal Users: client-scoped access only

---

## ✅ Testing

```bash
pytest
```

---

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow, code quality expectations, and documentation practices.

---

## 🔐 Security

If you discover a security issue, follow [`SECURITY.md`](SECURITY.md) for disclosure guidance.

---

## License

Proprietary - All Rights Reserved
