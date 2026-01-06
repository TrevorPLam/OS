# TODO.md — Repository Task List

Document Type: Workflow
Last Updated: 2026-01-06
Task Truth Source: **TODO.md**

This file is the single source of truth for actionable work.
If another document disagrees, the task record in this file wins (unless the Constitution overrides).

## Task schema (required)
- **ID**: `T-###` (unique)
- **Priority**: `P0 | P1 | P2 | P3`
- **Type**: `SECURITY | RELEASE | DEPENDENCY | DOCS | QUALITY | BUG | FEATURE | CHORE`
- **Owner**: `AGENT | Trevor`
- **Status**: `READY | BLOCKED | IN-PROGRESS | IN-REVIEW`
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

### T-073: Tenant isolation enforcement audit (firm-scoped query correctness)
Priority: P1
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- Tenant isolation depends on always applying firm scoping at queryset boundaries.
Acceptance Criteria:
- [ ] Identify endpoints/services that use Model.objects.* where firm scoping is required.
- [ ] Replace with firm-scoped managers/querysets where appropriate.
- [ ] Add cross-firm negative tests (data leakage prevention).
- [ ] Document the rule in CONTRIBUTING.md.
References:
- src/modules/firm/utils.py
- src/api/
- src/modules/
Dependencies: None
Effort: L

### T-060: PostgreSQL Row-Level Security (RLS) defense-in-depth
Priority: P3
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- Application-layer scoping is necessary but not sufficient for “diamond” isolation.
Acceptance Criteria:
- [ ] RLS is enabled for tenant-scoped tables and validated.
References:
- src/modules/core/middleware.py
- docs/SECURITY.md
Dependencies: T-119, T-120, T-121, T-122, T-123
Effort: L

### T-119: RLS 1/5 — Inventory tenant-scoped tables
Priority: P3
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- Need an explicit inventory before writing policies.
Acceptance Criteria:
- [ ] List all tables requiring firm scoping.
- [ ] Verify firm_id columns and constraints.
References:
- src/modules/
Dependencies: None
Effort: M

### T-120: RLS 2/5 — Set app.current_firm_id for DB session
Priority: P3
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- Policies require an unspoofable session variable.
Acceptance Criteria:
- [ ] Middleware sets current_setting('app.current_firm_id') safely per request.
- [ ] Background jobs set firm context where applicable.
References:
- src/modules/core/middleware.py
Dependencies: T-119
Effort: M

### T-121: RLS 3/5 — Add migrations to enable RLS + policies
Priority: P3
Type: SECURITY
Owner: AGENT
Status: READY
Context:
- RLS must be enabled and policies installed via migrations.
Acceptance Criteria:
- [ ] Migration enables RLS on inventory tables.
- [ ] Policies enforce firm_id = current_setting('app.current_firm_id').
References:
- src/
Dependencies: T-119, T-120
Effort: L

### T-122: RLS 4/5 — Tests validating RLS with direct SQL
Priority: P3
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- Need proof RLS works even if app code is wrong.
Acceptance Criteria:
- [ ] Tests attempt cross-firm selects via raw SQL and verify rejection.
References:
- tests/
Dependencies: T-121
Effort: M

### T-123: RLS 5/5 — Document RLS model + ops implications
Priority: P3
Type: DOCS
Owner: AGENT
Status: READY
Context:
- Security posture must be explainable.
Acceptance Criteria:
- [ ] SECURITY.md explains RLS assumptions, limitations, and debugging steps.
References:
- SECURITY.md
Dependencies: T-121
Effort: S

### T-026: Add deal management unit tests
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- Deal models, views, and automation logic exist but no dedicated test files found.
- Deal assignment automation, stage automation, and rotting detection need test coverage.
Acceptance Criteria:
- [ ] tests/crm/test_deal_models.py exists with Deal model tests.
- [ ] tests/crm/test_deal_views.py exists with DealViewSet tests.
- [ ] tests/crm/test_deal_assignment_automation.py exists with assignment rule tests.
- [ ] tests/crm/test_deal_stage_automation.py exists with stage automation tests.
- [ ] tests/crm/test_deal_rotting.py exists with stale deal detection tests.
References:
- src/modules/crm/models.py
- src/modules/crm/views.py
Dependencies: None
Effort: L

### T-027: Split src/modules/crm/models.py into separate files
Priority: P2
Type: CHORE
Owner: AGENT
Status: READY
Context:
- src/modules/crm/models.py is 3,469 lines (largest file in the codebase).
- Contains 10+ distinct model classes.
- Large files slow agent comprehension, increase merge conflicts, and make testing harder.
Acceptance Criteria:
- [ ] Split into src/modules/crm/models/ directory with separate files by entity.
- [ ] src/modules/crm/models/__init__.py re-exports all models for backward compatibility.
- [ ] All imports elsewhere remain functional (no breaking changes).
- [ ] All existing tests pass without modification.
References:
- src/modules/crm/models.py
Dependencies: None
Effort: M

