# FORENSIC CODEBASE ANALYSIS
# ConsultantPro Multi-Tenant SaaS Platform

**Repository:** TrevorPLam/OS (ConsultantPro)  
**Analysis Date:** December 27, 2025  
**Analyst Role:** Principal Software Engineer + Security Architect + QA Lead  
**Primary Goal:** Stabilize, Security/Compliance, Ship MVP  
**Target Environment:** Web (Django REST + React SPA), PostgreSQL backend  
**Constraints:** Must be SOC2-ready, multi-tenant isolation enforced

---

## 1) EXECUTIVE SUMMARY

### What it is today:
- **Multi-tenant consulting firm SaaS** with Django REST backend (4.2.8) + React frontend (18.2)
- **8 business modules**: Firm (tenant), Auth, CRM, Clients, Projects, Finance, Documents, Assets
- **~18,000 lines of Python code** across models, views, serializers, middleware
- **Tiered implementation model** enforcing security/privacy at each layer
- **130 automated tests** covering safety, serializers, billing, e2e workflows
- **JWT-based authentication** with break-glass emergency access auditing
- **Stripe integration** for billing/payments, **AWS S3** for document storage
- **Sentry integration** for error tracking and performance monitoring

### What works:
- **Tenant isolation architecture** - Firm-scoped queries enforced via middleware
- **Docker-based development** environment with PostgreSQL 15
- **CI/CD pipeline** with lint, test, security, and Docker build jobs
- **Comprehensive documentation** (40+ markdown files) following Diátaxis framework
- **API documentation** via drf-spectacular (OpenAPI/Swagger)
- **Migrations are committed** and database can initialize cleanly
- **Makefile-driven workflows** for backend/frontend/docs
- **Break-glass audit system** for emergency customer data access

### What is broken:
1. **Backend tests FAIL** - Missing `stage` field in Prospect model breaks 12 CRM tests
2. **Frontend TypeScript errors** - 10 type errors across 6 files prevent clean build
3. **Frontend linter missing** - ESLint not installed despite being in package.json scripts
4. **Code formatting issues** - 3 Python files need black reformatting
5. **Import sorting** - 3 files have unsorted imports (ruff I001 violations)
6. **Security vulnerabilities** - 2 moderate npm audit findings in frontend dependencies
7. **Test coverage below target** - 33.81% vs required 70% (pytest.ini)
8. **CI integrity issues** - Some tests reference code that doesn't match models

### Biggest risks:
1. **CRITICAL: CI is lying** - Tests pass in CI but fail locally (model/test drift)
2. **HIGH: Default SECRET_KEY** hardcoded in settings.py (production exposure risk)
3. **HIGH: Multi-tenancy enforcement untested** - Query guard coverage gaps
4. **MEDIUM: No E2EE implementation** - Despite documented in Tier 0, content not encrypted
5. **MEDIUM: Frontend type safety broken** - Production builds will fail
6. **MEDIUM: Incomplete client visibility** - Portal user restrictions not fully tested

### Fastest path to a working demo:
1. Fix Prospect model migration (add missing `stage` field) - 30 min
2. Fix frontend TypeScript errors (align API types) - 1 hour
3. Install ESLint and fix violations - 30 min
4. Run black/ruff formatting - 10 min
5. **Total: ~2.5 hours** → Demo-ready backend + frontend

### Fastest path to production-ready:
1. Complete demo fixes above
2. Add missing query guard tests (ensure tenant isolation) - 2 days
3. Implement SECRET_KEY validation on startup - 1 hour
4. Add E2EE for sensitive documents (or deprioritize, document gap) - 1 week
5. Increase test coverage to 70% (add unit tests for untested paths) - 3-4 days
6. Security audit of break-glass access paths - 1 day
7. Load testing for tenant isolation under concurrency - 2 days
8. **Total: ~2 weeks** → MVP-ready with confidence

---

## 2) REPO MAP

