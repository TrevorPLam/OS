# ConsultantPro - Multi-Firm SaaS Platform

**Privacy-first architecture with tiered governance for multi-tenant consulting firms.**

---

## Overview

ConsultantPro is a multi-tenant SaaS platform designed for consulting firms. The platform emphasizes strict tenant isolation, privacy controls, and a tiered delivery model that prevents skipping foundational safety work.

**Core goals:**
- Firm-level tenant isolation and privacy by default
- Audited break-glass access with strict oversight
- Clear governance and delivery tiers
- Transparent, honest CI and schema management

---

## Documentation

- **Getting Started:** [`docs/01-tutorials/getting-started.md`](docs/01-tutorials/getting-started.md) - Complete setup tutorial
- **Architecture:** [`docs/04-explanation/architecture-overview.md`](docs/04-explanation/architecture-overview.md) - System design and concepts
- **Platform Capabilities:** [`docs/03-reference/platform-capabilities.md`](docs/03-reference/platform-capabilities.md) - Feature inventory (what exists and what's missing)
- **Documentation Index:** [`docs/README.md`](docs/README.md) - Organized by type (tutorials, how-to, reference, explanation)
- **Tier System:** [`docs/03-reference/tier-system.md`](docs/03-reference/tier-system.md) - Architecture governance and priorities
- **API Reference:** [`docs/03-reference/api-usage.md`](docs/03-reference/api-usage.md) - Complete API documentation
- **Deployment Guide:** [`docs/02-how-to/production-deployment.md`](docs/02-how-to/production-deployment.md) - Production deployment
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md) - Development workflow
- **Security:** [`SECURITY.md`](SECURITY.md) - Security policy and reporting

---

## 🚨 Architectural Governance

This project follows a **strict tiered implementation model** to ensure security, privacy, and multi-tenant safety.

**Critical Rules:**
1. **No tier may be skipped** - Each tier builds on the previous
2. **No tier may be partially completed and left** - Complete all tasks in a tier
3. **All changes must preserve tenant isolation and privacy guarantees** - Security is non-negotiable
4. **CI must never lie** - Test failures must fail the build

**Current Progress (as of Dec 2025):** Tiers 0-3 Complete (100%), Tier 4 In Progress (63%), Tier 5 Not Started

For detailed tier information and current status, see [`docs/03-reference/tier-system.md`](docs/03-reference/tier-system.md).

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

### Run the App

```bash
cd src
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
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
- **End-to-end encryption** - Customer content is E2EE
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
