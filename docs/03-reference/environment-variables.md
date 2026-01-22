# Environment Variables Reference

Document Type: Reference
Last Updated: 2026-01-24

This document lists all environment variables used by ConsultantPro, their purpose, and configuration requirements.

**Why this structure:** Variables are grouped by subsystem so operators can quickly locate what a change impacts. Evidence references point to the exact code or templates that consume each variable for auditability.

## Evidence policy

Each variable includes an evidence reference to the file(s) that read or define it. If you add a new variable, update `.env.example` and the relevant config module, then extend this list.

## Core Django Settings

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | Yes | None | Django cryptographic signing key. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `DJANGO_DEBUG` | No | `False` | Enables Django debug mode. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `DJANGO_ALLOWED_HOSTS` | Yes (production) | `localhost,127.0.0.1` | Allowed hostnames for Django. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `E2E_PROVISION_TOKEN` | No | None | Enables debug-only provisioning endpoint for E2E tests. | `src/config/settings.py` |
| `CI` | No | None | Skips environment validation when set to `true`. | `src/config/env_validator.py` |
| `USE_SQLITE_FOR_TESTS` | No | None | Forces SQLite for tests/local dev when set to `True`. | `src/config/settings.py` |

## Database Configuration

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `POSTGRES_DB` | Yes | `consultantpro` | PostgreSQL database name. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `POSTGRES_USER` | Yes | `postgres` | PostgreSQL username. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `POSTGRES_PASSWORD` | Yes | `postgres` | PostgreSQL password. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `POSTGRES_HOST` | Yes | `db` | PostgreSQL host. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port. | `.env.example`, `src/config/settings.py` |
| `DB_STATEMENT_TIMEOUT_MS` | No | `5000` | PostgreSQL statement timeout in milliseconds. | `src/config/database.py` |
| `DB_SLOW_QUERY_THRESHOLD_MS` | No | `100` | Threshold (ms) for slow query logging. | `src/config/database.py` |

