# TODO.md — Repository Task List

Document Type: Workflow
Last Updated: 2026-01-16
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

### T-082: Document ADR process in CONTRIBUTING and DOCS_INDEX
Priority: P2
Type: DOCS
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- Contributors need to know when and how to add ADRs.
Acceptance Criteria:
- [x] Add ADR process to CONTRIBUTING.md.
- [x] Link ADR directory from DOCS_INDEX.md.
References:
- CONTRIBUTING.md
- docs/DOCS_INDEX.md
Dependencies: T-080
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

#### P2 — Feature completion from F&F (module gaps)

### T-090: Add CRM pipeline forecasting and activity timeline/audit history
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F flags pipeline forecasting and activity timeline/audit history as missing in CRM.
- Forecasting and activity visibility are core CRM capabilities expected for sales ops.
Acceptance Criteria:
- [ ] Define CRM pipeline forecasting requirements and data model changes (if needed).
- [ ] Implement pipeline forecasting service logic and API endpoints.
- [ ] Implement activity timeline/audit history storage and API endpoints.
- [ ] Document CRM forecasting and timeline behavior in module docs.
References:
- F&F.md
- src/modules/crm/
Dependencies: None
Effort: M

### T-091: Implement marketing orchestration, testing, analytics, and compliance tooling
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F shows marketing gaps: orchestration, A/B testing, analytics dashboards, consent management, asset library integration.
- These are foundational for scalable campaigns and compliance.
Acceptance Criteria:
- [ ] Add multi-channel orchestration workflows for marketing campaigns.
- [ ] Implement A/B testing framework (experiment definition, assignment, reporting).
- [ ] Build engagement analytics dashboards for campaign performance.
- [ ] Add compliance & consent management controls for marketing outreach.
- [ ] Integrate marketing campaigns with asset library usage.
- [ ] Document marketing orchestration and compliance workflows.
References:
- F&F.md
- src/modules/marketing/
Dependencies: None
Effort: L

### T-092: Build client lifecycle automation and analytics dashboards
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F marks client lifecycle automation and analytics dashboards as missing.
- Lifecycle automation and analytics are key to retention and account management.
Acceptance Criteria:
- [ ] Define client lifecycle stages and automation triggers.
- [ ] Implement lifecycle automation services and API endpoints.
- [ ] Add client analytics dashboards (health trends, segmentation insights).
- [ ] Document client lifecycle automation workflows.
References:
- F&F.md
- src/modules/clients/
Dependencies: None
Effort: M

### T-093: Expand e-signature support for multi-provider workflows and auditability
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F shows missing multi-provider support, template/envelope UI, audit trails/legal hold, and reminders.
- E-signature compliance depends on auditability and reminder workflows.
Acceptance Criteria:
- [ ] Add multi-provider integration abstraction for e-signature services.
- [ ] Implement template and envelope management UI or API endpoints.
- [ ] Add audit trail storage and legal hold workflows for signed documents.
- [ ] Implement reminder and expiration workflows for envelopes.
- [ ] Document supported providers and audit trail behavior.
References:
- F&F.md
- src/modules/esignature/
Dependencies: None
Effort: L

### T-094: Implement project delivery APIs, timelines, and operational dashboards
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing project CRUD APIs, timelines, resource management, milestones, dashboards, and time tracking.
- These are baseline capabilities for project delivery and profitability analysis.
Acceptance Criteria:
- [ ] Add project CRUD API endpoints and serialization.
- [ ] Implement Gantt/timeline visualization data sources.
- [ ] Add resource management and capacity allocation support.
- [ ] Implement milestone and dependency management UI/API.
- [ ] Add project health dashboards and reporting.
- [ ] Implement time tracking and cost rollup capabilities.
- [ ] Document project delivery workflows.
References:
- F&F.md
- src/modules/projects/
Dependencies: None
Effort: L

### T-095: Extend finance module with APIs, tax handling, reporting, and dunning
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F notes missing finance APIs, tax/VAT handling, reporting dashboards, dunning, and forecasting.
- Finance workflows require compliance and collection tooling.
Acceptance Criteria:
- [ ] Add finance operation API endpoints and serializers.
- [ ] Implement tax/VAT calculation and storage.
- [ ] Build financial reporting dashboards (AR, revenue, aging).
- [ ] Add dunning & collections workflows (reminders, escalation).
- [ ] Implement forecasting & cashflow projections.
- [ ] Document finance operational workflows.
References:
- F&F.md
- src/modules/finance/
Dependencies: None
Effort: L

