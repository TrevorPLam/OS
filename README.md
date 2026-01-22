# ConsultantPro — Multi-Firm SaaS Platform

**Privacy-first, multi-tenant platform for management consulting firms.**

ConsultantPro is a Django + React SaaS platform built around strict tenant isolation, modular domain boundaries, and auditable governance.

---

## Table of Contents

- [Overview](#overview)
- [Scope & Principles](#scope--principles)
- [Platform Pillars](#platform-pillars)
- [Feature Status Snapshot](#feature-status-snapshot)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Documentation Map](#documentation-map)
- [🚀 Quickstart (Local Development)](#-quickstart-local-development)
- [🐳 Quickstart (Docker)](#-quickstart-docker)
- [🧰 VS Code Workspace](#-vs-code-workspace)
- [✅ Verification & Testing](#-verification--testing)
- [📌 Project Status](#-project-status)
- [🤝 Contributing](#-contributing)
- [🔐 Security](#-security)
- [License](#license)

---

## Overview

ConsultantPro is a multi-tenant SaaS platform designed for service-based firms. The system emphasizes firm-level isolation, privacy-by-default access controls, and an audited break-glass path for rare emergency access.

---

## Scope & Principles

The platform’s core architecture principles are:

1. **Multi-tenant isolation** — firm boundaries are enforced at both application and database layers.
2. **Privacy by default** — platform staff cannot access customer content without audited break-glass workflows.
3. **Modular monolith** — bounded domain modules remain independent and testable.
4. **API-first design** — REST APIs with OpenAPI docs.
5. **Secure defaults** — security controls are designed-in, not bolted on.

---

## Platform Pillars

ConsultantPro is organized around these functional pillars:

- **CRM & Sales** — lead to proposal lifecycle management.
- **Client Management** — client portal, onboarding, and collaboration.
- **Project & Task Management** — delivery workflows, tasks, and time tracking.
- **Finance & Billing** — invoicing, payments, and revenue operations.
- **Calendar & Scheduling** — booking links, availability, and sync.
- **Marketing Automation** — campaigns, workflows, and segmentation.
- **Communications** — email, SMS, portal messaging, and templates.
- **Documents & Knowledge** — versioned documents and knowledge base.
- **Support & Ticketing** — ticketing with SLA and routing.
- **Integrations** — webhook platform plus external providers.

See [docs/PILLARS.md](docs/PILLARS.md) for module-to-pillar mapping.

---

## Feature Status Snapshot

High-level inventory from the platform capabilities audit:

- **Fully implemented:** 150+ features ✅
- **Partially implemented:** 1 feature ⚠️
- **Coming soon:** 18 features 🔜
- **Not planned:** mobile native apps, blockchain integration, cryptocurrency payments, social media management

For the authoritative inventory, see [docs/03-reference/platform-capabilities.md](docs/03-reference/platform-capabilities.md).

---

## Architecture & Tech Stack

**Backend:** Django 4.2 LTS + Django REST Framework, modular monolith with firm-scoped data access.

**Frontend:** React 18 + TypeScript + Vite.

**Database:** PostgreSQL 15 with Row-Level Security (RLS) for tenant isolation.

**Observability:** OpenAPI docs, structured logging, and Sentry integration.

For the full architecture details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Documentation Map

- **Getting Started Tutorial:** [`docs/01-tutorials/getting-started.md`](docs/01-tutorials/getting-started.md)
- **Documentation Index:** [`docs/README.md`](docs/README.md)
- **Architecture Overview:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Security Baseline:** [`docs/SECURITY_BASELINE.md`](docs/SECURITY_BASELINE.md)
- **Platform Capabilities:** [`docs/03-reference/platform-capabilities.md`](docs/03-reference/platform-capabilities.md)
- **Repo Map:** [`docs/REPO_MAP.md`](docs/REPO_MAP.md)
- **Testing Strategy:** [`docs/TESTING_STRATEGY.md`](docs/TESTING_STRATEGY.md)
- **Environment Reference:** [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md)
- **Operations Guide:** [`docs/OPERATIONS.md`](docs/OPERATIONS.md)
- **API Reference:** [`docs/03-reference/api-usage.md`](docs/03-reference/api-usage.md)
- **Dependency Reference:** [`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md)
- **Deployment Guide:** [`docs/02-how-to/production-deployment.md`](docs/02-how-to/production-deployment.md)
- **Changelog:** [`CHANGELOG.md`](CHANGELOG.md)
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Security Policy:** [`SECURITY.md`](SECURITY.md)

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

Enable the tracking pipeline with the following environment variables:

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

## 🧰 VS Code Workspace

The repository ships a shared VS Code workspace configuration to make formatting, linting, and debugging consistent across contributors:

- **Workspace settings:** `.vscode/settings.json` sets Black + Ruff for Python and ESLint/Prettier for JS/TS formatting.
- **Recommended extensions:** `.vscode/extensions.json` lists the editor extensions that match the repo tooling.
- **Debug configs:** `.vscode/launch.json` includes launch profiles for the Django runserver and Vite dev server.

Open the repo in VS Code to pick up the defaults, then run the debug profiles as needed.

---

## ✅ Verification & Testing

Recommended repo-level verification commands:

```bash
make lint
make test
```

Additional recommended checks (see `repo.manifest.yaml`):

```bash
./docs/scripts/ai-audit.sh
./docs/scripts/check.sh
./docs/scripts/security-scan.sh
```

**Local environment note:** tests default to SQLite locally, and RLS checks skip without PostgreSQL.

---

## 📌 Project Status

Current project snapshot:

- **Phase:** Backend hardening and test backfill
- **Environment:** Local development (tests run with SQLite; RLS probes skip without PostgreSQL)
- **Key risks:** Background jobs must wrap DB access in `firm_db_session` for RLS enforcement

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the canonical status and decisions.

---

## 🤝 Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for workflow, code quality expectations, and documentation practices.

---

## 🔐 Security

If you discover a security issue, follow [`SECURITY.md`](SECURITY.md) for disclosure guidance.

---

## License

Proprietary - All Rights Reserved
