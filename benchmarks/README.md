# Benchmarks — Locust Load Tests

Document Type: Reference
Last Updated: 2026-01-16

## Purpose
Provide repeatable Locust scenarios for API performance baselines (auth, CRUD, list, search).

## Quick start
1) Install dev dependencies (includes Locust):
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2) Run Locust with defaults:
   ```bash
   make benchmark
   ```

## Required configuration
Locust needs a running API. Configure the host and test data via environment variables.

| Variable | Purpose | Example |
| --- | --- | --- |
| `LOCUST_HOST` | Base host for the API | `http://localhost:8000` |
| `LOCUST_USERNAME` | Username for auth login | `demo@example.com` |
| `LOCUST_PASSWORD` | Password for auth login | `SecurePass123!` |
| `LOCUST_FIRM_ID` | Firm ID used for CRM CRUD payloads | `f1f3a3b1-...` |
| `LOCUST_LEAD_ID` | Existing Lead ID for update/delete | `3c0a7a9f-...` |
| `LOCUST_SEARCH_QUERY` | Search query for list/search benchmarks | `acme` |

### Optional overrides
You can override endpoint paths if your deployment differs:

| Variable | Default | Notes |
| --- | --- | --- |
| `LOCUST_API_PREFIX` | `/api/v1` | Shared API prefix. |
| `LOCUST_AUTH_LOGIN_PATH` | `/api/v1/auth/login/` | Auth login endpoint. |
| `LOCUST_CRM_LEADS_PATH` | `/api/v1/crm/leads/` | CRM lead list/create endpoint. |

## Notes
- CRUD benchmarks skip create/update/delete if required IDs are missing.
- Auth benchmarking runs independently so you can isolate login performance.
- Adjust users, spawn rate, and duration via `LOCUST_ARGS` in the `make benchmark` command.
