# SECURITY.md

Last Updated: 2026-01-02

## Supported versions
This repository is a template framework. When used in a real project, define supported release lines here.

## Reporting a vulnerability
If this repo is deployed/used in production, define a private reporting channel (email or ticket system) and response SLA.

## Security principles (baseline)
- Never commit secrets. Use environment variables, `.env` (gitignored), or a secret manager.
- Least privilege for credentials and tokens.
- Prefer dependency pinning and automated updates in CI.
- Treat AI-generated code as untrusted until verified (tests + review).

## Quick checks
- Run: `make ci`
- Review: `docs/SECURITY_BASELINE.md`

## Tenant isolation (RLS)
- PostgreSQL row-level security is enabled for firm-scoped tables. See `docs/SECURITY_RLS.md` for the table inventory and session-handling rules (`app.current_firm_id` via middleware/background jobs).
- Assumptions: PostgreSQL is the primary database engine; RLS policies rely on `app.current_firm_id` being set by `FirmRLSSessionMiddleware` for HTTP requests and `firm_db_session(firm)` for background jobs/management commands.
- Limitations: Policies are enforced only on PostgreSQL; SQLite test runs skip RLS assertions. Any new tenant-scoped model must include a `firm` FK so the migration policy sweep can apply.
- Debugging steps:
  - Confirm the session variable is set: `SELECT current_setting('app.current_firm_id', true);`
  - Verify policies exist/enabled: `SELECT * FROM pg_policies WHERE polname LIKE '%_firm_rls';`
  - If policies reject access, ensure middleware order keeps `FirmRLSSessionMiddleware` after firm resolution and that background tasks wrap DB work in `firm_db_session(firm)`.