### T-028: Split src/modules/clients/models.py into separate files
Priority: P2
Type: CHORE
Owner: AGENT
Status: READY
Context:
- src/modules/clients/models.py is 2,699 lines (second largest file).
- Similar complexity issues as crm/models.py.
Acceptance Criteria:
- [ ] Split into src/modules/clients/models/ directory with separate files.
- [ ] Backward compatible re-exports in __init__.py.
- [ ] All existing tests pass.
References:
- src/modules/clients/models.py
Dependencies: None
Effort: M

### T-029: Split src/modules/documents/models.py into separate files
Priority: P3
Type: CHORE
Owner: AGENT
Status: READY
Context:
- src/modules/documents/models.py is 2,386 lines.
Acceptance Criteria:
- [ ] Split into src/modules/documents/models/ directory.
- [ ] Backward compatible re-exports.
- [ ] All tests pass.
References:
- src/modules/documents/models.py
Dependencies: None
Effort: M

### T-030: Split src/modules/calendar/services.py into focused service classes
Priority: P3
Type: CHORE
Owner: AGENT
Status: READY
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

### T-031: Remove unused dev dependencies (factory-boy, faker, import-linter)
Priority: P2
Type: DEPENDENCY
Owner: AGENT
Status: READY
Context:
- Three dev dependencies installed but unused.
- Removing these simplifies dev environment and reduces attack surface.
Acceptance Criteria:
- [ ] Remove factory-boy==3.3.0 from requirements-dev.txt.
- [ ] Remove faker==22.0.0 from requirements-dev.txt.
- [ ] Remove import-linter==2.0 from requirements-dev.txt.
- [ ] Run pip install -r requirements-dev.txt to verify no breaking changes.
- [ ] Run test suite to verify no hidden dependencies.
References:
- requirements-dev.txt
Dependencies: None
Effort: S

### T-032: Consolidate pytest-cov and coverage dependencies
Priority: P2
Type: DEPENDENCY
Owner: AGENT
Status: READY
Context:
- Both pytest-cov and coverage are installed redundantly.
- pytest-cov already includes coverage as a dependency.
Acceptance Criteria:
- [ ] Remove coverage==7.4.0 from requirements-dev.txt (keep pytest-cov).
- [ ] Verify pytest-cov still works: pytest --cov=src tests/.
- [ ] Update any CI/local scripts that reference coverage directly.
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

### T-036: Evaluate DocuSign SDK adoption
Priority: P2
Type: DEPENDENCY
Owner: AGENT
Status: READY
Context:
- Currently using raw requests library for DocuSign API.
- Official SDK available: docusign-esign.
Acceptance Criteria:
- [ ] Research SDK size and dependencies.
- [ ] Compare SDK methods to current implementation.
- [ ] Make recommendation: migrate to SDK or keep custom implementation.
- [ ] Document findings in DEPENDENCYAUDIT.md.
References:
- src/modules/esignature/docusign_service.py
Dependencies: None
Effort: M

### T-037: Evaluate Pillow dependency for single watermarking usage
Priority: P3
Type: DEPENDENCY
Owner: Trevor
Status: READY
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

### T-038: Create comprehensive dependency documentation
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- Several critical dependencies lack documentation.
- No single document explaining dependency choices.
Acceptance Criteria:
- [ ] Create docs/DEPENDENCIES.md with all major dependencies documented.
- [ ] Document: purpose, usage, alternatives, upgrade considerations.
- [ ] Link from README.md to DEPENDENCIES.md.
References:
- requirements.txt
- requirements-dev.txt
Dependencies: None
Effort: L

### T-039: Review and consolidate numbered docs files (docs/1-35)
Priority: P3
Type: DOCS
Owner: Trevor
Status: BLOCKED
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

### T-040: Expand DOCS_INDEX.md to include all major doc categories
Priority: P3
Type: DOCS
Owner: AGENT
Status: READY
Context:
- Current DOCS_INDEX.md covers governance but omits implementation docs, policies, integration guides.
Acceptance Criteria:
- [ ] Add sections for: Implementation Docs, Policy Docs, Integration Guides, User Guides.
- [ ] List major documents from each category.
References:
- docs/DOCS_INDEX.md
Dependencies: None
Effort: S

### T-041: Create missing user guides or clean up dead references
Priority: P3
Type: DOCS
Owner: Trevor
Status: BLOCKED
Context:
- DOCS_INDEX.md references firm-admin-guide.md and client-portal-guide.md but files don't exist.
Acceptance Criteria:
- [ ] Decide whether to create missing guides or remove references.
- [ ] If creating guides, create basic structure.
References:
- docs/DOCS_INDEX.md
Dependencies: None
Effort: M

