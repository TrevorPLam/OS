# SECURITY REVIEW

Precedence: CODEBASECONSTITUTION.md → READMEAI.md → specs/* → this document.

Purpose: maintain a practical security baseline for an AI-built codebase without requiring scripts, scanners, or CI. This is a repeatable review checklist that produces concrete P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md tasks when gaps exist.

What this is:

* A lightweight, recurring security checklist focused on the most common real-world failures.

What this is not:

* A formal pen test
* A compliance certification
* A replacement for professional review on high-stakes systems

Primary outputs:

* Security findings converted into P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md tasks (Type: QUALITY or COMPLETE or ENHANCE with SEC category)
* Optional updates to DECISIONS.md when security tradeoffs are chosen
* Optional updates to docs if behavior/requirements change

Hard rule:

* No security findings stay buried in docs or code comments. They become tasks with acceptance criteria.
---

## AGENT EXECUTION PROMPT (RUN THIS EXACTLY)

You are a security review agent operating inside this repository.

Constraints:

* Assume the repo owner does not run scripts and does not use GitHub Actions.
* Prefer review methods that can be done by reading code/config and using the deployed preview (if available).
* When you find a gap, create a concrete task in P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md:

  * Priority: P0 for critical exploitable issues; P1 for high-risk; P2 for hardening
  * Type: QUALITY if refactor/cleanup; COMPLETE if required behavior is missing; ENHANCE if hardening
  * Include acceptance criteria and file references.

Deliverables:

1. A “Security Review Summary” section appended to the bottom of this file (date + results).
2. P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md updates for all findings (no exceptions).
3. If applicable, updates to env.example to document required env vars safely (placeholders only).

⠀
Stop conditions:

* If you identify a likely secret committed to the repo, treat as P0 and prioritize remediation steps immediately (rotate key, remove secret, document).
---

## Severity Rules (Use These)

P0 (Critical):

* secrets committed or exposed
* auth bypass or missing authorization checks
* payment or sensitive data integrity failure
* arbitrary code execution / injection vectors
* IDOR (insecure direct object reference) on sensitive objects

P1 (High):

* weak session handling, missing CSRF protections where needed
* overly verbose error messages leaking internals
* missing rate limits on sensitive endpoints
* unsafe file upload handling
* missing input validation on key fields

P2 (Hardening):

* security headers, best-practice defaults
* dependency hygiene improvements
* logging redaction improvements
* least privilege improvements
* improved audit trails
---

## Phase 1 — Secrets & Sensitive Data (Most Important)

1. Confirm no secrets are stored in repo

2. Check common locations:

⠀
* .env, .env.*, env.example
* README*, docs, config files
* code constants, “API_KEY=”
* JSON credentials, private keys, PEM files

If any real secret is found:

* Create P0 tasks:

  * rotate/revoke the secret
  * remove it from history if necessary
  * replace with env var references
  * update env.example with placeholder

1. Logging safety

2. Check for logs that might leak:

⠀
* tokens, cookies, auth headers
* full request bodies containing PII
* payment details

Task rule:

* Add a task to redact or avoid logging sensitive fields.

Acceptance criteria examples:

* “No logs include Authorization headers or session tokens”
* “PII fields are masked/redacted in logs”
---

## Phase 2 — Authentication & Authorization

1. Authentication present and consistent (if app uses auth)

⠀
* Is there a single auth mechanism (not multiple half-implemented ones)?
* Are session/token lifetimes defined?
* Is logout implemented correctly?

1. Authorization (most common failure)

2. For any data access or mutation:

⠀
* Confirm there is an authorization check:

  * tenant isolation (if multi-tenant)
  * role permissions (admin/user)
  * ownership checks (“can this user access this object?”)

Look specifically for IDOR:

* routes like /resource/:id without checking ownership/tenant

If missing:

* P0 tasks with explicit acceptance criteria:

  * “User cannot access objects outside their tenant even with direct ID guessing”
  * “Server enforces access; UI-only checks not relied upon”

1. CSRF (if cookies + state-changing requests)

⠀
* If using cookie-based auth:

  * confirm CSRF protections exist or architecture avoids CSRF risk (e.g., same-site strict + token)
* If unclear, create a P1 task to document and enforce.
---

## Phase 3 — Input Validation & Injection Risks

1. Validate all external inputs

2. Targets:

⠀
* form inputs
* query params
* JSON payloads
* webhook payloads
* file uploads
* redirects/URLs

1. Injection vectors checklist

⠀
* SQL injection (if raw queries exist)
* command injection (shell execution)
* XSS (rendering user-controlled HTML)
* SSRF (server fetching user-provided URLs)
* open redirect (redirect URL is user-controlled)

If any “direct string concatenation” to queries/commands/HTML is found:

* Create P0/P1 tasks depending on exploitability.

Acceptance criteria examples:

* “All API routes validate request schema before processing”
* “User input is escaped/encoded when rendered”
* “Server-side fetch only allows allowlisted domains”
---

## Phase 4 — External Integrations (Stripe, OAuth, Webhooks, etc.)

1. Webhooks

⠀
* Verify signature validation exists (Stripe webhook signature, etc.)
* Ensure idempotency (duplicate webhook events don’t double-apply effects)
* Ensure webhook handler does not log sensitive payloads

1. OAuth / third-party tokens

⠀
* Tokens stored securely (server-side, not in client localStorage unless architecture demands)
* Refresh token handling documented
* Scopes minimized

1. Payment safety (if applicable)

⠀
* Never store card numbers/CVV
* Use provider tokens
* Confirm “double charge” prevention (idempotency keys / dedupe)

Missing signature validation or idempotency in payments/webhooks is typically P0.

---

## Phase 5 — Data Protection & Privacy Basics

1. Identify sensitive data categories used in app

⠀
* PII (name, email, phone)
* financial data
* credentials/tokens
* business confidential data

1. Storage rules

⠀
* Sensitive data should not be stored unnecessarily
* If stored, encryption-at-rest depends on platform; document assumptions
* Access should be least privilege

1. Client-side storage

⠀
* Avoid storing tokens in localStorage when possible
* Avoid storing sensitive user data in the browser persistently

1. Data retention

⠀
* If you keep logs or user data, document retention defaults
* If not decided, create a P2 hardening task to define retention
---

## Phase 6 — Dependency & Supply Chain Hygiene (No tools required)

1. Quick dependency sanity

2. By inspection:

⠀
* Are there obviously abandoned libs?
* Are there “random” one-off deps used for trivial tasks?
* Are there duplicate libs (two date libs, etc.)?

1. Pinning policy

⠀
* Lockfile present
* Avoid “latest” without reason

Create P2 tasks:

* reduce dependency sprawl
* replace questionable deps
* document update cadence in DEPENDENCY_HEALTH.md (if present)
---

## Phase 7 — Deployment & Runtime Hardening (Doc-only)

Even without configuring headers/infra today, document what “good” looks like.

Checklist:

* HTTPS only (platform default typically)
* security headers (CSP, HSTS, X-Frame-Options, etc.) where feasible
* error pages don’t leak stack traces
* environment separation (dev/staging/prod)

If lacking:

* Create P2 tasks (or P1 if real leakage exists).
---

## Required Output: Security Review Summary (Append Below)

When you complete a review, append:

## Security Review Summary — YYYY-MM-DD

## Scope reviewed:

Top findings:

* (P0) …
* (P1) …
* (P2) …

* Tasks created:
* T-### …

* Notes / assumptions:
---

## Security Review Summary — 2026-01-03

### Scope reviewed:
- Complete codebase review covering:
  - Backend Python/Django code (src/modules, src/api, src/config)
  - Frontend React/TypeScript code (src/frontend)
  - Configuration files (.env.example, settings.py)
  - Dependencies (requirements.txt, package.json)
  - All 7 security review phases per SECURITY_REVIEW.md

### Top findings:

#### P0 (Critical) - None Found ✅
- No hardcoded secrets detected in repository
- No authentication bypass vulnerabilities
- No payment integrity failures identified
- No injection vectors discovered

#### P1 (High) - 2 Findings
* **(P1) Missing webhook idempotency handling** - Webhook endpoints (Stripe, DocuSign, Square, SMS) process events but lack explicit idempotency key tracking to prevent duplicate processing if webhooks are retried.
* **(P1) Missing rate limiting on webhook endpoints** - While auth endpoints have rate limiting, webhook endpoints (Stripe, Square, DocuSign, SMS) lack rate limiting which could allow webhook flooding attacks.

#### P2 (Hardening) - 3 Findings
* **(P2) No explicit data retention policy documented** - While GDPR features exist (CRM-INT-4 in P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md), there's no explicit retention policy for logs, webhook events, or user data.
* **(P2) Missing Content-Security-Policy header** - While other security headers are configured (HSTS, XSS Filter, etc.), CSP header is not explicitly set.
* **(P2) Frontend dependency versions not pinned** - package.json uses caret (^) versions which could introduce unexpected updates. Backend uses pinned versions correctly.

### Tasks created:
* **SEC-1** (P1): Implement webhook idempotency tracking (Priority: P1, Type: QUALITY, Category: SEC)
* **SEC-2** (P1): Add rate limiting to webhook endpoints (Priority: P1, Type: QUALITY, Category: SEC)
* **SEC-3** (P2): Document and implement data retention policies (Priority: P2, Type: COMPLETE, Category: SEC)
* **SEC-4** (P2): Add Content-Security-Policy header configuration (Priority: P2, Type: ENHANCE, Category: SEC)
* **SEC-5** (P2): Pin frontend dependency versions (Priority: P2, Type: QUALITY, Category: SEC)

### Notes / assumptions:

**Strengths identified:**
1. ✅ No secrets committed to repository - all sensitive values use environment variables
2. ✅ Strong authentication with JWT tokens (1hr access, 7 day refresh with rotation)
3. ✅ Comprehensive authorization via FirmScopedMixin enforces tenant isolation
4. ✅ CSRF protection properly implemented (exempt only for signature-verified webhooks)
5. ✅ Strong password requirements (12 char minimum, complexity validators)
6. ✅ Rate limiting on auth endpoints (django-ratelimit on MFA: 3/h, login: 5/h)
7. ✅ Webhook signature verification for Stripe, Square, DocuSign, Twilio
8. ✅ Production security headers configured (HSTS, XSS Filter, Content-Type Nosniff, SSL Redirect)
9. ✅ No dangerouslySetInnerHTML usage found in React frontend
10. ✅ Django ORM used throughout - no raw SQL string concatenation
11. ✅ Error handling doesn't leak stack traces in production
12. ✅ Sentry integration for error tracking and monitoring
13. ✅ MFA support implemented (django-otp with QR codes)
14. ✅ SAML and OAuth support for enterprise SSO

**Assumptions:**
- Repository owner does not run CI/CD pipelines (per SECURITY_REVIEW.md constraints)
- Django DEBUG=False in production (default per settings.py)
- Database encryption-at-rest handled by platform (PostgreSQL on managed service)
- HTTPS enforced by platform/reverse proxy (SECURE_SSL_REDIRECT=True when DEBUG=False)
- Dependencies are updated regularly via manual review (no automated scanning available)

**Items explicitly not in scope:**
- Infrastructure configuration (AWS, database, networking) - platform responsibility
- Third-party service security (Stripe, DocuSign, AWS) - vendor responsibility
- Penetration testing or active vulnerability scanning
- Compliance certifications (SOC 2, ISO 27001, etc.)

**Follow-up recommendations:**
1. Consider implementing AWS_SECRET_SCANNER or similar in pre-commit hooks
2. Consider adding SECURITY.txt file per RFC 9116
3. Monitor OWASP dependency check results for Python and npm packages
4. Review and update security headers annually as browser standards evolve

---

## Security Review Summary — 2026-01-08

### Scope reviewed:
- Webhook handlers and signature validation
- Frontend auth token storage
- Environment configuration templates

### Top findings:

#### P0 (Critical) - None Found ✅

#### P1 (High) - 2 Findings
* **(P1) Webhook signature checks can be bypassed when secrets are unset** — DocuSign and Twilio webhook handlers accept unsigned requests if secrets are missing, which makes endpoints vulnerable if misconfigured.
* **(P1) Auth tokens stored in localStorage** — JWT tokens are persisted in localStorage, which exposes them to XSS-based theft.

#### P2 (Hardening) - None

### Tasks created:
* **SEC-6** (P1): Require DocuSign + Twilio webhook signature verification even when secrets are missing.
* **SEC-7** (P1): Move auth tokens from localStorage to HttpOnly cookies.

### Notes / assumptions:
- Webhook endpoints are publicly reachable in production.
- Current CSP reduces XSS risk but does not eliminate it; token storage should still be hardened.
- Stripe and Square webhooks already fail closed when signature secrets are missing.

---
