# Operations Guide

**Purpose:** Setup, environment variables, running the application, and data safety procedures for ConsultantPro.

**Audience:** Non-coder founder, operators, DevOps engineers.

**Evidence Status:** STATIC-ONLY verification (commands from README.md and Makefile, not executed in this agent session).

---

## 1. Prerequisites

**Evidence:** `README.md:55-58`

- **Python:** 3.11+ (evidence: `.github/workflows/ci.yml:10`)
- **PostgreSQL:** 15+ (evidence: `README.md:58`)
- **Node.js:** 18 (evidence: `.github/workflows/ci.yml:11` - for frontend only)

---

## 2. Initial Setup

### 2.1 Backend Setup

**Evidence:** `README.md:62-66`, `Makefile:13-32`

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**OR** use the Makefile target (which also sets up frontend and docs):

```bash
make setup
```

**What this does** (evidence: `Makefile:13-32`):
- Runs `make -C src setup` for backend
- Runs `make -C src/frontend setup` for frontend
- Reports PASS/FAIL status for each

### 2.2 Frontend Setup

**Evidence:** `Makefile:22`, `README.md:84-94`

```bash
cd src/frontend
npm ci
```

---

## 3. Environment Variables (Required)

**Evidence:** `src/config/settings.py:15-30`, `README.md:68-82`

### 3.1 Core Required Variables

```bash
# CRITICAL: Application will fail to start if these are missing
export DJANGO_SECRET_KEY="your-secret-key-here"
export DJANGO_DEBUG=True                    # Set to False for production
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
export POSTGRES_DB=consultantpro
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

# CORS (for frontend)
export CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Evidence for required status:**
- `DJANGO_SECRET_KEY`: `settings.py:17-24` raises `ValueError` if missing
- `DJANGO_DEBUG`: `settings.py:28` defaults to `False`
- Database vars: Referenced throughout `settings.py` (not shown in excerpt but required for Django)

### 3.2 Frontend Error Tracking (Optional)

**Evidence:** `README.md:84-94`

```bash
export VITE_SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"
export VITE_SENTRY_TRACES_SAMPLE_RATE="0.1"
```

If `VITE_SENTRY_DSN` is omitted, Sentry is disabled in the frontend.

### 3.3 Generate Secret Key

**Evidence:** `settings.py:21-23`

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 4. Running the Application

### 4.1 Apply Database Migrations

**Evidence:** `README.md:98-99`, `.github/workflows/ci.yml:107-110`

```bash
cd src
python manage.py migrate
```

### 4.2 Start Backend Development Server

**Evidence:** `README.md:100-101`

```bash
cd src
python manage.py runserver 0.0.0.0:8000
```

The application will be available at:
- **API**: http://localhost:8000/api/
- **Swagger UI**: http://localhost:8000/api/docs/ (evidence: `README.md:105`)
- **ReDoc**: http://localhost:8000/api/redoc/ (evidence: `README.md:106`)

### 4.3 Start Frontend Development Server

**Evidence:** `README.md` frontend section (not shown in excerpt), `Makefile:77-96`

```bash
make dev
```

**What this does** (evidence: `Makefile:77-96`):
- Runs `make -C src dev` for backend dev server
- Runs `make -C src/frontend dev` for frontend dev server
- Reports PASS/FAIL status

---

## 5. Docker Deployment (Alternative)

**Evidence:** `README.md:112-117`, `.github/workflows/ci.yml:213-231`

```bash
docker compose up --build
```

The Django server will be available at http://localhost:8000.

**Docker Build Verification:** CI runs docker build test (evidence: `.github/workflows/ci.yml:213-231`).

---

## 6. Data Safety & Backups

### 6.1 Database Backups

**STATUS:** UNKNOWN - No evidence of automated backup procedures found in repo.

**To verify:** Check for:
- Cron jobs or scheduled tasks
- Backup scripts in `/scripts/`
- Cloud provider backup configs

**Runbook:** See `docs/RUNBOOKS/RUNBOOK_backup-restore.md` - **UNKNOWN** (verify existence).

### 6.2 Document Storage

**Evidence:** `README.md:129` - "End-to-end encryption - Customer content is E2EE"

**Storage Backend:** UNKNOWN (assumed S3 based on `settings.py:84` AWS env vars, but not verified)

**Backup Strategy:** UNKNOWN - Requires verification of S3 versioning/backup policies.

### 6.3 Audit Log Retention

**Evidence:** `docs/codingconstitution.md:363` - "Sensitive actions are logged in an append-only audit trail."

**Retention Policy:** UNKNOWN - Verify retention period and archival strategy.

**Audit Export:** UNKNOWN - Verify if export tooling exists per TODO.md:216.

---

## 7. Common Operations

### 7.1 Run Tests

**Evidence:** `Makefile:56-75`, `README.md:149-151`

```bash
# All tests
make test

