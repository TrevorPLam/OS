# Architecture Analysis (Diamond Standard)

## Architecture Inventory

- System shape: modular monolith backend with a separate SPA frontend.
  - Evidence: `backend/config/settings.py` (INSTALLED_APPS list of domain modules), `frontend/package.json` (React + `Vite` app), `repo.manifest.yaml` (structure: backend/frontend).

- Primary runtime units:
  - Django web app (WSGI) with `Gunicorn` for production.
    - Evidence: `Dockerfile` (CMD uses `gunicorn ... config.wsgi:application`), `backend/config/wsgi.py`.
  - Local dev web service (Django `runserver`).
    - Evidence: `docker-compose.yml` service `web` runs `python manage.py runserver`.
  - PostgreSQL database.
    - Evidence: `docker-compose.yml` service `db`, `backend/config/settings.py` `DATABASES`.
  - Background job queue modeled in DB (JobQueue/DLQ) with enqueue usage.
    - Evidence: `backend/modules/jobs/models.py`, `backend/modules/automation/executor.py`.
  - Worker runtime or scheduler for job queue.
    - Insufficient evidence: no worker process, management command, or service definition found.
    - Evidence: `docker-compose.yml` defines only `web` and `db`.

- Data stores & ownership:
  - PostgreSQL as primary store with Django migrations per module.
    - Evidence: `backend/config/settings.py` `DATABASES`, `backend/modules/**/migrations/*.py`.
  - Tenant boundary = Firm; domain records are firm-scoped.
    - Evidence: `backend/modules/firm/README.md`, `backend/modules/clients/models/clients.py`, `backend/modules/crm/models/leads.py`.
  - S3 document storage for documents module.
    - Evidence: `backend/modules/documents/services.py`, `backend/config/settings.py` `AWS_*`, `requirements.txt` `boto3`.
  - Cache dependency used in readiness check; cache backend configuration.
    - Insufficient evidence: no cache configuration found in `backend/config/settings.py`.
    - Evidence: `backend/config/health.py` uses `django.core.cache`.

- External integrations:
  - Stripe payments.
    - Evidence: `backend/modules/finance/services.py`, `backend/config/settings.py` `STRIPE_*`.
  - Square payments.
    - Evidence: `backend/modules/finance/square_service.py` (uses `settings.SQUARE_*`).
  - Twilio SMS webhooks.
    - Evidence: `backend/modules/sms/webhooks.py`, `backend/config/env_validator.py` (TWILIO env checks).
  - DocuSign e-signature.
    - Evidence: `backend/modules/esignature/docusign_service.py`, `backend/config/settings.py` `DOCUSIGN_*`.
  - QuickBooks + Xero accounting.
    - Evidence: `backend/modules/accounting_integrations/quickbooks_service.py`, `backend/modules/accounting_integrations/xero_service.py`.
  - Google + Microsoft Calendar.
    - Evidence: `backend/modules/calendar/google_service.py`, `backend/modules/calendar/microsoft_service.py`, `backend/modules/calendar/sync_service.py`.
  - Salesforce, Slack, Google Analytics.
    - Evidence: `backend/modules/integrations/models.py`, `backend/modules/integrations/views.py`.
  - Active Directory LDAP/LDAPS.
    - Evidence: `backend/modules/ad_sync/connector.py`, `requirements.txt` (`ldap3`).
  - Sentry error tracking.
    - Evidence: `backend/config/sentry.py`, `frontend/package.json` (`@sentry/react`).

- Build graph:
  - Root `Makefile` orchestrates backend/frontend workflows.
    - Evidence: `Makefile`.
  - Backend dependencies pinned in `requirements.txt` and dev deps in `requirements-dev.txt`.
    - Evidence: `requirements.txt`, `requirements-dev.txt`.
  - Frontend dependencies pinned in `package-lock.json`.
    - Evidence: `frontend/package-lock.json`.
  - Toolchain hints for Python/Node/Go.
    - Evidence: `mise.toml`.

- Deployment graph:
  - Backend container image via `Dockerfile`.
    - Evidence: `Dockerfile`.
  - Local composition with `web` and `db`.
    - Evidence: `docker-compose.yml`.
  - Production infra (Kubernetes/Helm/Terraform/Serverless).
    - Insufficient evidence: no infra manifests found.
    - Evidence: no files under `docs/`, `.github/`, or infra directories.
  - Frontend deployment artifacts.
    - Insufficient evidence: no frontend `Dockerfile` or hosting config found.
    - Evidence: only `frontend/` source + build scripts in `frontend/package.json`.

- Control planes & config:
  - Environment-driven configuration with startup validation.
    - Evidence: `backend/config/settings.py`, `backend/config/env_validator.py`, `backend/config/wsgi.py`.
  - Repo-level verification guidance.
    - Evidence: `repo.manifest.yaml`.
  - `.env.example` template.
    - Insufficient evidence: referenced but missing.
    - Evidence: `backend/config/env_validator.py` prints "See .env.example".