### T-096: Add calendar analytics and resource capacity planning
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing calendar analytics/reporting and capacity planning.
- Capacity planning supports SLA and staffing decisions.
Acceptance Criteria:
- [ ] Define analytics metrics for booking performance and utilization.
- [ ] Implement calendar analytics data collection and reporting endpoints.
- [ ] Add resource capacity planning workflows and UI/API support.
- [ ] Document analytics and capacity planning features.
References:
- F&F.md
- src/modules/calendar/
Dependencies: None
Effort: M

### T-097: Add document CRUD APIs, retention policies, and search/indexing
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F indicates missing document CRUD APIs, retention/archival policies, and search/indexing.
- Approval workflows are tracked separately in T-089.
Acceptance Criteria:
- [ ] Implement document CRUD API endpoints and serializers.
- [ ] Add retention and archival policy enforcement.
- [ ] Implement document search and indexing workflows.
- [ ] Document retention and search behavior.
References:
- F&F.md
- src/modules/documents/
Dependencies: T-089
Effort: M

### T-098: Implement account recovery and password reset flows
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F flags missing account recovery and password reset flows in auth.
- These are essential for user access continuity and security.
Acceptance Criteria:
- [ ] Define password reset and account recovery requirements.
- [ ] Implement recovery tokens, expiry, and email/SMS delivery.
- [ ] Add API endpoints and UI/UX support for recovery flows.
- [ ] Document auth recovery flows and security controls.
References:
- F&F.md
- src/modules/auth/
Dependencies: None
Effort: M

### T-099: Add automation versioning/rollback and audit trails
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F highlights missing automation versioning/rollback and audit trails.
- Automation governance requires traceability and safe rollbacks.
Acceptance Criteria:
- [ ] Implement versioning for automation definitions.
- [ ] Add rollback mechanisms and API support.
- [ ] Implement audit trail logging for automation runs.
- [ ] Document automation governance features.
References:
- F&F.md
- src/modules/automation/
Dependencies: None
Effort: M

### T-100: Implement feature flag and experimentation framework in core
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F indicates missing feature flag/experimentation framework in core.
- Feature flags enable safe rollouts and experimentation.
Acceptance Criteria:
- [ ] Design feature flag data model and evaluation strategy.
- [ ] Implement flag management APIs and admin UI (if applicable).
- [ ] Add SDK/utilities for feature checks across modules.
- [ ] Document feature flag usage guidelines.
References:
- F&F.md
- src/modules/core/
Dependencies: None
Effort: M

### T-101: Implement webhook verification, signing, retries, and observability
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing webhooks verification, retry/backoff, delivery status, signing, tenant isolation, and observability dashboards.
- Webhook reliability and security are critical for integrations.
Acceptance Criteria:
- [ ] Implement webhook endpoints with verification/signing support.
- [ ] Add retry/backoff policies and delivery status tracking.
- [ ] Implement secret rotation and tenant isolation controls.
- [ ] Add webhook observability dashboards and alerting hooks.
- [ ] Document webhook security and delivery guarantees.
References:
- F&F.md
- src/modules/webhooks/
Dependencies: None
Effort: L

### T-102: Expand integrations management with token lifecycle and health dashboards
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F highlights missing OAuth token lifecycle management, webhook verification, health dashboards, marketplace registry, and usage analytics.
- Integration reliability depends on token refresh and health monitoring.
Acceptance Criteria:
- [ ] Implement OAuth token lifecycle management (refresh, revoke, rotate).
- [ ] Add webhook ingestion and verification for integrations.
- [ ] Build integration health dashboards and alerting hooks.
- [ ] Implement marketplace discovery/registry listing.
- [ ] Add usage analytics and quota tracking.
- [ ] Document integration lifecycle management.
References:
- F&F.md
- src/modules/integrations/
Dependencies: None
Effort: L

### T-103: Build job lifecycle APIs, queue integration, and observability
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F shows missing job lifecycle APIs, scheduling/retry policies, queue integration, metrics, dead-letter handling, priority/SLA config, and audit trails.
- Job infrastructure is required for reliable background processing.
Acceptance Criteria:
- [ ] Implement job lifecycle API endpoints and serializers.
- [ ] Add scheduling and retry policy management.
- [ ] Integrate job queue/worker execution backend.
- [ ] Implement metrics/observability dashboards and logging.
- [ ] Add dead-letter handling, priority, SLA configuration.
- [ ] Add audit trail records for job execution.
- [ ] Document job processing workflows.
References:
- F&F.md
- src/modules/jobs/
Dependencies: None
Effort: L

