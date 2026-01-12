# TODO.md — Repository Task List

Document Type: Workflow
Last Updated: 2026-01-10
Task Truth Source: **TODO.md**

This file is the single source of truth for actionable work.
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
## Active tasks

### Phase 0 — Production readiness blockers (P0)

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

### Phase 1 — Security and tenant isolation (P1/P3)

#### P1 — High impact (do within 7 days)

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

#### P2 — Important (do within 30 days)

### T-027: Split src/modules/crm/models.py into separate files
Priority: P2
Type: CHORE
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- src/modules/crm/models.py is 3,469 lines (largest file in the codebase).
- Contains 10+ distinct model classes.
- Large files slow agent comprehension, increase merge conflicts, and make testing harder.
- Tests currently fail to collect in this environment due to missing pytest-django/pytest-cov plugins.
Acceptance Criteria:
- [x] Split into src/modules/crm/models/ directory with separate files by entity.
- [x] src/modules/crm/models/__init__.py re-exports all models for backward compatibility.
- [x] All imports elsewhere remain functional (no breaking changes).
- [ ] All existing tests pass without modification.
References:
- src/modules/crm/models.py
Dependencies: None
Effort: M

### T-028: Split src/modules/clients/models.py into separate files
Priority: P2
Type: CHORE
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- src/modules/clients/models.py is 2,699 lines (second largest file).
- Similar complexity issues as crm/models.py.
- Tests currently fail to collect in this environment due to missing pytest-django/pytest-cov plugins.
Acceptance Criteria:
- [x] Split into src/modules/clients/models/ directory with separate files.
- [x] Backward compatible re-exports in __init__.py.
- [ ] All existing tests pass.
References:
- src/modules/clients/models.py
Dependencies: None
Effort: M

### T-032: Consolidate pytest-cov and coverage dependencies
Priority: P2
Type: DEPENDENCY
Owner: AGENT
Status: IN-REVIEW
Blocker: Verification blocked (pip install requirements-dev.txt failed: proxy 403).
Context:
- Both pytest-cov and coverage are installed redundantly.
- pytest-cov already includes coverage as a dependency.
Acceptance Criteria:
- [x] Remove coverage==7.4.0 from requirements-dev.txt (keep pytest-cov).
- [ ] Verify pytest-cov still works: pytest --cov=src tests/. (blocked: pytest-cov not installed in sandbox)
- [x] Update any CI/local scripts that reference coverage directly (none found).
References:
- requirements-dev.txt
- pyproject.toml
- pytest.ini
Dependencies: None
Effort: S

### T-035: Evaluate python3-saml maintenance and consider alternatives
Priority: P2
Type: DEPENDENCY
Owner: Trevor
Status: READY
Blocker: None.
Context:
- python3-saml==1.16.0 last updated 2+ years ago.
- Requires native dependencies (xmlsec, lxml).
- Need to assess if SAML is actively used in production.
Acceptance Criteria:
- [ ] Check if SAML authentication is actively used.
- [ ] If NOT used: Create task to remove python3-saml dependencies.
- [ ] If used: Research alternatives (python-saml fork) and document decision.
References:
- requirements.txt
- src/modules/auth/saml_views.py
Dependencies: None
Effort: M

### T-040: Expand DOCS_INDEX.md to include all major doc categories
Priority: P2
Type: DOCS
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- Current DOCS_INDEX.md covers governance but omits implementation docs, policies, integration guides.
Acceptance Criteria:
- [x] Add sections for: Implementation Docs, Policy Docs, Integration Guides, User Guides.
- [x] List major documents from each category.
References:
- docs/DOCS_INDEX.md
Dependencies: None
Effort: S

### T-047: Add frontend build output verification to CI/CD
Priority: P2
Type: QUALITY
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- Frontend build not verified in pre-release checks.
Acceptance Criteria:
- [x] Root Makefile includes frontend build check.
- [x] Built assets verified to exist.
- [x] Frontend production build tested.
References:
- src/frontend/Makefile
- Makefile
Dependencies: None
Effort: S