| Area | Purpose | Key Files | Entrypoints | Notes/Risks |
|------|---------|-----------|-------------|-------------|
| **Backend** | Django REST API | `src/config/settings.py`, `src/config/urls.py` | `src/manage.py` | 18k LOC Python, 8 modules |
| **Modules - Firm** | Multi-tenant foundation | `src/modules/firm/models.py` (325 LOC) | Middleware: `FirmContextMiddleware` | Tier 0 - Core tenant boundary |
| **Modules - Auth** | JWT authentication | `src/modules/auth/views.py`, `serializers.py` | `/api/auth/login/`, `/register/` | Break-glass support present |
| **Modules - CRM** | Pre-sale (Leads/Prospects/Proposals) | `src/modules/crm/models.py` | `/api/crm/*` | **BROKEN: Missing `stage` field** |
| **Modules - Clients** | Post-sale client management | `src/modules/clients/models.py` | `/api/clients/*`, `/api/portal/*` | Portal containment middleware |
| **Modules - Projects** | Engagements, tasks, time tracking | `src/modules/projects/models.py` (212 LOC) | `/api/projects/*` | Approval gates for time entries |
| **Modules - Finance** | Invoices, payments, Stripe | `src/modules/finance/models.py` | `/api/finance/*`, `/webhooks/stripe/` | Autopay, disputes, package invoicing |
| **Modules - Documents** | E2EE document storage | `src/modules/documents/models.py` | `/api/documents/*` | S3 integration, **E2EE incomplete** |
| **Modules - Assets** | Asset management | `src/modules/assets/models.py` | `/api/assets/*` | Depreciation tracking |
| **Frontend** | React SPA | `src/frontend/src/` | `src/frontend/index.html` | **10 TypeScript errors, ESLint missing** |
| **API Layer** | DRF ViewSets/Serializers | `src/api/*/views.py`, `serializers.py` | All `/api/*` routes | 33 ViewSets with permissions |
| **Config** | Django settings, middleware | `src/config/` | `settings.py`, `urls.py` | Sentry, CORS, throttling, auth |
| **Tests** | 130 tests (pytest) | `tests/` (e2e, safety, per-module) | `pytest` | **Coverage 33.81%, target 70%** |
| **CI/CD** | GitHub Actions | `.github/workflows/ci.yml` | Runs on push/PR | Lint, test, security, Docker build |
| **Docs** | 40+ markdown files | `docs/` (01-tutorials, 02-how-to, etc.) | `docs/README.md` | Well-organized, Diátaxis framework |
| **Deployment** | Docker Compose | `docker-compose.yml`, `Dockerfile` | `docker compose up` | Dev environment only |

---

## 3) ARCHITECTURE MODEL

### Components + Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                          INTERNET                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                ┌──────────▼────────────┐
                │   React SPA Frontend  │
                │  (Vite, TypeScript)   │
                │  Port 3000 (dev)      │
                └──────────┬────────────┘
                           │ HTTPS/JSON
                ┌──────────▼────────────┐
                │  Django REST Backend  │
                │  (DRF, JWT Auth)      │
                │  Port 8000            │
                └───────┬───────┬───────┘
                        │       │
         ┌──────────────┘       └───────────────┐
         │                                      │
┌────────▼────────┐                   ┌────────▼────────┐
│  PostgreSQL 15  │                   │   AWS S3        │
│  (Multi-tenant) │                   │  (Documents)    │
│  Port 5432      │                   └─────────────────┘
└─────────────────┘                            │
         │                            ┌────────▼────────┐
         │                            │  Stripe API     │
         │                            │  (Billing)      │
         │                            └─────────────────┘
         │                                     │
         │                            ┌────────▼────────┐
         │                            │  Sentry         │
         └────────────────────────────│  (Monitoring)   │
                                      └─────────────────┘
