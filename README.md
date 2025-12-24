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

## Documentation Map

Start here for a cohesive view of the documentation set:

- **Project docs index:** [`docs/README.md`](docs/README.md)
- **Authoritative rules (must-follow):** [`docs/claude/NOTES_TO_CLAUDE.md`](docs/claude/NOTES_TO_CLAUDE.md)
- **Tier backlog:** [`TODO.md`](TODO.md)
- **API usage guide:** [`API_USAGE.md`](API_USAGE.md)
- **Deployment guide:** [`DEPLOYMENT.md`](DEPLOYMENT.md)

---

## 🚨 Architectural Governance

This project follows a **strict tiered implementation model** to ensure security, privacy, and multi-tenant safety.

### Tier Structure

| Tier | Focus | Status |
|------|-------|--------|
| **Tier 0** | Foundational Safety (tenancy, privacy, break-glass) | 🔴 Not Started |
| **Tier 1** | Schema Truth & CI Truth (migrations, honest CI) | 🔴 Not Started |
| **Tier 2** | Authorization & Ownership (permissions, scoping) | 🔴 Not Started |
| **Tier 3** | Data Integrity & Privacy (purge, audit, signing) | 🔴 Not Started |
| **Tier 4** | Billing & Monetization (engagement-centric) | 🔴 Not Started |
| **Tier 5** | Durability, Scale & Exit (performance, offboarding) | 🔴 Not Started |

### Critical Rules

1. **No tier may be skipped**
2. **No tier may be partially completed and left**
3. **If code conflicts with `docs/claude/NOTES_TO_CLAUDE.md`, code must change**
4. **All changes must preserve tenant isolation and privacy guarantees**
5. **CI must never lie**

---

## 🚀 Quickstart (Local Development)

### Prerequisites

- Python 3.11+
- PostgreSQL 15+

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure Environment

Set the required environment variables (see `DEPLOYMENT.md` for production-ready values):

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