### T-104: Implement orchestration workflow APIs, triggers, and admin UI
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing orchestration APIs, workflow definitions/versioning, triggers, observability, retries, access controls, and admin UI.
- Orchestration is foundational for cross-module workflows.
Acceptance Criteria:
- [ ] Add orchestration workflow API endpoints and serializers.
- [ ] Implement workflow definitions, versioning, and storage.
- [ ] Add event-driven triggers and execution hooks.
- [ ] Implement observability/tracing and error handling with retries.
- [ ] Add access controls and admin UI for workflow management.
- [ ] Document orchestration configuration and governance.
References:
- F&F.md
- src/modules/orchestration/
Dependencies: None
Effort: L

### T-105: Enhance email ingestion with attachments, spam filtering, and reporting
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F flags missing attachment processing, spam filtering, and analytics for email ingestion.
- These are required for reliable inbound processing.
Acceptance Criteria:
- [ ] Implement attachment processing and storage pipeline.
- [ ] Add spam filtering and quarantine handling.
- [ ] Build email ingestion analytics/reporting dashboards.
- [ ] Document email ingestion workflows and controls.
References:
- F&F.md
- src/modules/email_ingestion/
Dependencies: None
Effort: M

### T-106: Add firm settings UI, data residency, and compliance reporting
Priority: P2
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F indicates missing firm org settings UI, data residency, compliance dashboards, and analytics.
- Firm governance features are necessary for enterprise readiness.
Acceptance Criteria:
- [ ] Implement org-level settings UI and API endpoints.
- [ ] Add multi-region data residency configuration and enforcement.
- [ ] Build compliance reporting dashboards.
- [ ] Add firm-level analytics and KPI dashboards.
- [ ] Document firm governance workflows.
References:
- F&F.md
- src/modules/firm/
Dependencies: None
Effort: L

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

### T-107: Build asset management APIs, storage pipeline, and governance controls
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing asset CRUD APIs, upload/storage pipeline, CDN delivery, metadata search, versioning, access controls, transforms, and audit/retention policies.
- Asset management is foundational but not currently exposed beyond models/admin.
Acceptance Criteria:
- [ ] Implement asset CRUD API endpoints and serializers.
- [ ] Build upload pipeline and storage abstraction.
- [ ] Add CDN delivery integration for asset serving.
- [ ] Implement metadata tagging/search and versioning/history.
- [ ] Add access controls/sharing policies and transformation workflows.
- [ ] Implement audit trails and retention policies for assets.
- [ ] Document asset governance and storage behavior.
References:
- F&F.md
- src/modules/assets/
Dependencies: None
Effort: L

### T-108: Add knowledge search, approval workflows, and analytics
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F flags missing knowledge search, approval/versioning, analytics, access controls, and import/export.
- Knowledge scalability requires discoverability and governance.
Acceptance Criteria:
- [ ] Implement search and semantic retrieval for knowledge articles.
- [ ] Add versioning and approval workflows.
- [ ] Build knowledge analytics dashboards.
- [ ] Add access controls and sharing policies.
- [ ] Implement content import/export tooling.
- [ ] Document knowledge governance workflows.
References:
- F&F.md
- src/modules/knowledge/
Dependencies: None
Effort: L

### T-109: Implement communications multi-channel delivery, templates, and analytics
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing multi-channel support, templates, delivery tracking, scheduling, threading, permissions, spam handling, and analytics.
- Communication workflows need core delivery infrastructure and governance.
Acceptance Criteria:
- [ ] Add multi-channel delivery support (email/SMS/push).
- [ ] Implement template management and message rendering.
- [ ] Add delivery tracking, scheduling/queueing, and threading support.
- [ ] Implement permissions/privacy controls and spam/abuse handling.
- [ ] Build analytics and engagement reporting dashboards.
- [ ] Document communications workflows and policies.
References:
- F&F.md
- src/modules/communications/
Dependencies: None
Effort: L

### T-110: Add tracking governance, stitching, retention controls, and exports
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F shows missing tracking taxonomy governance, session stitching, retention controls, dashboards, and export hooks.
- Analytics reliability depends on consistent taxonomy and retention policies.
Acceptance Criteria:
- [ ] Define event taxonomy governance and enforcement rules.
- [ ] Implement session/user stitching logic.
- [ ] Add data retention controls and privacy policy alignment.
- [ ] Build analytics dashboards for tracking insights.
- [ ] Implement export and integration hooks.
- [ ] Document tracking governance and retention policies.
References:
- F&F.md
- src/modules/tracking/
Dependencies: None
Effort: M

