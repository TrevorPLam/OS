# Dependencies

Document Type: Reference
Last Updated: 2026-01-08

## Purpose
This document explains why each major dependency exists, where it is used, and what to consider before upgrades.
Sources of truth:
- `requirements.txt` (runtime dependencies)
- `requirements-dev.txt` (developer tooling)

If a dependency’s usage cannot be verified in code, it is marked **UNKNOWN** with the search used.

## Runtime dependencies (`requirements.txt`)

| Dependency | Purpose | Usage in repo | Alternatives | Upgrade considerations |
| --- | --- | --- | --- | --- |
| Django | Core web framework (Django 4.2 LTS). | Used across the Django project (e.g., `src/manage.py`, `src/config/settings.py`, migrations under `src/modules/*/migrations`). | **UNKNOWN** (no alternatives evaluated in-repo). | Track Django 4.2 LTS release notes; verify migrations, admin, and middleware compatibility before upgrading. |
| djangorestframework | REST API framework for Django. | API views and permissions (e.g., `src/permissions.py`, `src/modules/sms/views.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Review DRF release notes; verify authentication/permissions behavior and schema generation. |
| django-cors-headers | CORS middleware for Django. | Settings config (`src/config/settings.py`, `src/config/settings_auth_test.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Ensure middleware ordering remains correct; re-validate allowed origins after upgrades. |
| django-filter | Query filtering for DRF viewsets. | Filter backends in viewsets (e.g., `src/modules/crm/views.py`, `src/modules/knowledge/views.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Check filter backend API changes and field lookup behavior in DRF integrations. |
| psycopg2 | PostgreSQL driver. | **UNKNOWN**: no direct imports found via `rg -n "psycopg2" src/`; used by Django database backend. | **UNKNOWN** (no alternatives evaluated in-repo). | Keep aligned with PostgreSQL server/client versions; confirm libpq headers available in build environment. |
| djangorestframework-simplejwt | JWT auth support. | Auth flows (e.g., `src/modules/auth/authentication.py`, `src/modules/auth/saml_views.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Verify token rotation/blacklist behavior and settings compatibility when upgrading. |
| cryptography | Encryption primitives (Fernet). | Field encryption and AD sync (`src/modules/core/encryption.py`, `src/modules/ad_sync/sync_service.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Track Python/OS crypto backend requirements; re-test encryption/decryption and key rotation paths. |
| django-ratelimit | Rate limiting decorators. | Webhooks (`src/modules/sms/webhooks.py`, `src/api/finance/webhooks.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Validate decorator semantics and cache backend configuration after upgrades. |
| django-allauth | OAuth/social auth integration. | OAuth flows and settings (e.g., `src/modules/auth/oauth_views.py`, `src/config/settings.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Review provider API changes and allauth configuration keys after upgrades. |
| python3-saml | SAML authentication. | SAML endpoints (`src/modules/auth/saml_views.py`, `src/modules/auth/urls.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Verify IdP metadata parsing and XMLsec compatibility; library appears stale (see TODO T-035). |
| django-otp | MFA (TOTP) support. | MFA views and settings (`src/modules/auth/mfa_views.py`, `src/config/settings.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Re-test device enrollment and token validation after upgrades. |
| qrcode | QR code generation for MFA. | MFA QR generation (`src/modules/auth/mfa_views.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm SVG/PNG output compatibility with client apps after upgrades. |
| ldap3 | LDAP/Active Directory integration. | AD sync connector (`src/modules/ad_sync/connector.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Validate LDAP TLS settings and error handling; re-test against AD servers. |
| drf-spectacular | OpenAPI schema generation. | API schema generation and settings (`src/Makefile`, `src/config/settings.py`, `src/modules/ad_sync/views.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm schema output and annotation APIs; re-generate docs after upgrades. |
| boto3 | AWS SDK (KMS, S3, ACM, SES). | AWS clients (`src/modules/core/encryption.py`, `src/modules/core/purge.py`, `src/modules/clients/portal_views.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Watch for AWS API deprecations; verify credentials/region handling and retry behavior. |
| django-storages | Django storage backends (S3). | **UNKNOWN**: no direct imports found via `rg -n "storages" src/config src/modules`. | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm storage backend settings; verify S3 uploads/downloads in staging after upgrades. |
| stripe | Stripe payments SDK. | Payments and webhooks (`src/modules/finance/services.py`, `src/api/finance/webhooks.py`, `src/modules/finance/reconciliation.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Review Stripe API version changes; re-test webhook signature verification and payment flows. |
| python-dotenv | Load environment variables from `.env`. | Django entrypoint (`src/manage.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Ensure environment loading order stays consistent; check for deprecations in dotenv API. |
| Pillow | Image processing (watermarking). | Document watermarking (`src/modules/core/access_controls.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Validate native dependencies and image output quality; consider security patches. |
| requests | HTTP client. | CRM enrichment and DocuSign integrations (`src/modules/crm/enrichment_service.py`, `src/modules/esignature/docusign_service.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm TLS/timeout defaults; handle retry behavior explicitly if upgrading. |
| icalendar | iCal parsing/generation. | Calendar feeds (`src/modules/calendar/ical_service.py`, `src/modules/calendar/test_avail_1.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Verify timezone/DST handling; re-run calendar availability checks. |
| gunicorn | WSGI server for production. | **UNKNOWN**: no direct references found via `rg -n "gunicorn" -g '*.md' -g 'Dockerfile' -g '*.py'`. | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm worker settings and health endpoints in deployment docs before upgrade. |
| python-json-logger | JSON log formatting. | Logging config (`src/config/settings.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Validate log schema and ingestion pipeline after upgrades. |
| sentry-sdk | Error tracking and performance monitoring. | Sentry setup (`src/config/sentry.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm DSN config, sampling rates, and tracing integrations remain compatible. |
| bcrypt | Password hashing for document shares. | Document sharing models (`src/modules/documents/models/shares.py`, `src/modules/documents/models/locks.py`). | **UNKNOWN** (no alternatives evaluated in-repo). | Re-test hash verification; watch for platform-specific build issues. |

## Development dependencies (`requirements-dev.txt`)

| Dependency | Purpose | Usage in repo | Alternatives | Upgrade considerations |
| --- | --- | --- | --- | --- |
| black | Python code formatter. | Config in `pyproject.toml` (`[tool.black]`). | **UNKNOWN** (no alternatives evaluated in-repo). | Align with ruff/isort rules; reformatting can be large—use in focused changes. |
| ruff | Python linting/formatting. | Config in `pyproject.toml` (`[tool.ruff]`). | **UNKNOWN** (no alternatives evaluated in-repo). | Validate rule set changes; update ignores if new rules surface. |
| import-linter | Architectural boundary enforcement. | Config in `.importlinter`; referenced in `docs/BOUNDARY_RULES.md`. | **UNKNOWN** (no alternatives evaluated in-repo). | Re-run boundary checks after upgrades; confirm contract syntax compatibility. |
| pytest | Test runner. | Config in `pytest.ini`. | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm plugin compatibility; re-run full test suite after upgrades. |
| pytest-django | Django test integration. | Config relies on `DJANGO_SETTINGS_MODULE` in `pytest.ini`. | **UNKNOWN** (no alternatives evaluated in-repo). | Ensure Django version compatibility; validate database reuse settings. |
| pytest-cov | Coverage reporting for pytest. | Coverage flags configured in `pytest.ini`. | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm coverage output paths and thresholds after upgrades. |
| coverage | Coverage library (used by pytest-cov). | Coverage flags configured in `pytest.ini`. | **UNKNOWN** (no alternatives evaluated in-repo). | Keep in sync with pytest-cov expectations; validate XML/HTML output. |
| factory-boy | Test factories. | **UNKNOWN**: no direct imports found via `rg -n "factory_boy|Factory" tests src`. | **UNKNOWN** (no alternatives evaluated in-repo). | If unused, consider removal (see TODO T-031). |
| faker | Fake data generation. | **UNKNOWN**: no direct imports found via `rg -n "faker|Faker" tests src`. | **UNKNOWN** (no alternatives evaluated in-repo). | If unused, consider removal (see TODO T-031). |
| safety | Dependency vulnerability scanning. | **UNKNOWN**: no local config found via `rg -n "safety" -g '*.toml' -g '*.ini'`. | **UNKNOWN** (no alternatives evaluated in-repo). | Confirm intended usage in local scripts/CI before upgrading. |
| bandit | Static security analysis. | **UNKNOWN**: no local config found via `rg -n "bandit" -g '*.toml' -g '*.ini'`. | **UNKNOWN** (no alternatives evaluated in-repo). | Verify baseline ignores and target paths; re-run scans after upgrades. |
| mypy | Static type checking. | **UNKNOWN**: no config found via `rg -n "mypy" -g '*.toml' -g '*.ini'`. | **UNKNOWN** (no alternatives evaluated in-repo). | Add/verify config before enabling in CI; check Django stubs compatibility. |
| django-stubs | Type hints for Django. | **UNKNOWN**: no config found via `rg -n "django-stubs" -g '*.toml' -g '*.ini'`. | **UNKNOWN** (no alternatives evaluated in-repo). | Keep aligned with Django/mypy versions; enable when type checking is enforced. |

## Upgrade workflow (recommended)
1. Update the version pin in `requirements.txt` or `requirements-dev.txt`.
2. Re-run `pip install -r requirements.txt -r requirements-dev.txt` in a clean virtualenv.
3. Run tests (`pytest`) and any module-specific verification.
4. Update this document with any new caveats or behavior changes.