### T-052: Enable MyPy type checking in CI pipeline
Priority: P2
Type: QUALITY
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- MyPy configured in pyproject.toml but not enforced in CI.
- Type hints provide value only when checked automatically.
- Prevents type-related bugs.
Acceptance Criteria:
- [x] Add make typecheck command to src/Makefile.
- [x] Command runs mypy src/ with strict settings.
- [x] Add typecheck to root make verify command.
- [x] Fix existing type errors (if any).
- [x] Document type checking requirements in CONTRIBUTING.md.
References:
- pyproject.toml
- src/Makefile
- Diamond Standard Plan Phase 5
Dependencies: None
Effort: M

### T-080: Add ADR template and decision log scaffolding
Priority: P2
Type: DOCS
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- No ADRs for major architectural decisions.
- Historical context lost, decisions re-litigated.
Acceptance Criteria:
- [x] Create docs/05-decisions/ directory.
- [x] Add ADR template (MADR format).
References:
- docs/DOCS_INDEX.md
- CONTRIBUTING.md
- Diamond Standard Plan Phase 6
Dependencies: None
Effort: S

### T-081: Document existing key architectural decisions in ADRs
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Major decisions need recorded context for future work.
Acceptance Criteria:
- [ ] Document decisions: multi-tenancy pattern, firm-scoped queries, break-glass access, billing ledger.
- [ ] ADRs follow the template in docs/05-decisions/.
References:
- docs/05-decisions/
- Diamond Standard Plan Phase 6
Dependencies: T-080
Effort: M

### T-082: Document ADR process in CONTRIBUTING and DOCS_INDEX
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Contributors need to know when and how to add ADRs.
Acceptance Criteria:
- [ ] Add ADR process to CONTRIBUTING.md.
- [ ] Link ADR directory from DOCS_INDEX.md.
References:
- CONTRIBUTING.md
- docs/DOCS_INDEX.md
Dependencies: T-080
Effort: S

### T-054: Create make fixtures command with sample data
Priority: P2
Type: CHORE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- No quick way to populate development environment with realistic data.
- Manual data entry slows development and testing.
- Sample data improves developer experience.
Acceptance Criteria:
- [ ] Create src/modules/core/management/commands/load_fixtures.py.
- [ ] Command creates: 3 firms, 10 users, 20 clients, 30 projects, 50 documents, 10 invoices.
- [ ] Data includes relationships and edge cases.
- [ ] Add make fixtures command to Makefile.
- [ ] Document in README.md.
References:
- src/modules/core/management/commands/
- README.md
- Diamond Standard Plan Phase 7
Dependencies: None
Effort: M

### T-055: Add VS Code workspace settings for consistent developer experience
Priority: P2
Type: CHORE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- No shared IDE configuration causes inconsistent formatting and linting experience.
- VS Code is primary development environment.
- Workspace settings improve onboarding.
Acceptance Criteria:
- [ ] Create .vscode/settings.json with Python, TypeScript, formatting settings.
- [ ] Configure: Black formatter, Ruff linter, ESLint, Prettier.
- [ ] Add .vscode/extensions.json with recommended extensions.
- [ ] Add .vscode/launch.json for debugging Django and frontend.
- [ ] Document in README.md.
References:
- .vscode/
- README.md
- Diamond Standard Plan Phase 7
Dependencies: None
Effort: S

### T-083: Add Locust load test benchmarks
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- No performance regression testing.
- Cannot validate SLO targets (p95 <200ms, FCP <1.5s).
Acceptance Criteria:
- [ ] Create benchmarks/ directory with Locust load tests.
- [ ] Benchmark: auth, CRUD operations, list endpoints, search.
- [ ] Add make benchmark command for Locust tests.
References:
- docs/OBSERVABILITY.md
- Diamond Standard Plan Phase 8
Dependencies: None
Effort: M

### T-084: Add Lighthouse CI for frontend performance
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Frontend performance lacks automated verification.
Acceptance Criteria:
- [ ] Add Lighthouse CI configuration for frontend performance.
- [ ] Document how to run Lighthouse CI locally.
References:
- src/frontend/
- Diamond Standard Plan Phase 8
Dependencies: None
Effort: M

### T-085: Document performance baselines and store benchmark results
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Baseline metrics are needed for trend analysis and SLO tracking.
Acceptance Criteria:
- [ ] Document baseline metrics: API p95, p99, throughput, frontend Core Web Vitals.
- [ ] Store results in benchmarks/results/ for trend analysis.
- [ ] Update docs/OBSERVABILITY.md with baseline metrics and interpretation.
References:
- docs/OBSERVABILITY.md
- benchmarks/results/
- Diamond Standard Plan Phase 8
Dependencies: T-083, T-084
Effort: M