### T-111: Add reconciliation dashboards and alerting for accounting integrations
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F notes missing reconciliation dashboards and error alerting for accounting integrations.
- Operational visibility is required for reliable accounting syncs.
Acceptance Criteria:
- [ ] Build reconciliation dashboards for accounting integrations.
- [ ] Implement error alerting/observability integration for sync failures.
- [ ] Document reconciliation workflows and alerting expectations.
References:
- F&F.md
- src/modules/accounting_integrations/
Dependencies: None
Effort: M

### T-112: Implement ad sync scheduling policies and performance dashboards
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing scheduling/cron policy management, error reporting, and campaign performance dashboards.
- Ad sync reliability depends on scheduling and visibility.
Acceptance Criteria:
- [ ] Add scheduling/cron policy management for ad sync runs.
- [ ] Implement error reporting and retry analytics.
- [ ] Build campaign performance dashboards for synced ad data.
- [ ] Document ad sync scheduling and reporting workflows.
References:
- F&F.md
- src/modules/ad_sync/
Dependencies: None
Effort: M

### T-113: Build delivery scheduling, SLA tracking, and reporting
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F flags missing delivery APIs, scheduling, status tracking, retry handling, notifications, audit trails, reporting, and integration hooks.
- Delivery workflows need operational visibility and reliability guarantees.
Acceptance Criteria:
- [ ] Implement delivery API endpoints and serializers.
- [ ] Add delivery scheduling and SLA tracking.
- [ ] Implement status tracking, retry/failure handling, and notifications.
- [ ] Add audit trails and reporting dashboards.
- [ ] Implement integration hooks for communications/webhooks.
- [ ] Document delivery workflows.
References:
- F&F.md
- src/modules/delivery/
Dependencies: None
Effort: L

### T-114: Add onboarding templates, document collection, and progress dashboards
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing guided checklists, document collection, dashboards, reminders, and role-based approvals.
- Onboarding experience relies on guided templates and progress visibility.
Acceptance Criteria:
- [ ] Implement guided checklist templates for onboarding.
- [ ] Add document collection and validation workflows.
- [ ] Build client progress dashboards.
- [ ] Add automated reminders and role-based approvals.
- [ ] Document onboarding workflows and roles.
References:
- F&F.md
- src/modules/onboarding/
Dependencies: None
Effort: M

### T-115: Expand pricing with promotions, versioning, and analytics
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F highlights missing discounting/promotions, price versioning/audit trails, and analytics dashboards.
- Pricing governance requires versioning and auditability.
Acceptance Criteria:
- [ ] Implement discounting and promotions engine.
- [ ] Add price versioning and audit trails.
- [ ] Build pricing analytics dashboards.
- [ ] Document pricing governance workflows.
References:
- F&F.md
- src/modules/pricing/
Dependencies: None
Effort: M

### T-116: Add recurrence APIs, UI configuration, and validation tooling
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing recurrence APIs, UI configuration, exceptions, timezone handling, analytics, validation, and versioning.
- Recurrence reliability depends on validation and timezone support.
Acceptance Criteria:
- [ ] Implement recurrence rule API endpoints and serializers.
- [ ] Add UI configuration workflows for recurrence rules.
- [ ] Implement exception handling and overrides.
- [ ] Add timezone-aware recurrence rules.
- [ ] Build recurrence analytics and validation tooling.
- [ ] Add versioning/audit trails for recurrence rules.
- [ ] Document recurrence configuration and governance.
References:
- F&F.md
- src/modules/recurrence/
Dependencies: None
Effort: L

### T-117: Add SMS templates, scheduling, and delivery analytics
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F indicates missing SMS template library, scheduling/queueing, and analytics dashboards.
- SMS workflows need content governance and reporting.
Acceptance Criteria:
- [ ] Implement SMS template library and rendering.
- [ ] Add scheduling/queueing support for SMS sends.
- [ ] Build delivery analytics dashboards.
- [ ] Document SMS workflows and reporting.
References:
- F&F.md
- src/modules/sms/
Dependencies: None
Effort: M