# OR backend only
cd src
pytest
```

**What this does** (evidence: `Makefile:56-75`):
- Runs `make -C src test` for backend tests
- Runs `make -C src/frontend test` for frontend tests
- Reports PASS/FAIL status

### 7.2 Run Linters

**Evidence:** `Makefile:34-54`

```bash
make lint
```

**What this does** (evidence: `Makefile:34-54`):
- Runs `make -C src lint` for backend lint (ruff, black, isort)
- Runs `make -C src/frontend lint` for frontend lint
- Runs `make -C docs validate` for docs validation
- Reports PASS/FAIL status

### 7.3 Verify Everything (CI Equivalent)

**Evidence:** `Makefile:118-158`

```bash
make verify
```

**What this does** (evidence: `Makefile:118-158`):
- Backend lint
- Frontend lint
- Docs validation
- Backend tests
- Frontend tests
- OpenAPI schema generation
- OpenAPI drift check
- Reports comprehensive PASS/FAIL status

---

## 8. Deployment

**Evidence:** `README.md:24` references `docs/02-how-to/production-deployment.md` (UNKNOWN - directory doesn't exist yet).

**Archived Legacy:** `DEPLOYMENT_STEPS.md` moved to `docs/ARCHIVE/roadmap-legacy-2025-12-30/`.

**Current Reference:** See `docs/RUNBOOKS/RUNBOOK_release.md` - **TO BE CREATED**.

### 8.1 Staging Deployment

**Evidence:** `.github/workflows/ci.yml:294-323` - Automated staging deployment on main branch push.

**Trigger:** Push to `main` branch after all CI checks pass.

**Status:** UNKNOWN - Actual deployment steps marked as comments in workflow (lines 312-322).

### 8.2 Production Deployment

**STATUS:** UNKNOWN - No production deployment workflow found in CI.

**To verify:** Check for:
- Production deployment workflow file
- Deployment runbook
- Rollback procedures (evidence: `docs/runbooks/ROLLBACK.md` exists per `docs/RUNBOOKS/README.md:12`)

---

## 9. Secrets Management

**Evidence:** `docs/codingconstitution.md:117-120` - Secrets Discipline

### 9.1 Rules (from Constitution)

- Secrets must not be committed (enforced by `.github/workflows/ci.yml:206-210` - TruffleHog scan)
- Secrets must not be printed in logs (evidence: TODO.md:248 - DOC-21.2 no-content logging)
- Secrets must be rotatable (evidence: constitution requirement, implementation UNKNOWN)

### 9.2 Where Secrets are Stored

**Development:**
- Environment variables (evidence: `settings.py:17`, `README.md:68-82`)

**Production:**
- UNKNOWN - Verify secret management service (AWS Secrets Manager, HashiCorp Vault, etc.)

---

## 10. Monitoring & Observability

**Evidence:** `README.md:84-94` (Sentry), TODO.md:212 (DOC-21.1 observability baseline)

### 10.1 Error Tracking

**Frontend:** Sentry (evidence: `README.md:84-94`, optional via `VITE_SENTRY_DSN`)

**Backend:** UNKNOWN - Verify Sentry configuration for backend.

### 10.2 Metrics & Alerts

**Evidence:** TODO.md:212 - "DOC-21.1 Observability baseline: correlation IDs end-to-end; tenant-safe metrics; DLQ + integration lag visibility ✅ Completed Dec 30, 2025"

**Metrics Documented:** `docs/ALERT_CONFIGURATION.md` (evidence: file exists per inventory)

**Metrics Status:** STATIC-ONLY - Verify actual metrics collection in production.

---

## 11. Troubleshooting

For operational issues, see:
- **Troubleshooting Guide:** `docs/TROUBLESHOOTING.md` (evidence: created in this session)
- **Runbooks:** `docs/RUNBOOKS/` (evidence: `docs/runbooks/README.md`)
  - Rollback: `docs/RUNBOOKS/ROLLBACK.md` ✅ EXISTS
  - Incident Response: **UNKNOWN** (marked TODO in runbooks/README.md:18)

---

## 12. Health Checks

**Evidence:** TODO.md:41 - "CONST-2: Implement health check endpoints"

**Endpoints:**
- **Liveness:** `/health` (evidence: implemented in `src/config/health.py`)
- **Readiness:** `/ready` (evidence: implemented in `src/config/health.py`)

**Status:** STATIC-ONLY - Verify actual endpoint paths by checking `config/urls.py`.

---

## Summary: Operator Checklist

**To run the application locally:**
1. ✅ Install Python 3.11+ and PostgreSQL 15+
2. ✅ Set required environment variables (Section 3.1)
3. ✅ Run `make setup` OR manually install dependencies
4. ✅ Run `cd src && python manage.py migrate`
5. ✅ Run `cd src && python manage.py runserver 0.0.0.0:8000`

**To verify everything works:**
1. ✅ Run `make verify` (runs all lint, test, and validation checks)

**For production deployment:**
1. ⚠️ UNKNOWN - See deployment runbook (to be created)

---

**Verification Status:** STATIC-ONLY
**Commands Referenced:** Makefile:11-158, README.md:62-117, settings.py:15-95
**Commands NOT Executed:** This document is based on static code analysis. Commands have not been run in this agent session.