### T-044: Add production environment variable validation
Priority: P1
Type: RELEASE
Owner: AGENT
Status: READY
Context:
- No startup validation of required vars in production.
- Missing critical vars could cause runtime failures.
Acceptance Criteria:
- [ ] Startup script validates required environment variables.
- [ ] Missing vars cause immediate failure with clear error message.
- [ ] Validation runs in manage.py or container entrypoint.
References:
- .env.example
- src/config/env_validator.py
Dependencies: None
Effort: S

### T-045: Implement Sentry monitoring hooks for critical flows
Priority: P1
Type: RELEASE
Owner: AGENT
Status: READY
Context:
- Sentry integration exists but critical flow instrumentation incomplete.
Acceptance Criteria:
- [ ] Payment processing wrapped in Sentry transaction spans.
- [ ] Webhook handlers log custom breadcrumbs.
- [ ] Email ingestion failures tagged with firm context.
- [ ] Break-glass access events sent to Sentry.
References:
- src/config/sentry.py
- src/modules/finance/
- src/modules/webhooks/
Dependencies: None
Effort: M

### T-046: Document monitoring and alerting requirements
Priority: P1
Type: DOCS
Owner: AGENT
Status: READY
Context:
- OBSERVABILITY.md exists but doesn't define alert thresholds or monitoring requirements.
Acceptance Criteria:
- [ ] Define alert thresholds.
- [ ] Document which metrics require 24/7 paging.
- [ ] Create runbook for common failure scenarios.
- [ ] Define SLO targets.
References:
- docs/OBSERVABILITY.md
Dependencies: None
Effort: M

### T-047: Add frontend build output verification to CI/CD
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- Frontend build not verified in pre-release checks.
Acceptance Criteria:
- [ ] Root Makefile includes frontend build check.
- [ ] Built assets verified to exist.
- [ ] Frontend production build tested.
References:
- src/frontend/Makefile
- Makefile
Dependencies: None
Effort: S

### T-048: Add frontend unit tests with React Testing Library and Vitest
Priority: P1
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- Frontend has no unit tests (CODEAUDIT.md finding).
- React components untested increases regression risk.
- Need test infrastructure before expanding features.
Acceptance Criteria:
- [ ] Install @testing-library/react and vitest as dev dependencies.
- [ ] Configure vitest in vite.config.ts.
- [ ] Create tests/ directory in src/frontend/.
- [ ] Add tests for: AuthContext, API client, form components.
- [ ] Achieve 60%+ frontend test coverage.
- [ ] Add npm test command to package.json.
- [ ] Update root Makefile to include frontend tests in make test.
References:
- src/frontend/
- Diamond Standard Plan Phase 3
Dependencies: None
Effort: L

### T-049: Implement E2E tests for critical paths with Playwright
Priority: P1
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- Critical user journeys lack E2E test coverage.
- Manual smoke testing is error-prone and slow.
- Need automated regression prevention for auth, payments, core workflows.
Acceptance Criteria:
- [ ] Install @playwright/test as dev dependency.
- [ ] Create e2e/ directory with Playwright config.
- [ ] Implement E2E tests for: registration, login, MFA, OAuth, create firm, create client, create invoice, payment flow.
- [ ] Tests run against Docker Compose environment.
- [ ] Add make e2e command.
- [ ] Tests pass in CI (when enabled).
References:
- Docker Compose environment
- RELEASEAUDIT.md smoke test checklist
- Diamond Standard Plan Phase 3
Dependencies: None
Effort: L

### T-050: Create incident response runbooks
Priority: P1
Type: DOCS
Owner: AGENT
Status: READY
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

### T-052: Enable MyPy type checking in CI pipeline
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- MyPy configured in pyproject.toml but not enforced in CI.
- Type hints provide value only when checked automatically.
- Prevents type-related bugs.
Acceptance Criteria:
- [ ] Add make typecheck command to src/Makefile.
- [ ] Command runs mypy src/ with strict settings.
- [ ] Add typecheck to root make verify command.
- [ ] Fix existing type errors (if any).
- [ ] Document type checking requirements in CONTRIBUTING.md.
References:
- pyproject.toml
- src/Makefile
- Diamond Standard Plan Phase 5
Dependencies: None
Effort: M

### T-053: Add Architecture Decision Records (ADRs) template
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- No ADRs for major architectural decisions.
- Historical context lost, decisions re-litigated.
- ADRs are diamond standard practice.
Acceptance Criteria:
- [ ] Create docs/05-decisions/ directory.
- [ ] Add ADR template (MADR format).
- [ ] Document existing key decisions: multi-tenancy pattern, firm-scoped queries, break-glass access, billing ledger.
- [ ] Add ADR process to CONTRIBUTING.md.
- [ ] Link from DOCS_INDEX.md.
References:
- docs/DOCS_INDEX.md
- CONTRIBUTING.md
- Diamond Standard Plan Phase 6
Dependencies: None
Effort: M