- Operational hooks:
  - Health and readiness endpoints.
    - Evidence: `backend/config/health.py`, `backend/config/urls.py`.
  - Logging configuration and telemetry helper.
    - Evidence: `backend/config/settings.py` `LOGGING`, `backend/modules/core/telemetry.py`.
  - Sentry error tracking.
    - Evidence: `backend/config/sentry.py`.
  - Metrics/tracing stack and runbooks.
    - Insufficient evidence: no OTEL/Prometheus/Grafana config or runbooks found.
    - Evidence: no `docs/` directory; no config files for metrics.

## Rubric Scores (A–I)

A) Architectural Clarity & Boundaries — Score: 2/4
Rationale: Clear module list and API routing, plus explicit firm boundary; however, contracts and ADRs are missing and several docs are referenced but not present.
Evidence: `backend/config/settings.py` (module boundaries), `backend/config/urls.py` (module routing), `backend/modules/firm/README.md`.
Fixes:

- Add ADRs under `docs/adr/` for tenancy, job system, and sync strategy (Insufficient evidence of ADRs today; no `docs/` directory).
- Commit OpenAPI artifact to repo (e.g., `backend/openapi.yaml`) using `backend/Makefile` `openapi` target (file missing).
- Add explicit module boundary tests (import-linter or custom checks) to enforce layer rules.

Risk if not addressed: Medium.

B) Dependency Hygiene & Build Integrity — Score: 2/4
Rationale: Dependencies are pinned; local `Makefile` verification exists; no CI gating or dependency-direction enforcement.
Evidence: `requirements.txt`, `frontend/package-lock.json`, `Makefile`, no `.github/workflows/`.
Fixes:

- Add CI workflow to run `make verify` and fail on lint/test/type check/build drift.
- Add dependency boundary enforcement (import-linter or architecture tests).
- Add lock file/toolchain enforcement in CI (e.g., verify `python=3.11`, `node=20` via `mise.toml`).

Risk if not addressed: Medium.

C) Runtime Topology & Scalability Design — Score: 2/4
Rationale: Web + DB runtime defined; job queue modeled with idempotency but no worker runtime or scheduler process defined.
Evidence: `docker-compose.yml` (`web`, `db` only), `backend/modules/jobs/models.py`, `backend/modules/automation/executor.py`.
Fixes:

- Add worker runtime (management command or service) and include it in `docker-compose.yml`.
- Document scaling strategy for queue processing and web concurrency.
- Add backpressure/timeout policy for external integrations in shared clients.

Risk if not addressed: High.

D) Data Architecture & Consistency Model — Score: 2/4
Rationale: Firm-scoped data ownership is evident and migrations exist, but there is no documented cross-module consistency policy and no data ownership docs.
Evidence: `backend/modules/clients/models/clients.py`, `backend/modules/crm/models/leads.py`, `backend/modules/**/migrations/*.py`, `backend/modules/firm/README.md`.
Fixes:

- Add data ownership and consistency doc per module (Insufficient evidence; no `docs/` directory).
- Document shared table usage or cross-module access patterns.
- Add schema ownership notes to each module README.

Risk if not addressed: Medium.

E) Reliability Engineering & Failure Containment — Score: 2/4
Rationale: Health/readiness endpoints and slow-query monitoring exist; retries appear in specific services; no centralized retry/backoff policy or failure-mode docs.
Evidence: `backend/config/health.py`, `backend/config/query_monitoring.py`, `backend/modules/orchestration/executor.py`, `backend/modules/sms/webhooks.py`.
Fixes:

- Centralize retry/timeout policies in shared client wrappers or settings.
- Add runbooks or failure-mode docs (Insufficient evidence; no `docs/` directory).
- Add worker health checks if job runtime is introduced.

Risk if not addressed: Medium.

F) Security Architecture & Supply Chain — Score: 2/4
Rationale: Env validation, CSP, rate limiting, and webhook verification exist; security tooling present in dev deps but not enforced via CI; no SBOM/signing.
Evidence: `backend/config/env_validator.py`, `backend/config/csp_middleware.py`, `backend/config/settings.py` `WEBHOOK_RATE_LIMITS`, `requirements-dev.txt`.
Fixes:

- Add CI steps for `bandit`, `pip-audit`, and `safety` plus SBOM generation.
- Add secret management docs (Insufficient evidence; no security docs found).
- Add policy for webhook secret enforcement across providers.

Risk if not addressed: High.

G) Observability & Operability — Score: 2/4
Rationale: Structured logging and Sentry are configured; telemetry helper exists; no metrics/tracing backend or dashboards-as-code.
Evidence: `backend/config/settings.py` `LOGGING`, `backend/config/sentry.py`, `backend/modules/core/telemetry.py`.
Fixes:

- Add metrics/tracing config (Prometheus/OpenTelemetry) and export endpoints.
- Add dashboards/alerts-as-code and incident response docs (Insufficient evidence; no docs found).

Risk if not addressed: Medium.

H) Test Architecture & Quality Gates (Architecture-Level) — Score: 2/4
Rationale: Tests exist with `pytest` configuration and frontend e2e; no CI gates enforcing them.
Evidence: `pytest.ini`, `tests/contract_tests.py`, `frontend/e2e/`, `frontend/playwright.config.ts`, `Makefile` `verify`.
Fixes:

- Add CI workflow to run unit/integration/e2e tests.
- Document contract test scope and expected artifacts (Insufficient evidence; docs referenced but not present).
- Add integration test environment documentation (docker-compose usage or `testcontainers`).

Risk if not addressed: Medium.

I) Configuration, Environments, and Release Engineering — Score: 2/4
Rationale: Environment variable validation and a version file exist; no `.env.example`, environment parity docs, or release notes.
Evidence: `backend/config/env_validator.py`, `backend/config/wsgi.py`, `VERSION`.
Fixes:

- Add `.env.example` and environment matrix doc.
- Add release notes/changelog and deployment strategy doc.
- Add CI release tagging based on `VERSION`.

Risk if not addressed: Medium.

## Diamond Gate Check

- Reproducible builds + pinned dependencies/toolchains: Partial pass.
  Evidence: `requirements.txt`, `frontend/package-lock.json`, `mise.toml`.
- Clear module/service boundaries with documented contracts: Fail.
  Evidence: module boundaries exist in `backend/config/settings.py`, but no ADRs or committed OpenAPI artifact (`backend/openapi.yaml` missing).
- CI that runs tests and build verification: Fail.
  Evidence: no `.github/workflows/` found; `Makefile` `verify` exists but not enforced.
- Supply-chain/security scanning baseline: Fail.
  Evidence: `requirements-dev.txt` includes `bandit`, `safety`, `pip-audit`, but no CI configs present.
- Deployment artifacts exist or explicitly documented: Partial pass.
  Evidence: `Dockerfile`, `docker-compose.yml`; no production infra manifests found.
- Observability hooks exist or explicitly documented: Partial pass.
  Evidence: `backend/config/settings.py` logging + `backend/config/sentry.py`; no metrics/tracing configs or dashboards found.

Verdict: Silver (Diamond gates not satisfied).

## Top Risks

1) No CI enforcement for tests/build/security.
   Evidence: no `.github/workflows/` files; `Makefile` `verify` exists.
   Mitigation: add CI workflow to run `make verify` and security scans.

2) Background job runtime undefined despite queue models.
   Evidence: `backend/modules/jobs/models.py` defines JobQueue/DLQ; `docker-compose.yml` has no worker service.
   Mitigation: implement worker process and deploy it (add service definition + docs).

3) Architecture and contract documentation missing or referenced but absent.
   Evidence: no `docs/` directory; `backend/Makefile` references OpenAPI generation but `backend/openapi.yaml` missing.
   Mitigation: add ADRs, commit OpenAPI artifacts, and create architecture docs.

4) Observability incomplete (no metrics/tracing or dashboards).
   Evidence: logging and Sentry configured; no OTEL/Prometheus/Grafana configs found.
   Mitigation: add metrics/tracing exporters and dashboards-as-code.

5) Supply-chain security not enforced.
   Evidence: scanners listed in `requirements-dev.txt` but no CI; no SBOM/signing configs found.
   Mitigation: wire scanners into CI and generate SBOM/signing artifacts.

## 90-Day Plan

0-2 weeks

- Add CI workflow running `make verify` and security scanners.
  Evidence: `Makefile` `verify`, `requirements-dev.txt` tools.
- Commit OpenAPI artifact generated by `backend/Makefile openapi`.
  Evidence: `backend/Makefile` has `openapi` target; `backend/openapi.yaml` missing.
- Add `.env.example` and environment configuration doc.
  Evidence: `backend/config/env_validator.py` references `.env.example`; file missing.

2-6 weeks

- Define job worker runtime and add deployment entry (service or supervisor).
  Evidence: `docker-compose.yml` lacks worker service; `backend/modules/jobs/models.py` exists.
- Create ADRs for tenancy model, job system, and sync strategy.
  Evidence: no `docs/` directory found.
- Add metrics/tracing configuration and collection endpoints.
  Evidence: no OTEL/Prometheus configs found.

6-12 weeks

- Document data ownership and consistency per module.
  Evidence: firm-scoped models exist but no ownership docs.
- Introduce SBOM generation and signing in CI.
  Evidence: no SBOM/signing configs found.
- Document deployment strategies (e.g., blue/green/canary if applicable).
  Evidence: no deployment docs found.
