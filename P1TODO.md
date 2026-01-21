# P1TODO.md - Repository Task List

Document Type: Workflow
Last Updated: 2026-01-21
Task Truth Source: **P1TODO.md**
Other Priority Files: P0TODO.md, P2TODO.md, P3TODO.md

<!--
Meta-commentary:
  - Current Status: Authoritative task list; T-127, T-135, T-137, and T-138 moved to TODOCOMPLETED.md.
  - Mapping: Mirrors completed work recorded in TODOCOMPLETED.md and CHANGELOG.md.
- Reasoning: Keep task truth source accurate after completion.
- Assumption: Tasks are appended/moved manually with auditability in mind.
- Limitation: This file does not capture execution details beyond acceptance criteria.
-->

This file is the single source of truth for P1 tasks.
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

### Phase 1 — Security and tenant isolation (P1/P3)
#### P1 — High impact (do within 7 days)
### T-131: Create comprehensive GitHub Actions CI/CD workflow (REFACTOR Phase 1)
Priority: P1
Type: RELEASE
Owner: AGENT
Status: READY
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 1 Item 1 - Enable automated quality gates
- CI/CD automation must be enforced with branch protection and verified runs
- Broken code can merge to main without automated checks
- FORENSIC_AUDIT.md Issue #8.1
Acceptance Criteria:
- [ ] Create .github/workflows/ci.yml with jobs: test, lint, typecheck, security-scan
- [ ] Configure test job: pytest --cov=src --cov-fail-under=60
- [ ] Configure lint job: black --check, ruff check, mypy
- [ ] Configure security job: pip-audit --strict, bandit -r src/
- [ ] Configure frontend job: npm ci, npm run typecheck, npm run test, npm run build
- [ ] Enable branch protection requiring CI pass before merge
- [ ] Push test commit and verify CI runs
References:
- REFACTOR_PLAN.md:186-215, 492-536
- FORENSIC_AUDIT.md Issue #8.1
- .github/workflows/ci.yml
Dependencies: None
Effort: M

### T-132: Update pre-commit hooks for comprehensive validation (REFACTOR Phase 1)
Priority: P1
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 1 Item 2 - Prevent style drift and secret commits
- Existing .pre-commit-config.yaml needs enhancement
- FORENSIC_AUDIT.md Issue #8.4 - No SAST in pipeline
Acceptance Criteria:
- [ ] Update .pre-commit-config.yaml with: black, ruff, mypy, git-secrets, eslint
- [ ] Configure mypy to run on src/ with pass_filenames: false
- [ ] Add git-secrets hook to prevent secret commits
- [ ] Add eslint for frontend files in src/frontend/
- [ ] Test pre-commit hooks: try committing with lint error, verify blocked
- [ ] Document pre-commit setup in CONTRIBUTING.md
References:
- REFACTOR_PLAN.md:197-201, 441-478
- FORENSIC_AUDIT.md Issue #8.4
- .pre-commit-config.yaml
Dependencies: None
Effort: S
### T-133: Configure dependency scanning in CI pipeline (REFACTOR Phase 1)
Priority: P1
Type: SECURITY
Owner: AGENT
Status: READY
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 1 Item 3 - Prevent known CVEs in production
- No automated dependency vulnerability scanning
- FORENSIC_AUDIT.md Issue #6.2, #6.4 - CVE risks
Acceptance Criteria:
- [ ] Add pip-audit to CI workflow (security job)
- [ ] Configure weekly dependency scan schedule
- [ ] Add safety check for Python dependencies
- [ ] Document dependency scanning process
- [ ] Set up notifications for new vulnerabilities
References:
- REFACTOR_PLAN.md:203-206
- FORENSIC_AUDIT.md Issue #6.2, #6.4
Dependencies: T-131 (CI workflow)
Effort: S

### T-148: Enable GitHub Actions workflows and remove cost-control governance
Priority: P1
Type: CHORE
Owner: AGENT
Status: IN-REVIEW
Blocker: None
Context:
- GitHub Actions were parked in a nonstandard directory and need to run from `.github/workflows/`.
- Governance docs still mention disabled-by-default Actions.
- Repo manifest and scripts should align with enabled workflows.
Acceptance Criteria:
- [x] Move GitHub Actions workflows into `.github/workflows/`.
- [x] Remove cost-control governance references tied to GitHub Actions.
- [x] Update governance docs and scripts to point to `.github/workflows/`.
- [x] Update repo.manifest.yaml to reflect enabled Actions.
References:
- CODEBASECONSTITUTION.md
- READMEAI.md
- BESTPR.md
- repo.manifest.yaml
- .github/workflows/
Dependencies: None
Effort: S

### T-136: Sanitize error messages to prevent information disclosure (REFACTOR Phase 2)
Priority: P1
Type: SECURITY
Owner: AGENT
Status: IN-REVIEW
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 2 Item 3 - Eliminate critical security vulnerabilities
- Detailed error messages exposed to clients reveal internal state
- Information disclosure aids attackers
- FORENSIC_AUDIT.md Issue #5.1 findings
Acceptance Criteria:
- [x] Replace detailed errors with generic messages in src/modules/auth/saml_views.py:163,209,243
- [x] Add security comments explaining information disclosure prevention
- [ ] Log detailed error info server-side only (deferred to observability phase)
- [ ] Ensure no stack traces sent to clients (requires middleware review)
- [x] Add tests for generic error responses (tests/auth/test_saml_views.py)
- [ ] Review all auth endpoints for information disclosure (separate task needed)
References:
- REFACTOR_PLAN.md:234-237
- FORENSIC_AUDIT.md Issue #5.1
- src/modules/auth/saml_views.py:163,209,243
Dependencies: None
Effort: S

### T-050: Create incident response runbooks
Priority: P1
Type: DOCS
Owner: AGENT
Status: BLOCKED
Blocker: T-042 (deployment platform).
Context:
- No documented procedures for responding to production incidents.
- Increases MTTR (mean time to recovery) during outages.
- Required for operations maturity.
Acceptance Criteria:
- [ ] Create docs/04-runbooks/incident-response/ directory.
- [ ] Document runbooks for: service degradation, database issues, payment failures, security incidents, data corruption.
- [ ] Each runbook includes: symptoms, diagnosis steps, remediation, escalation path, post-mortem template.
- [ ] Link from OBSERVABILITY.md.
References:
- docs/OBSERVABILITY.md
- Diamond Standard Plan Phase 4
Dependencies: T-042 (deployment platform)
Effort: M

### T-051: Set up uptime monitoring and alerting
Priority: P1
Type: RELEASE
Owner: Trevor
Status: BLOCKED
Blocker: T-042 (deployment platform).
Context:
- No external uptime monitoring configured.
- Cannot detect outages proactively.
- Required for SLO compliance and on-call operations.
Acceptance Criteria:
- [ ] Configure uptime monitoring service (UptimeRobot, Pingdom, or similar).
- [ ] Monitor: /health/, /ready/, key API endpoints, frontend.
- [ ] Configure alerts to: on-call rotation, Slack/PagerDuty.
- [ ] Document monitoring setup in OBSERVABILITY.md.
- [ ] Test alert delivery.
References:
- docs/OBSERVABILITY.md
- Diamond Standard Plan Phase 4
Dependencies: T-042 (deployment platform)
Effort: M

