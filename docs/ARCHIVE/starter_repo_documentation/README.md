Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: CODEBASECONSTITUTION.md; READMEAI.md; TODO.md; docs/DOCS_INDEX.md; docs/REPO_MAP.md; docs/CHANGELOG.md

ConsultantPro is a multi-tenant SaaS platform for service-based firms (consulting, accounting, legal, etc.) with emphasis on privacy-first architecture and tiered governance.

**Core Capabilities:**
- CRM (leads, prospects, proposals, pipeline management)
- Client Management (portal, documents, projects, tasks)
- Finance (billing, invoicing, payments via Stripe/Square)
- Calendar (scheduling, event types, booking links - Calendly replacement)
- Marketing Automation (tags, segments, campaigns, visual workflow builder)
- Communications (email ingestion, SMS, conversations, threads)
- Integrations (QuickBooks, Xero, DocuSign, Active Directory, webhooks)

**Core Principles:**
- **Multi-tenant isolation** - Hard boundaries between firms with RLS enforcement
- **Privacy by default** - Platform staff cannot read customer content without audited break-glass access
- **Modular monolith** - Bounded contexts per domain, testable in isolation
- **API-first** - REST API with OpenAPI documentation, versioning policy
- **Secure defaults** - No secrets in repo, RLS enabled, webhook signature verification

**Tech Stack:**
- **Backend:** Django 4.2 LTS + Django REST Framework + PostgreSQL 15
- **Frontend:** React + TypeScript + Vite
- **Integrations:** Stripe, Square, DocuSign, QuickBooks, Xero, Twilio
- **Deployment:** Docker + Docker Compose, Gunicorn, AWS S3
- **Testing:** pytest + pytest-django + coverage
- **CI/CD:** GitHub Actions (lint, test, security, Docker build, docs validation)

Start here (mandatory):
1) CODEBASECONSTITUTION.md
2) READMEAI.md
3) TODO.md
4) docs/DOCS_INDEX.md
5) docs/SETUP.md
6) docs/ARCHITECTURE.md
7) docs/REPO_MAP.md