## CORS & CSRF Configuration

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `CORS_ALLOWED_ORIGINS` | Yes (if frontend separate) | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173` | Allowed CORS origins. | `.env.example`, `src/config/settings.py` |
| `CSRF_TRUSTED_ORIGINS` | No | `CORS_ALLOWED_ORIGINS` | Explicit CSRF trusted origins override. | `src/config/settings.py` |

## Tracking Pipeline

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `TRACKING_PUBLIC_KEY` | No | None | Shared key for backend ingestion and frontend snippet. | `src/config/settings.py`, `README.md` |
| `TRACKING_INGEST_ENABLED` | No | `True` | Enable/disable tracking ingest endpoint. | `src/config/settings.py`, `README.md` |
| `TRACKING_INGEST_RATE_LIMIT_PER_MINUTE` | No | `300` | Tracking ingest rate limit per minute. | `src/config/settings.py`, `README.md` |
| `TRACKING_MAX_PROPERTIES_BYTES` | No | `16384` | Max JSON properties size for tracking payloads. | `src/config/settings.py`, `README.md` |

## Auth Cookie Settings

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `AUTH_COOKIE_SAMESITE` | No | `Lax` | SameSite value for auth cookies. | `src/config/settings.py` |
| `AUTH_COOKIE_DOMAIN` | No | None | Domain for auth cookies. | `src/config/settings.py` |
| `AUTH_COOKIE_PATH` | No | `/api/` | Path for auth cookies. | `src/config/settings.py` |
| `ACCESS_TOKEN_COOKIE_NAME` | No | `cp_access_token` | Cookie name for access token. | `src/config/settings.py` |
| `REFRESH_TOKEN_COOKIE_NAME` | No | `cp_refresh_token` | Cookie name for refresh token. | `src/config/settings.py` |
| `SESSION_COOKIE_SAMESITE` | No | `AUTH_COOKIE_SAMESITE` | SameSite for session cookies. | `src/config/settings.py` |
| `CSRF_COOKIE_SAMESITE` | No | `AUTH_COOKIE_SAMESITE` | SameSite for CSRF cookies. | `src/config/settings.py` |

## AWS S3 Storage

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `AWS_ACCESS_KEY_ID` | Yes (when using S3) | None | AWS access key for S3. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `AWS_SECRET_ACCESS_KEY` | Yes (when using S3) | None | AWS secret key for S3. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `AWS_STORAGE_BUCKET_NAME` | Yes (when using S3) | None | S3 bucket for documents. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `AWS_S3_REGION_NAME` | No | `us-east-1` | AWS region for S3 bucket. | `.env.example`, `src/config/settings.py` |

## KMS / Encryption

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `DEFAULT_FIRM_KMS_KEY_ID` | No | None | Default KMS key ID for firm encryption. | `.env.example`, `src/config/settings.py` |
| `KMS_BACKEND` | No | None | KMS backend selector (e.g., AWS). | `.env.example`, `src/config/settings.py` |

## Payment Processing (Stripe)

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `STRIPE_SECRET_KEY` | Yes (when Stripe enabled) | None | Stripe API secret key. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `STRIPE_PUBLISHABLE_KEY` | Yes (when Stripe enabled) | None | Stripe publishable key for frontend. | `.env.example`, `src/config/settings.py` |
| `STRIPE_WEBHOOK_SECRET` | Yes (when Stripe webhooks enabled) | None | Webhook signature secret. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |

## OAuth Providers

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `GOOGLE_OAUTH_CLIENT_ID` | No | None | Google OAuth client ID. | `src/config/settings.py` |
| `GOOGLE_OAUTH_CLIENT_SECRET` | No | None | Google OAuth client secret. | `src/config/settings.py` |
| `MICROSOFT_OAUTH_CLIENT_ID` | No | None | Microsoft OAuth client ID. | `src/config/settings.py` |
| `MICROSOFT_OAUTH_CLIENT_SECRET` | No | None | Microsoft OAuth client secret. | `src/config/settings.py` |

## SAML Configuration

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `SAML_ENABLED` | No | `False` | Enable SAML auth flow. | `src/config/settings.py` |
| `SAML_IDP_METADATA_URL` | No | None | IdP metadata URL. | `src/config/settings.py` |
| `SAML_SP_ENTITY_ID` | No | None | Service provider entity ID. | `src/config/settings.py` |
| `SAML_SP_PUBLIC_CERT` | No | None | SP public certificate. | `src/config/settings.py` |
| `SAML_SP_PRIVATE_KEY` | No | None | SP private key. | `src/config/settings.py` |

## DocuSign E-Signature Integration

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `DOCUSIGN_CLIENT_ID` | Yes (when DocuSign enabled) | None | DocuSign OAuth client ID. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `DOCUSIGN_CLIENT_SECRET` | Yes (when DocuSign enabled) | None | DocuSign OAuth client secret. | `.env.example`, `src/config/settings.py` |
| `DOCUSIGN_REDIRECT_URI` | Yes (when DocuSign enabled) | None | OAuth callback URL. | `.env.example`, `src/config/settings.py` |
| `DOCUSIGN_WEBHOOK_SECRET` | Yes (when DocuSign webhooks enabled) | None | Webhook signature secret. | `.env.example`, `src/config/settings.py`, `src/config/env_validator.py` |
| `DOCUSIGN_ENVIRONMENT` | No | `production` | DocuSign API environment. | `.env.example`, `src/config/settings.py` |

## Twilio SMS Integration

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `TWILIO_ACCOUNT_SID` | Yes (when Twilio enabled) | None | Twilio account SID. | `.env.example`, `src/config/env_validator.py` |
| `TWILIO_AUTH_TOKEN` | Yes (when Twilio enabled) | None | Twilio auth token. | `.env.example`, `src/config/env_validator.py` |

## Sentry Error Tracking

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `SENTRY_DSN` | No | None | Sentry DSN for error reporting. | `.env.example`, `src/config/sentry.py` |
| `SENTRY_ENVIRONMENT` | No | `production` | Sentry environment name. | `.env.example`, `src/config/sentry.py` |
| `SENTRY_TRACES_SAMPLE_RATE` | No | `0.1` | Sentry tracing sample rate. | `.env.example`, `src/config/sentry.py` |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | `0.1` | Sentry profiling sample rate. | `.env.example`, `src/config/sentry.py` |
| `SENTRY_DEBUG` | No | `False` | Enable Sentry debug logging. | `.env.example`, `src/config/sentry.py` |
| `GIT_COMMIT_SHA` | No | None | Release identifier for Sentry. | `.env.example`, `src/config/sentry.py` |

## Webhook Rate Limiting

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `WEBHOOK_RATE_LIMIT` | No | `100/m` | Default webhook rate limit. | `.env.example`, `src/config/settings.py` |
| `STRIPE_WEBHOOK_RATE_LIMIT` | No | `WEBHOOK_RATE_LIMIT` | Stripe webhook rate limit override. | `src/config/settings.py` |
| `SQUARE_WEBHOOK_RATE_LIMIT` | No | `WEBHOOK_RATE_LIMIT` | Square webhook rate limit override. | `src/config/settings.py` |
| `DOCUSIGN_WEBHOOK_RATE_LIMIT` | No | `WEBHOOK_RATE_LIMIT` | DocuSign webhook rate limit override. | `src/config/settings.py` |
| `TWILIO_STATUS_WEBHOOK_RATE_LIMIT` | No | `WEBHOOK_RATE_LIMIT` | Twilio status webhook rate limit override. | `src/config/settings.py` |
| `TWILIO_INBOUND_WEBHOOK_RATE_LIMIT` | No | `WEBHOOK_RATE_LIMIT` | Twilio inbound webhook rate limit override. | `src/config/settings.py` |

## Data Retention

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `WEBHOOK_RETENTION_DAYS` | No | `180` | Webhook event retention window (days). | `.env.example`, `src/config/settings.py` |
| `LOG_RETENTION_DAYS` | No | `90` | Application log retention window (days). | `.env.example`, `src/config/settings.py` |
| `AUDIT_LOG_ARCHIVE_DAYS` | No | `365` | Audit log archive threshold (days). | `.env.example`, `src/config/settings.py` |
| `ENABLE_AUTOMATED_CLEANUP` | No | `true` | Toggle automated cleanup jobs. | `.env.example`, `src/config/settings.py` |

## Content Security Policy

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `CSP_REPORT_URI` | No | `/api/security/csp-report/` | Endpoint for CSP violation reports. | `.env.example`, `src/config/settings.py` |

## Fixture Seeding (Local Dev)

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `FIXTURE_USER_PASSWORD` | No | `fixture-password` | Overrides default password for `load_fixtures`. | `src/modules/core/management/commands/load_fixtures.py` |

## Frontend (Vite)

| Variable | Required | Default | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| `VITE_API_URL` | No | `http://localhost:8000/api` | Base API URL for frontend requests. | `src/frontend/src/api/client.ts` |
| `VITE_API_BASE_URL` | No | `http://localhost:8000/api/v1` | Base API URL for automation API client. | `src/frontend/src/api/automation.ts` |
| `VITE_SENTRY_DSN` | No | None | Enable Sentry in the frontend. | `src/frontend/src/main.tsx` |
| `VITE_SENTRY_TRACES_SAMPLE_RATE` | No | `0` | Frontend Sentry tracing sample rate. | `src/frontend/src/main.tsx` |
| `VITE_TRACKING_KEY` | No | None | Tracking snippet public key. | `src/frontend/src/main.tsx` |
| `VITE_TRACKING_FIRM_SLUG` | No | None | Firm slug for tracking events. | `src/frontend/src/main.tsx` |
| `VITE_TRACKING_ENDPOINT` | No | `/api/v1/tracking/collect/` | Tracking endpoint override. | `src/frontend/src/main.tsx` |

## See Also
- `.env.example` - Example environment file
- `src/config/env_validator.py` - Startup validation rules
- `src/config/settings.py` - Django settings
- `docs/03-reference/management-commands.md` - Management commands reference