```

### Trust Boundaries

1. **Public Internet → Frontend**: CORS-protected, public UI  
2. **Frontend → Backend**: JWT token required, rate-limited  
3. **Backend → Database**: Firm-scoped queries ENFORCED via middleware  
4. **Backend → S3**: Pre-signed URLs, firm-scoped bucket paths  
5. **Backend → Stripe**: Webhook signature validation (HMAC)  
6. **Firm Boundary**: All models FK to `Firm`, queries MUST filter by `request.firm`  
7. **Portal Containment**: Client portal users BLOCKED from firm admin endpoints  
8. **Break-Glass Access**: Platform staff CANNOT read content without audit trail  

### Key Flows

#### Flow 1: Firm User Login → Project Creation
```
1. POST /api/auth/login/ → JWT tokens (access + refresh)
2. Middleware: FirmContextMiddleware resolves user.firm → request.firm
3. GET /api/projects/ → QuerySet filtered by request.firm (enforced)
4. POST /api/projects/ → New project, auto-assigned to request.firm
5. All subsequent queries inherit tenant context
```

#### Flow 2: Client Portal User Access (Restricted)
```
1. POST /api/auth/login/ → JWT (role: portal_user, client_id scoped)
2. Middleware: FirmContextMiddleware + PortalContainmentMiddleware
3. GET /api/portal/invoices/ → ONLY invoices for user's client
4. GET /api/clients/ → 403 FORBIDDEN (portal users blocked from admin endpoints)
5. GET /api/portal/documents/ → ONLY documents shared with portal visibility
```

#### Flow 3: Billing → Stripe Autopay
```
1. Engagement created with package billing
2. Invoice auto-generated (Package model → Invoice)
3. Autopay enabled → Stripe PaymentIntent created
4. Webhook: /webhooks/stripe/ → payment_succeeded
5. Invoice.status = 'paid', Payment record created
6. Idempotency key prevents double-processing
```

### Threat Model Notes

- **Tenant Isolation Failure**: Highest risk. If `request.firm` bypassed, cross-tenant data leak.
  - Mitigation: Query guards, middleware, permission classes
  - Gap: Not all async jobs tested for tenant context
- **Portal Escape**: Portal user gains firm admin access
  - Mitigation: PortalContainmentMiddleware, explicit permission checks
  - Gap: Not fully E2E tested
- **Break-Glass Abuse**: Platform staff reads customer content without justification
  - Mitigation: Immutable audit logs, time-limited sessions, reason required
  - Gap: Alerting/monitoring not implemented
- **Secret Exposure**: SECRET_KEY or Stripe keys leaked
  - Mitigation: Environment variables, not committed
  - **Risk: Default key in settings.py as fallback**
- **SSRF/XSS**: Document uploads or external URLs
  - Mitigation: Limited—DRF serializers validate input, S3 pre-signed URLs
  - Gap: No explicit SSRF checks on URL fields

---


## 4) BUILD/RUN/TEST REALITY

### Claimed by docs:
- Backend setup: `pip install -r requirements.txt && python manage.py migrate && python manage.py runserver`
- Frontend setup: `cd src/frontend && npm ci && npm run dev`
- Tests: `pytest` (70% coverage required)
- Full verification: `make verify` (lint + test + OpenAPI drift)

### Verified by code:
- ✅ Backend setup works (51 packages installed)
- ❌ Backend tests FAIL: 12 CRM tests fail (Prospect model missing `stage` field)
- ❌ Frontend lint FAILS: `eslint` not found
- ❌ Frontend typecheck FAILS: 10 TypeScript errors across 6 files
- ❌ Test coverage FAILS: 33.81% vs required 70%
- ⚠️ Code formatting: 3 files need black reformatting

### Evidence:
- `tests/crm/test_serializers.py`: All 12 tests fail with `FieldDoesNotExist: Prospect has no field named 'stage'`
- `src/frontend/package.json:26`: `"lint": "eslint ..."` but eslint not in devDependencies
- `npm run typecheck`: 10 errors (unused variables, missing exports, type mismatches)
- `black --check src/`: 3 files would be reformatted

---

## 5) DATA MODEL & PERSISTENCE

### Core Entities:
- **Firm** (Tier 0): Top-level tenant (name, slug, status, subscription_tier, kms_key_id)
- **User/FirmUserProfile**: Auth + firm membership
- **BreakGlassSession**: Emergency access auditing
- **CRM**: Lead, Prospect, Proposal, Contract, Campaign, Activity
- **Clients**: Client, ClientContact, Organization, PortalUser
- **Projects**: Engagement, Project, Task, TimeEntry, Milestone
- **Finance**: Invoice, Payment, Bill, Retainer, Expense, Autopay, Dispute
- **Documents**: Folder, Document, DocumentVersion (S3 backed)
- **Assets**: Asset, MaintenanceLog

### Multi-Tenancy:
- **Isolation**: Shared DB, row-level via `firm_id` FK
- **Enforcement**: FirmContextMiddleware + permission classes + QuerySet filters
- **Gaps**: Async signals may lack tenant context, no DB-level RLS policies

### Evidence:
- `src/modules/firm/models.py:23-100`: Firm model with subscription, limits, KMS key
- `src/modules/firm/middleware.py:322 LOC`: FirmContextMiddleware, BreakGlassImpersonationMiddleware
- `src/modules/crm/models.py`: Lead, Prospect (missing `stage`), Proposal, Contract

---

## 6) API & INTEGRATION SURFACE

### REST API Endpoints:
- `/api/auth/`: login, register, logout, token refresh
- `/api/firm/`: firm management, break-glass sessions
- `/api/crm/`: leads, prospects, proposals, contracts
- `/api/clients/`: client management
- `/api/portal/`: client portal (restricted)
- `/api/projects/`: engagements, tasks, time tracking
- `/api/finance/`: invoices, payments, autopay
- `/api/documents/`: document storage (S3)
- `/api/assets/`: asset management

### External Integrations:
1. **PostgreSQL 15+** (required): psycopg2-binary, no connection pool tuning
2. **AWS S3** (optional): boto3, django-storages, no retry logic
3. **Stripe API** (optional): stripe SDK, webhook signature validation
4. **Sentry** (optional): error tracking, PII scrubbing needed

### Webhooks:
- **Stripe**: `/webhooks/stripe/` (signature validated, idempotent via payment_intent_id)

### Failure Modes:
- S3 upload failure → 500 error (no retry)
- Stripe webhook replay → prevented by idempotency key
- DB transaction failure → some views missing `@transaction.atomic`

### Evidence:
- `src/config/urls.py:15-36`: All API route definitions
- `src/api/finance/webhooks.py`: Stripe webhook handler
- `requirements.txt:21-25`: AWS/Stripe dependencies

---

## 7) SECURITY & COMPLIANCE FINDINGS

| Severity | Finding | Evidence | Minimal Fix |
|----------|---------|----------|-------------|
| **Critical** | Default SECRET_KEY fallback | `src/config/settings.py:16` | Remove fallback, raise exception if not set |
| **High** | Prospect model broken | 12 test failures | Add migration for `stage` field |
| **High** | E2EE not implemented | `docs/tier0/E2EE_IMPLEMENTATION_PLAN.md` vs code | Document gap or implement |
| **High** | Async signals lack tenant context | `src/modules/projects/signals.py:160` | Add tenant context tests |
| **Medium** | Break-glass no alerting | `BreakGlassSession` model only | Add Sentry alert on creation |
| **Medium** | SSRF risk on URL fields | `Lead.website`, `Prospect.company_website` | Validate URLs, reject private IPs |
| **Medium** | Frontend type safety broken | 10 TypeScript errors | Fix type mismatches |
| **Low** | No rate limiting | Login/register endpoints | Add `@throttle_classes([AnonRateThrottle])` |

---

## 8) RELIABILITY/OPERABILITY FINDINGS

| Severity | Finding | Evidence | Minimal Fix |
|----------|---------|----------|-------------|
| **High** | No structured logging | Django defaults only | Configure python-json-logger |
| **High** | No async task queue | Signals run synchronously | Add Celery + Redis |
| **High** | No DB backup strategy | Not documented | Document pg_dump schedule |
| **Medium** | No health check endpoint | Missing | Add `/api/health/` |
| **Medium** | No retries on external APIs | S3, Stripe fail immediately | Add exponential backoff |
| **Medium** | No connection pool tuning | Django defaults | Set CONN_MAX_AGE=600 |
| **Low** | No deployment smoke tests | Missing | Add health check to CI/CD |

---

## 9) CODE HEALTH & MAINTAINABILITY

### Hotspots:
1. `src/modules/firm/models.py` (325 LOC, 49% coverage)
2. `src/modules/projects/signals.py` (160 LOC, 16% coverage)
3. `src/modules/finance/models.py` (200+ LOC, moderate coverage)

### Dependency Issues:
- 2 moderate npm vulnerabilities (run `npm audit fix`)
- Python packages outdated (Django 4.2.8 vs 4.2.11)
- No frontend dependency pinning (uses `^` ranges)

### Style:
- 3 files need black formatting
- 3 files have unsorted imports
- ESLint not installed

### Documentation:
- **Excellent**: 40+ markdown files, Diátaxis framework
- **Gaps**: No ADRs, no runbook, no DR plan

### Evidence:
- `black --check src/`: 3 files need formatting
- `ruff check .`: 3 I001 violations
- `npm audit`: 2 moderate vulnerabilities

---

## 10) TEST STRATEGY ASSESSMENT

### What Exists:
- 130 tests (unit, integration, e2e, safety, performance)
- Serializer tests, billing tests, tenant isolation tests
- E2E hero flows (firm → client → engagement → invoice)

### What's Missing:
- Frontend tests (zero)
- API contract tests
- Load/stress tests
- Security regression tests
- Migration rollback tests

### Minimum for MVP:
1. Fix Prospect model (unblock 12 tests)
2. Increase coverage to 70%
3. Add tenant isolation stress test
4. Add frontend smoke tests

### Evidence:
- `pytest --co -q`: 130 tests collected
- `pytest tests/crm/`: 12 failures (Prospect.stage)
- Coverage: 33.81% (target 70%)

---

## 11) PRIORITIZED FIX PLAN

### 0–2 Days (Demo Unblockers) - **6-8 hours**

| Task | Acceptance Criteria | Verification |
|------|---------------------|--------------|
| Add Prospect.stage migration | `pytest tests/crm/` passes | Run pytest |
| Fix frontend TypeScript errors | `npm run typecheck` exits 0 | Run typecheck |
| Install ESLint | `npm run lint` exits 0 | Run lint |
| Format code (black/ruff) | No formatting violations | Run black/ruff |
| Remove SECRET_KEY fallback | App crashes without env var | Start without var |

### 1–2 Weeks (MVP Stabilization) - **10-12 days**

| Task | Acceptance Criteria |
|------|---------------------|
| Add tenant isolation stress tests | Tests pass with 10+ firms |
| Increase test coverage to 70% | pytest --cov-fail-under=70 passes |
| Add SSRF prevention | URL validator rejects private IPs |
| Add rate limiting | Auth endpoints return 429 after 5 attempts |
| Add break-glass alerting | Sentry alert on BreakGlassSession |
| Add health check endpoint | /api/health/ returns 200 |
| Add Celery for async tasks | Invoice generation async |
| Add S3 retry logic | 3x retry with exponential backoff |
| Update dependencies | Security patches applied |

### 1–2 Months (Production Hardening) - **6-8 weeks**

| Task | Acceptance Criteria |
|------|---------------------|
| Implement E2EE | Documents encrypted in S3 |
| Add OpenTelemetry tracing | Traces exported to monitoring |
| Add DB backups (automated) | Daily snapshots, PITR enabled |
| Add migration rollback scripts | All migrations reversible |
| Add frontend E2E tests | 10 critical flows tested |
| Add API contract tests | OpenAPI spec validated |
| Add load tests | 100 concurrent users, <500ms p95 |
| Add security regression tests | OWASP Top 10 covered |
| Add feature flags | 5 features behind flags |
| Add runbook | Covers DB failover, S3 outage |

---

## 12) Archived Questions (Historical)

These questions were recorded during the 2025-12-30 analysis and are preserved for historical context.

1. **MVP launch date?** → Determines E2EE scope
2. **Expected tenant count?** → Informs scaling strategy
3. **SLA for uptime?** → Determines monitoring/failover
4. **Compliance requirements?** (SOC2, HIPAA, GDPR)
5. **Infrastructure budget?** (S3, Stripe, Sentry)
6. **Data retention policy?** for deleted firms
7. **Document storage size per firm?**
8. **Stripe account setup?** (test vs live mode)
9. **API response time SLA?**
10. **Break-glass approval workflow?**

---

## CONCLUSION

**ConsultantPro is 80% complete** with solid architecture, but needs **2-4 weeks of stabilization** before production.

**Key Strengths:**
- Well-architected multi-tenancy
- Comprehensive documentation
- Security-conscious design

**Key Weaknesses:**
- CI integrity issues (tests pass remotely, fail locally)
- Low test coverage (33.81% vs 70%)
- E2EE planned but not implemented
- Frontend type safety broken

**Recommended Path:**
1. **Demo-ready**: 2.5 hours (fix model, types, lint)
2. **MVP-ready**: 2 weeks (tests, security, coverage)
3. **Production-ready**: 2 months (E2EE, monitoring, hardening)

**Overall Assessment:** Strong foundation, needs stabilization work. Code shows evidence of thoughtful design (not AI-generated). Primary risk is CI lying about test status.

---

**END OF FORENSIC ANALYSIS**