### T-118: Add snippet versioning, tagging, analytics, and sharing controls
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F lists missing snippet versioning, tagging, analytics, access controls, and import/export.
- Snippet governance requires versioning and access controls.
Acceptance Criteria:
- [ ] Implement snippet versioning and history tracking.
- [ ] Add categorization/tagging and bulk import/export.
- [ ] Implement usage analytics dashboards.
- [ ] Add access controls and sharing policies.
- [ ] Document snippet governance workflows.
References:
- F&F.md
- src/modules/snippets/
Dependencies: None
Effort: M

### T-119: Expand support workflows with SLAs, routing, and CSAT
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F flags missing SLA management, routing/escalation, knowledge integration, CSAT surveys, and analytics.
- Support effectiveness depends on routing and customer feedback loops.
Acceptance Criteria:
- [ ] Implement SLA management and priority rules.
- [ ] Add ticket routing and escalation workflows.
- [ ] Integrate knowledge base linking with support tickets.
- [ ] Implement customer satisfaction surveys.
- [ ] Build support analytics dashboards.
- [ ] Document support workflows and reporting.
References:
- F&F.md
- src/modules/support/
Dependencies: None
Effort: M

### T-120: Define unified permissions and policy management across modules
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F cross-module assessment flags unified permissions/policy management as a potential gap.
- Consistent authorization reduces drift and security risk across modules.
Acceptance Criteria:
- [ ] Inventory module-level permission checks and policy definitions.
- [ ] Define a unified permissions/policy management strategy.
- [ ] Implement shared policy utilities and enforcement hooks.
- [ ] Document cross-module authorization standards.
References:
- F&F.md
- src/modules/
Dependencies: None
Effort: M

### T-121: Standardize audit trails and compliance reporting for regulated workflows
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F cross-module assessment notes missing audit trails/compliance reporting for regulated workflows.
- Finance, documents, and e-signature require consistent auditability.
Acceptance Criteria:
- [ ] Define audit trail requirements for regulated workflows.
- [ ] Implement audit trail storage and reporting across finance, documents, and esignature.
- [ ] Build compliance reporting dashboards or exports.
- [ ] Document audit trail standards.
References:
- F&F.md
- src/modules/finance/
- src/modules/documents/
- src/modules/esignature/
Dependencies: None
Effort: L

### T-122: Validate API coverage gaps across modules lacking endpoints
Priority: P3
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F highlights inconsistent API coverage for modules without urls/views at module level.
- Ensuring API coverage is required for product completeness.
Acceptance Criteria:
- [ ] Inventory modules missing API endpoints (urls.py/views.py).
- [ ] Confirm or create tasks for missing API coverage per module.
- [ ] Document API coverage status in module docs.
References:
- F&F.md
- src/modules/
Dependencies: None
Effort: S

### T-123: Define AI/LLM integration layer requirements
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F cross-module assessment flags missing AI/LLM integration layer.
- AI assistance requires infrastructure for prompts, embeddings, and governance.
Acceptance Criteria:
- [ ] Define AI/LLM integration scope and target use cases.
- [ ] Document required infrastructure (providers, storage, privacy controls).
- [ ] Create implementation plan and module integration points.
References:
- F&F.md
- src/modules/
Dependencies: None
Effort: M

### T-124: Audit mobile/portal UX flows for coverage gaps
Priority: P3
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F cross-module assessment notes potential gaps in mobile/portal-specific UX flows.
- UI coverage must be validated against module capabilities.
Acceptance Criteria:
- [ ] Inventory mobile/portal routes and corresponding backend coverage.
- [ ] Identify missing UX flows and create follow-up tasks.
- [ ] Document UX coverage in relevant frontend docs.
References:
- F&F.md
- src/frontend/
Dependencies: None
Effort: S

### T-125: Define centralized notification and messaging strategy
Priority: P3
Type: FEATURE
Owner: AGENT
Status: READY
Blocker: None.
Context:
- F&F cross-module assessment notes missing centralized notification/messaging strategy across communications, sms, and email.
- Consistent messaging reduces duplication and policy drift.
Acceptance Criteria:
- [ ] Define centralized notification strategy and message types.
- [ ] Map module notification needs to communications/sms/email services.
- [ ] Document notification standards and delivery rules.
References:
- F&F.md
- src/modules/communications/
- src/modules/sms/
- src/modules/email_ingestion/
Dependencies: None
Effort: M

## Backlog
<!-- Add future tasks here. -->

## Notes
- No automation is allowed to rewrite this file.
- Optional scripts may generate `TODO.generated.md` for convenience; it is never authoritative.
