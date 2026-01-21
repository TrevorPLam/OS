# P3TODO.md - Repository Task List

Document Type: Workflow
Last Updated: 2026-01-21
Task Truth Source: **P3TODO.md**
Other Priority Files: P0TODO.md, P1TODO.md, P2TODO.md

<!--
Meta-commentary:
  - Current Status: Authoritative task list; T-127, T-135, T-137, and T-138 moved to TODOCOMPLETED.md.
  - Mapping: Mirrors completed work recorded in TODOCOMPLETED.md and CHANGELOG.md.
- Reasoning: Keep task truth source accurate after completion.
- Assumption: Tasks are appended/moved manually with auditability in mind.
- Limitation: This file does not capture execution details beyond acceptance criteria.
-->

This file is the single source of truth for P3 tasks.
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

