# CODEBASECONSTITUTION.md — ConsultantPro Governance & Repository Standards
Document Type: Governance
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active
Dependencies: docs/AMENDMENTS.md; docs/SECURITY_BASELINE.md; docs/EMERGENCY_PROTOCOL.md; docs/DEPRECATION.md

This document defines the non-negotiable structure, standards, and workflows for the ConsultantPro Django monorepo.
When in conflict with any other document, this Constitution prevails.

------------------------------------------------------------
1. Mission
------------------------------------------------------------
Build a multi-tenant SaaS platform for service-based firms with privacy-first architecture, modular design, and secure defaults.

------------------------------------------------------------
2. Core Modules (Django Apps)
------------------------------------------------------------
**Tier 0 - Foundation:**
- firm: Multi-tenant foundation (Workspace/Firm management, RLS enforcement)
- auth: Authentication & authorization (JWT, OAuth, SAML, MFA)

**Core Business Domains:**
- crm: Pre-sale (Leads, Prospects, Proposals, Pipeline)
- clients: Post-sale (Client management, portal, documents)
- projects: Project and task management
- finance: Billing, invoicing, payments (Stripe/Square integration)
- documents: Document management with versioning

**Engines & Automation:**
- pricing: Pricing engine with versioned rulesets
- delivery: Delivery templates and DAG instantiation
- recurrence: Recurrence engine for recurring events
- orchestration: Multi-step workflow orchestration
- automation: Marketing automation (triggers, actions, visual builder)

**Communications & Integration:**
- communications: Messages, conversations, threads
- email_ingestion: Email ingestion with mapping/triage
- calendar: Calendar, appointments, booking links (Calendly replacement)
- sms: SMS messaging (Twilio integration)
- webhooks: General webhook platform for external integrations

**Supporting Modules:**
- core: Shared infrastructure (audit, purge utilities, governance)
- marketing: Marketing automation primitives (tags, segments, campaigns)
- support: Support/ticketing with SLA tracking
- onboarding: Client onboarding workflows
- knowledge: Knowledge system (SOPs, training, playbooks)
- jobs: Background job queue and DLQ
- snippets: Quick text insertion (HubSpot-style)
- accounting_integrations: QuickBooks and Xero integrations
- esignature: DocuSign e-signature integration
- ad_sync: Active Directory integration and user synchronization

**Rule:** Modules must respect boundaries. Cross-module dependencies must be explicit and justified.

------------------------------------------------------------
3. System Model (Django Modular Monolith)
------------------------------------------------------------
- **Backend:** Django 4.2 LTS with Django REST Framework
- **Database:** PostgreSQL 15 with Row-Level Security (RLS)
- **API:** REST with OpenAPI documentation (drf-spectacular)
- **Frontend:** React + TypeScript + Vite
- **Authentication:** JWT (SimpleJWT) + OAuth/SAML (django-allauth) + MFA (django-otp)
- **Integrations:** Stripe, Square, DocuSign, QuickBooks, Xero, Twilio
- **Deployment:** Docker + Docker Compose, Gunicorn for production

**Prohibitions:**
- No direct SQL in views (use ORM or explicit raw SQL with justification)
- No hardcoded secrets (environment variables only)
- No cross-module imports without documented contracts

------------------------------------------------------------
4. Required Repo Structure
------------------------------------------------------------
/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── TODO.md
├── SECURITY.md
├── Makefile (orchestration: setup, lint, test, verify)
├── pyproject.toml (Python tooling config: ruff, black, pytest)
├── requirements.txt (Python dependencies)
├── requirements-dev.txt (Development dependencies)
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── src/
│   ├── manage.py
│   ├── config/ (Django settings)
│   ├── modules/ (Business modules/Django apps)
│   ├── api/ (API configuration)
│   ├── frontend/ (React frontend)
│   └── tests/ (Test suites)
├── docs/
│   ├── README.md (Documentation map - Diátaxis framework)
│   ├── codingconstitution.md (This file or equivalent)
│   ├── REPO_MAP.md (Directory structure explanation)
│   ├── 01-tutorials/ (Learning-oriented)
│   ├── 02-how-to/ (Problem-solving guides)
│   ├── 03-reference/ (Technical reference, API docs)
│   ├── 04-explanation/ (Understanding-oriented)
│   ├── 05-decisions/ (ADRs)
│   └── 06-user-guides/ (End-user documentation)
├── scripts/ (Utility scripts)
└── .github/
    └── workflows/ (CI/CD pipelines)

------------------------------------------------------------
5. Documentation Standards
------------------------------------------------------------
All governance/workflow/reference docs must include standard headers:
- Document Title
- Document Type (Governance/Workflow/Reference/Explanation)
- Version
- Last Updated
- Owner
- Status
- Dependencies

Documentation follows Diátaxis framework (tutorials, how-to, reference, explanation).

------------------------------------------------------------
6. Security & Privacy Requirements
------------------------------------------------------------
- **Multi-tenant isolation:** RLS policies on all tenant-scoped models
- **Privacy by default:** Platform staff cannot read customer content without break-glass access
- **No secrets in repo:** All secrets via environment variables
- **Audit logging:** All sensitive operations logged with metadata
- **Webhook security:** Signature verification for all webhook endpoints
- **Rate limiting:** Brute force protection on authentication endpoints
- **Permission staging:** Gradual permission requests with justification

------------------------------------------------------------
7. API Standards
------------------------------------------------------------
- REST API with OpenAPI/Swagger documentation
- Versioning policy: /api/v1/, /api/v2/ with deprecation warnings
- Consistent response formats (success, error, pagination)
- API endpoint authorization mapping documented
- Deprecation policy: 6-month minimum notice for breaking changes

------------------------------------------------------------
8. Testing Requirements
------------------------------------------------------------
- pytest + pytest-django for unit and integration tests
- Coverage target: 80% minimum for critical paths
- Tests for: model constraints, permissions, API endpoints, integration flows
- CI pipeline must pass: lint, test, security, Docker build

------------------------------------------------------------
9. Change Control Protocol
------------------------------------------------------------
- Meaningful changes require CHANGELOG entry
- ADRs for architectural decisions
- PR template with checklist (Definition of Done)
- Security changes require security review
- Breaking changes require deprecation notice

------------------------------------------------------------
10. Amendments
------------------------------------------------------------
Constitutional changes require:
1. ADR documenting the change
2. Impact analysis
3. Migration plan
4. Approval from repository owner

See docs/AMENDMENTS.md for amendment history.
