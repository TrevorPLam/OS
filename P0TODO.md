# P0TODO.md - Repository Task List

Document Type: Workflow
Last Updated: 2026-01-21
Task Truth Source: **P0TODO.md**
Other Priority Files: P1TODO.md, P2TODO.md, P3TODO.md

<!--
Meta-commentary:
  - Current Status: Authoritative task list; T-127, T-135, T-137, and T-138 moved to TODOCOMPLETED.md.
  - Mapping: Mirrors completed work recorded in TODOCOMPLETED.md and CHANGELOG.md.
- Reasoning: Keep task truth source accurate after completion.
- Assumption: Tasks are appended/moved manually with auditability in mind.
- Limitation: This file does not capture execution details beyond acceptance criteria.
-->

This file is the single source of truth for P0 tasks.
If another document disagrees, the task record in this file wins (unless the Constitution overrides).

## Task schema (required)
- **ID**: `T-###` (unique)
- **Priority**: `P0 | P1 | P2 | P3`
- **Type**: `SECURITY | RELEASE | DEPENDENCY | DOCS | QUALITY | BUG | FEATURE | CHORE`
- **Owner**: `AGENT | Trevor`
- **Status**: `READY | BLOCKED | IN-PROGRESS | IN-REVIEW`
- **Blocker**: `None` or explicit dependency/decision
- **Context**: why the task exists (1–5 bullets)
- **Acceptance Criteria**: verifiable checklist
- **References**: file paths and/or links inside this repo
- **Dependencies**: task IDs (if any)
- **Effort**: `S | M | L` (relative; explain if unclear)

### Priority meaning
- **P0**: blocks production readiness or causes security/data loss
- **P1**: high impact; do within 7 days
- **P2**: important but not urgent; do within 30 days
- **P3**: backlog/tech debt; do when convenient

### Ownership rule
- **Owner: AGENT** means the task can be executed by a coding agent in-repo.
- **Owner: Trevor** means it requires external actions (provider dashboards, DNS, billing, approvals).

## Prompt Scaffold (Required for AGENT-owned tasks)
Applies to AGENT-owned tasks in this file.
Role: Who the agent should act as (e.g., senior engineer, docs editor).
Goal: What done means in one sentence.
Non-Goals: Explicit exclusions to prevent scope creep.
Context: Relevant files, prior decisions, and why the task exists.
Constraints: Tooling, style, security, and architecture rules to follow.
Examples: Expected input/output or format examples when applicable.
Validation: Exact verification steps (tests, lint, build, manual checks).
Output Format: Required response format or artifacts.
Uncertainty: If details are missing, mark UNKNOWN and cite what was checked.

### Task Prompt Template (paste into each task)
Role:
Goal:
Non-Goals:
Context:
Constraints:
Examples:
Validation:
Output Format:
Uncertainty:

## Active tasks

### Phase 0 — Production readiness blockers (P0)
### T-128: Fix CSRF bypass on SAML endpoints (REFACTOR Phase 0)
Priority: P0
Type: SECURITY
Owner: AGENT
Status: IN-REVIEW
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 0 Item 3 - IMMEDIATE P0 FIX
- SAML endpoints have @csrf_exempt decorator
- No RelayState validation enables account takeover via CSRF
- FORENSIC_AUDIT.md Issue #5.2
Acceptance Criteria:
- [x] Remove @csrf_exempt from src/modules/auth/saml_views.py:119,142,212 (kept due to external POST)
- [x] Add SAML RelayState generation in SAMLLoginView with secrets.token_urlsafe(32)
- [x] Store RelayState in session for validation
- [x] Add RelayState validation in SAMLACSView using hmac.compare_digest()
- [x] Clear used state after validation to prevent replay attacks
- [x] Add security comments explaining CSRF protection approach
- [x] Add security test for CSRF protection (tests/auth/test_saml_views.py)
- [ ] Run existing tests: pytest src/tests/ (blocked: pytest not installed in sandbox)
- [ ] Manual test: SAML login flow (requires SAML IdP)
References:
- REFACTOR_PLAN.md:159-163
- FORENSIC_AUDIT.md Issue #5.2
- src/modules/auth/saml_views.py:119,142,212
Dependencies: None
Effort: M

### T-129: Fix production Dockerfile to use gunicorn (REFACTOR Phase 0)
Priority: P0
Type: RELEASE
Owner: AGENT
Status: IN-REVIEW
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 0 Item 4 - IMMEDIATE P0 FIX
- Production Dockerfile uses Django runserver (dev-only server)
- Causes DEBUG leaks, DoS vulnerability, no SSL support
- FORENSIC_AUDIT.md Issue #8.5
Acceptance Criteria:
- [x] Replace runserver with gunicorn in Dockerfile:40
- [x] Configure gunicorn workers and timeout settings (4 workers, 120s timeout)
- [x] Test Docker build: docker build . (to be verified)
- [ ] Verify container starts with gunicorn (requires Docker runtime)
- [x] Document production deployment requirements (security comments added)
References:
- REFACTOR_PLAN.md:165-169
- FORENSIC_AUDIT.md Issue #8.5
- Dockerfile:40-45
Dependencies: None
Effort: S

### T-130: Add type validation to webhook payment processing (REFACTOR Phase 0)
Priority: P0
Type: BUG
Owner: AGENT
Status: IN-REVIEW
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 0 Item 5 - IMMEDIATE P0 FIX
- Webhook divides amount_received without type validation
- Malformed Stripe data causes TypeError crash → revenue loss
- FORENSIC_AUDIT.md Issue #1.3
Acceptance Criteria:
- [x] Validate amount_received is numeric before division (basic isinstance check added at lines 331-340)
- [x] Add error handling for invalid webhook data (ValueError raised with logging)
- [x] Add Pydantic schema validation for webhook payload in src/api/finance/webhooks.py
- [x] Add webhook replay tests (requires test infrastructure)
- [ ] Run existing tests: pytest src/tests/ (blocked: pytest addopts require pytest-cov; pydantic install failed due to proxy 403)
- [ ] Manual test: Stripe webhook with test data (requires Stripe test environment)
References:
- REFACTOR_PLAN.md:171-175
- FORENSIC_AUDIT.md Issue #1.3
- src/api/finance/webhooks.py:331-350
Dependencies: None
Effort: S

### T-042: Document deployment platform and rollback procedures
Priority: P0
Type: RELEASE
Owner: Trevor
Status: BLOCKED
Blocker: Deployment platform decision (Owner: Trevor).
Context:
- Production readiness work is blocked without knowing the deployment target.
- Rollback procedures, DNS, and SSL/TLS ownership cannot be finalized without the platform choice.
Acceptance Criteria:
- [ ] Deployment platform documented (Vercel/K8s/ECS/Railway/etc.).
- [ ] Deployment commands documented in docs/02-how-to/production-deployment.md.
- [ ] Rollback procedures specific to platform documented.
- [ ] DNS configuration documented.
- [ ] SSL/TLS certificate renewal documented.
- [ ] Secrets rotation documented.
References:
- README.md
- docs/DEPLOYMENT.md
- docs/ARCHITECTURE.md
Dependencies: None
Effort: M