### T-057: Configure slow query logging and alerts
Priority: P2
Type: RELEASE
Owner: AGENT
Status: BLOCKED
Blocker: T-042 (deployment platform).
Context:
- No visibility into slow database queries in production.
- Query performance degradation goes undetected.
- Required for performance SLO compliance.
Acceptance Criteria:
- [ ] Configure PostgreSQL slow query log (threshold: 100ms).
- [ ] Set up log collection (to Sentry or dedicated service).
- [ ] Create alert for queries >500ms.
- [ ] Document query optimization process in docs/04-runbooks/.
- [ ] Add query performance dashboard (if monitoring service supports).
References:
- PostgreSQL configuration
- docs/OBSERVABILITY.md
- Diamond Standard Plan Phase 8
Dependencies: T-042 (deployment platform)
Effort: M

### T-058: Implement Core Web Vitals tracking for frontend
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- No frontend performance monitoring.
- User experience degradation undetected.
- Core Web Vitals (LCP, FID, CLS) are industry standard metrics.
Acceptance Criteria:
- [ ] Integrate web-vitals library in frontend.
- [ ] Send metrics to analytics service (Sentry, Google Analytics, or custom).
- [ ] Create dashboard showing: LCP, FID, CLS, TTFB, FCP, TTI.
- [ ] Set alert thresholds: LCP <2.5s, FID <100ms, CLS <0.1.
- [ ] Document in OBSERVABILITY.md.
References:
- src/frontend/
- docs/OBSERVABILITY.md
Dependencies: None
Effort: M

### T-059: Add query optimization tests to prevent N+1 queries
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- N+1 query patterns cause performance degradation.
- Manual review catches some but not all cases.
- Automated tests prevent regressions.
Acceptance Criteria:
- [ ] Install django-assert-num-queries or similar.
- [ ] Add query count assertions to critical endpoint tests.
- [ ] Test suite fails if query count exceeds baseline.
- [ ] Document query optimization patterns in CONTRIBUTING.md.
- [ ] Add CI check for query efficiency.
References:
- tests/
- CONTRIBUTING.md
- Diamond Standard Plan Phase 8
Dependencies: None
Effort: M

### T-086: Add Meta-commentary for billing, CRM, and automation modules
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Supporting modules (billing, CRM, automation actions) have medium complexity.
- State machines, scoring algorithms, routing rules need context documentation.
Acceptance Criteria:
- [ ] Add Meta-commentary to billing/models.py.
- [ ] Add Meta-commentary to crm/lead_routing.py.
- [ ] Add Meta-commentary to crm/scoring.py.
- [ ] Add Meta-commentary to automation/triggers.py.
- [ ] Add Meta-commentary to automation/actions.py.
- [ ] All Meta-commentary follows STYLE_GUIDE.md template.
References:
- docs/STYLE_GUIDE.md
- src/modules/ (files listed in Acceptance Criteria)
Dependencies: T-064, T-065, T-066, T-067
Effort: M

### T-087: Add Meta-commentary for webhooks, calendar, and projects modules
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Supporting modules (webhooks, calendar, projects) have medium complexity.
- State machines and routing rules need context documentation.
Acceptance Criteria:
- [ ] Add Meta-commentary to webhooks/delivery.py.
- [ ] Add Meta-commentary to sms/webhooks.py.
- [ ] Add Meta-commentary to calendar/availability.py.
- [ ] Add Meta-commentary to calendar/recurrence.py.
- [ ] Add Meta-commentary to projects/pricing.py.
- [ ] All Meta-commentary follows STYLE_GUIDE.md template.
References:
- docs/STYLE_GUIDE.md
- src/modules/ (files listed in Acceptance Criteria)
Dependencies: T-064, T-065, T-066, T-067
Effort: M

