# P2TODO.md - Repository Task List

Document Type: Workflow
Last Updated: 2026-01-21
Task Truth Source: **P2TODO.md**
Other Priority Files: P0TODO.md, P1TODO.md, P3TODO.md

<!--
Meta-commentary:
  - Current Status: Authoritative task list; T-127, T-135, T-137, and T-138 moved to TODOCOMPLETED.md.
  - Mapping: Mirrors completed work recorded in TODOCOMPLETED.md and CHANGELOG.md.
- Reasoning: Keep task truth source accurate after completion.
- Assumption: Tasks are appended/moved manually with auditability in mind.
- Limitation: This file does not capture execution details beyond acceptance criteria.
-->

This file is the single source of truth for P2 tasks.
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
#### P2 — Important (do within 30 days)
### T-139: Add pagination to all DRF ViewSets (REFACTOR Phase 3)
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 3 Item 1 - Fix performance issues
- List endpoints lack pagination causing memory exhaustion
- FORENSIC_AUDIT.md Issue #4.2 - Missing pagination
Acceptance Criteria:
- [ ] Add pagination_class = PageNumberPagination to all DRF ViewSets
- [ ] Set max page size to 100 items
- [ ] Add pagination tests for all list endpoints
- [ ] Verify pagination in API responses (count, next, previous fields)
- [ ] Document pagination in API documentation
References:
- REFACTOR_PLAN.md:261-265, 859-868
- FORENSIC_AUDIT.md Issue #4.2
Dependencies: None
Effort: M

### T-143: Optimize invoice total calculation (REFACTOR Phase 3)
Priority: P2
Type: QUALITY
Owner: AGENT
Status: READY
Blocker: None
Context:
- REFACTOR_PLAN.md Phase 3 Item 5 - Fix performance issues
- Invoice total recalculated O(n) on every access
- Hot path causing performance degradation
- FORENSIC_AUDIT.md Issue #4.7
Acceptance Criteria:
- [ ] Add denormalized total field to Invoice model in src/modules/finance/models.py
- [ ] Create database trigger or signal to update total on line item changes
- [ ] Migrate existing invoices to populate total field
- [ ] Add tests for total calculation accuracy
- [ ] Benchmark performance improvement
References:
- REFACTOR_PLAN.md:282-285
- FORENSIC_AUDIT.md Issue #4.7
- src/modules/finance/models.py
Dependencies: None
Effort: M

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

### T-084: Add Lighthouse CI for frontend performance
Priority: P2
Type: QUALITY
Owner: AGENT
Status: IN-REVIEW
Blocker: None.
Context:
- Frontend performance lacks automated verification.
Acceptance Criteria:
- [x] Add Lighthouse CI configuration for frontend performance.
- [x] Document how to run Lighthouse CI locally.
References:
- src/frontend/
- Diamond Standard Plan Phase 8
Dependencies: None
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