### T-054: Create make fixtures command with sample data
Priority: P2
Type: CHORE
Owner: AGENT
Status: READY
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

### T-056: Add performance benchmarks with Locust and Lighthouse
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Context:
- No performance regression testing.
- Cannot validate SLO targets (p95 <200ms, FCP <1.5s).
- Benchmarks prevent performance degradation over time.
Acceptance Criteria:
- [ ] Create benchmarks/ directory with Locust load tests.
- [ ] Benchmark: auth, CRUD operations, list endpoints, search.
- [ ] Add Lighthouse CI for frontend performance.
- [ ] Document baseline metrics: API p95, p99, throughput, frontend Core Web Vitals.
- [ ] Add make benchmark command.
- [ ] Store results in benchmarks/results/ for trend analysis.
References:
- docs/OBSERVABILITY.md
- Diamond Standard Plan Phase 8
Dependencies: None
Effort: L

### T-057: Configure slow query logging and alerts
Priority: P2
Type: RELEASE
Owner: AGENT
Status: READY
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
- Diamond Standard Plan Phase 8
Dependencies: None
Effort: M

### T-059: Add query optimization tests to prevent N+1 queries
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
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

### T-061: Plan API v2 for breaking changes
Priority: P3
Type: DOCS
Owner: AGENT
Status: IN-REVIEW
Context:
- API v1 accumulating technical debt.
- Future breaking changes need deprecation strategy.
- API versioning planning prevents customer disruption.
Acceptance Criteria:
- [ ] Create docs/API_V2_PLAN.md.
- [ ] Document: breaking changes needed, deprecation timeline, migration guide, parallel running strategy.
- [ ] Identify v1 endpoints for deprecation.
- [ ] Define v2 URL structure (/api/v2/).
- [ ] Review API_VERSIONING_POLICY.md for compliance.
References:
- docs/API_VERSIONING_POLICY.md
- Diamond Standard Plan Phase 9
Dependencies: None
Effort: M

### T-067: Add Meta-commentary to P1 integration modules
Priority: P1
Type: DOCS
Owner: AGENT
Status: READY
Context:
- Integration modules have webhook handlers, sync services with incomplete retry/reconciliation.
- Conflict resolution strategies and idempotency key usage need documentation.
- Frequent troubleshooting makes Meta-commentary valuable.
Acceptance Criteria:
- [ ] Add Meta-commentary to src/modules/calendar/services.py: CalendarService (sync conflict resolution, mapping staleness).
- [ ] Add Meta-commentary to src/modules/accounting_integrations/sync.py: sync_invoices_bidirectional (last-write-wins, sync locking missing).
- [ ] Add Meta-commentary to src/modules/esignature/docusign_service.py: DocuSignService (webhook verification, retry on network errors).
- [ ] Add Meta-commentary to src/modules/finance/stripe_service.py: create_payment_intent (idempotency enforcement, reconciliation gap).
- [ ] Add Meta-commentary to src/modules/jobs/queue.py: claim_job (concurrency assumptions, stale worker detection).
- [ ] All Meta-commentary follows STYLE_GUIDE.md template.
References:
- docs/STYLE_GUIDE.md
- src/modules/calendar/services.py
- src/modules/accounting_integrations/sync.py
- src/modules/esignature/docusign_service.py
- src/modules/finance/stripe_service.py
- src/modules/jobs/queue.py
Dependencies: T-064
Effort: M

### T-068: Add Meta-commentary to P2 supporting modules (backlog)
Priority: P2
Type: DOCS
Owner: AGENT
Status: READY
Context:
- Supporting modules (billing, CRM, automation actions) have medium complexity.
- State machines, scoring algorithms, routing rules need context documentation.
- Lower priority but still valuable for long-term maintainability.
Acceptance Criteria:
- [ ] Add Meta-commentary to 15 files: billing/models.py, crm/lead_routing.py, crm/scoring.py, automation/triggers.py, automation/actions.py, webhooks/delivery.py, sms/webhooks.py, calendar/availability.py, calendar/recurrence.py, projects/pricing.py, onboarding/workflows.py, documents/malware_scan.py, documents/reconciliation.py, finance/reconciliation.py, finance/ledger.py.
- [ ] All Meta-commentary follows STYLE_GUIDE.md template.
- [ ] Focus on state machines, assumptions, incomplete implementations, known limitations.
References:
- docs/STYLE_GUIDE.md
- src/modules/* (15 files listed in Context)
Dependencies: T-064, T-065, T-066, T-067
Effort: L

## Backlog
<!-- Add future tasks here. -->

## Notes
- No automation is allowed to rewrite this file.
- Optional scripts may generate `TODO.generated.md` for convenience; it is never authoritative.