### T-088: Add Meta-commentary for onboarding, documents, and finance modules
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Blocker: None.
Context:
- Supporting modules (onboarding, documents, finance) have medium complexity.
- Reconciliation logic needs context documentation.
Acceptance Criteria:
- [ ] Add Meta-commentary to onboarding/workflows.py.
- [ ] Add Meta-commentary to documents/malware_scan.py.
- [ ] Add Meta-commentary to documents/reconciliation.py.
- [ ] Add Meta-commentary to finance/reconciliation.py.
- [ ] Add Meta-commentary to finance/ledger.py.
- [ ] All Meta-commentary follows STYLE_GUIDE.md template.
References:
- docs/STYLE_GUIDE.md
- src/modules/ (files listed in Acceptance Criteria)
Dependencies: T-064, T-065, T-066, T-067
Effort: M

### T-089: Define and implement document approval workflow requirements
Priority: P2
Type: FEATURE
Owner: AGENT
Status: BLOCKED
Blocker: Product requirements for approval workflow (status transitions, roles, notifications).
Context:
- Document model includes placeholders for approval workflow fields.
- Inline TODO markers referenced untracked workflow requirements in src/modules/documents/models/documents.py.
- Requirements for approval lifecycle and permissions are not documented.
Acceptance Criteria:
- [ ] Define approval workflow statuses and transitions (draft → review → approved → published).
- [ ] Document who can submit/review/publish and any notification requirements.
- [ ] Implement service logic + API updates for approval workflow.
- [ ] Update tests to cover approval workflow transitions and permissions.
References:
- src/modules/documents/models/documents.py
- docs/14 DOCUMENTS_AND_STORAGE_SPEC
Dependencies: None
Effort: M

#### P3 — Backlog / tech debt

### T-029: Split src/modules/documents/models.py into separate files
Priority: P3
Type: CHORE
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- src/modules/documents/models.py is 2,386 lines.
- Tests currently fail to collect in this environment due to missing pytest-django/pytest-cov plugins.
Acceptance Criteria:
- [x] Split into src/modules/documents/models/ directory.
- [x] Backward compatible re-exports.
- [ ] All tests pass.
References:
- src/modules/documents/models.py
Dependencies: None
Effort: M

### T-030: Split src/modules/calendar/services.py into focused service classes
Priority: P3
Type: CHORE
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- src/modules/calendar/services.py is 2,360 lines (single service doing too much).
Acceptance Criteria:
- [ ] Split into focused service classes by provider/responsibility.
- [ ] Maintain existing public API.
- [ ] All tests pass.
References:
- src/modules/calendar/services.py
Dependencies: None
Effort: M

### T-037: Evaluate Pillow dependency for single watermarking usage
Priority: P3
Type: DEPENDENCY
Owner: Trevor
Status: READY
Blocker: None.
Context:
- Pillow is large native dependency used in only 1 location (image watermarking).
- Need product decision on watermarking requirement.
Acceptance Criteria:
- [ ] Assess if watermarking feature is actively used.
- [ ] If NOT needed: Create task to remove Pillow.
- [ ] If needed: Document decision to keep with justification.
References:
- requirements.txt
- src/modules/core/access_controls.py
Dependencies: None
Effort: S

### T-039: Resolve numbered docs inventory decision
Priority: P3
Type: DOCS
Owner: Trevor
Status: BLOCKED
Blocker: Trevor review of numbered docs.
Context:
- docs/ contains 35 numbered files without .md extension.
- Not referenced in DOCS_INDEX.md or other navigation.
- Appears to be alternative/legacy spec format.
Acceptance Criteria:
- [ ] Trevor reviews numbered files to determine if they should be archived, renamed, or deleted.
- [ ] Decision documented.
References:
- docs/1 through docs/35
- docs/DOCS_INDEX.md
Dependencies: None
Effort: S

### T-041: Create missing user guides or clean up dead references
Priority: P3
Type: DOCS
Owner: Trevor
Status: BLOCKED
Blocker: Trevor decision on missing guides.
Context:
- DOCS_INDEX.md references firm-admin-guide.md and client-portal-guide.md but files don't exist.
Acceptance Criteria:
- [ ] Decide whether to create missing guides or remove references.
- [ ] If creating guides, create basic structure.
References:
- docs/DOCS_INDEX.md
Dependencies: None
Effort: M

## Backlog
<!-- Add future tasks here. -->

## Notes
- No automation is allowed to rewrite this file.
- Optional scripts may generate `TODO.generated.md` for convenience; it is never authoritative.
