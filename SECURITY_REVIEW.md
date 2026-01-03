# SECURITY REVIEW

Precedence: CODEBASECONSTITUTION.md → READMEAI.md → specs/* → this document.

Purpose: maintain a practical security baseline for an AI-built codebase without requiring scripts, scanners, or CI. This is a repeatable review checklist that produces concrete TODO.md tasks when gaps exist.

What this is:

* A lightweight, recurring security checklist focused on the most common real-world failures.

What this is not:

* A formal pen test
* A compliance certification
* A replacement for professional review on high-stakes systems

Primary outputs:

* Security findings converted into TODO.md tasks (Type: QUALITY or COMPLETE or ENHANCE with SEC category)
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
* When you find a gap, create a concrete task in TODO.md:

  * Priority: P0 for critical exploitable issues; P1 for high-risk; P2 for hardening
  * Type: QUALITY if refactor/cleanup; COMPLETE if required behavior is missing; ENHANCE if hardening
  * Include acceptance criteria and file references.

Deliverables:

1. A “Security Review Summary” section appended to the bottom of this file (date + results).
2. TODO.md updates for all findings (no exceptions).
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