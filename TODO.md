# ConsultantPro - Current Work & Roadmap

**Last Updated:** December 30, 2025

---

## ✅ Doc-Driven Roadmap (Canonical; docs/1–docs/35)

Docs 1–35 are the source of truth for platform scope, invariants, and required subsystems.
Any legacy roadmap/checklist items below are retained for history only and MUST NOT drive prioritization.

### Prioritized Next Work (Top 18)

- [x] DOC-17.1 Resolve repo-structure delta vs docs/17 (document the intentional differences; keep boundaries explicit) ✅ Completed Dec 29, 2025 - see docs/repo-structure-delta.md
- [x] DOC-04.1 Resolve tenancy contradiction: docs require schema-per-tenant; code is firm-scoped row tenancy (choose + update invariants accordingly) ✅ Completed Dec 29, 2025 - ADR-0010 in docs/4 documents row-level tenancy as canonical
- [x] DOC-18.1 Map every API endpoint to canonical actions + enforce server-side authorization consistently (staff RBAC + portal scopes) ✅ Completed Dec 29, 2025 - see docs/API_ENDPOINT_AUTHORIZATION_MAPPING.md; fixed PaymentViewSet authorization
- [x] DOC-07.1 Implement governance classification registry + serializer/log/export redaction (no HR data in logs) ✅ Completed Dec 29, 2025 - see src/modules/core/governance.py, serializer_mixins.py, logging_utils.py
- [x] DOC-14.1 Documents: enforce governed artifact invariants (versioning is canonical; no unmanaged blob paths) ✅ Completed Dec 29, 2025 - added status, classification fields to Document; checksum, virus_scan_status to Version
- [x] DOC-14.2 Documents: add access logging for URL issuance + downloads/uploads (auditable, metadata-only) ✅ Completed Dec 29, 2025 - added DocumentAccessLog model with log_access() method
- [x] DOC-14.3 Documents: implement locking + admin override audit + portal download policy when scan is pending/flagged ✅ Completed Dec 29, 2025 - added DocumentLock model with override tracking and can_upload() method
- [x] DOC-33.1 Communications: Conversation/Participant/Message model with visibility rules + attachments as governed documents ✅ Completed Dec 29, 2025 - added modules/communications/ with Conversation, Participant, Message, MessageAttachment, MessageRevision, ConversationLink models
- [x] DOC-09.1 Pricing engine MVP: versioned RuleSets + evaluator + deterministic outputs + trace ✅ Completed Dec 29, 2025 - added modules/pricing/ with RuleSet, Quote, QuoteVersion, QuoteLineItem models; PricingEvaluator with deterministic evaluation + trace generation
- [x] DOC-09.2 Quote snapshots: immutable QuoteVersion persistence + retrieval endpoints for audit ✅ Completed Dec 30, 2025 - added API endpoints with audit logging for quote version retrieval; enforced immutability for accepted quotes
- [x] DOC-12.1 Delivery templates MVP: template DAG validation + deterministic instantiation into execution units ✅ Completed Dec 30, 2025 - added modules/delivery with DeliveryTemplate, DeliveryNode, DeliveryEdge models; DAG cycle detection; deterministic instantiation engine; template traceability in Task model
- [x] DOC-10.1 Recurrence engine MVP: RecurrenceRule + PeriodKey policy + RecurrenceGeneration dedupe ledger + DST correctness ✅ Completed Dec 30, 2025 - added modules/recurrence with RecurrenceRule, RecurrenceGeneration models; RecurrenceGenerator with timezone-aware period computation; DST handling; idempotency keys; unique constraints for dedupe
- [x] DOC-11.1 Orchestration engine MVP: executions + step history + retry/DLQ model + per-step idempotency strategy ✅ Completed Dec 30, 2025 - added modules/orchestration with OrchestrationDefinition, OrchestrationExecution, StepExecution, OrchestrationDLQ models; OrchestrationExecutor with error classification, retry logic, backoff strategies, DLQ routing
- [x] DOC-15.1 Email ingestion MVP: EmailArtifact + attachment storage as Documents + mapping suggestions + triage + audited remaps ✅ Completed Dec 30, 2025 - added modules/email_ingestion with EmailConnection, EmailArtifact, EmailAttachment, IngestionAttempt models; EmailMappingService with confidence scoring; EmailIngestionService with idempotent ingestion; triage workflow with audit events
- [x] DOC-34.1 Calendar domain MVP: appointment types + availability profiles + booking links + booking flow ✅ Completed Dec 30, 2025 - added modules/calendar with AppointmentType, AvailabilityProfile, BookingLink, Appointment, AppointmentStatusHistory models; AvailabilityService with DST-aware slot calculation; RoutingService with multiple routing policies; BookingService with race condition protection; comprehensive test suite covering buffers, DST transitions, and approval flows
- [x] DOC-16.1 Calendar sync MVP: stable external IDs + SyncAttemptLog + reconciliation rules + manual resync tooling ✅ Completed Dec 30, 2025 - added CalendarConnection and SyncAttemptLog models; CalendarSyncService with idempotent pull/push operations; ResyncService with manual resync tooling; unique constraint on (connection_id, external_event_id); timezone-aware event parsing; audit logging for time changes and resync requests
- [x] DOC-22.1 Add contract tests mandated by docs (pricing/permissions/recurrence/orchestration/billing/documents) ✅ Completed Dec 30, 2025 - added src/tests/contract_tests.py with comprehensive contract tests for pricing determinism, recurrence DST/leap-year correctness and dedupe, orchestration retry matrix and DLQ routing, document versioning/locking/portal visibility/access logging, billing ledger idempotency and allocation constraints, permissions allow/deny matrix
- [ ] DOC-21.1 Observability baseline: correlation IDs end-to-end; tenant-safe metrics; DLQ + integration lag visibility

### Doc-Driven Backlog (All Canonical Requirements)

**Foundations**
- [ ] DOC-05.1 Align system invariants in code with SYSTEM_SPEC (authority rules, idempotency expectations, auditability)
- [ ] DOC-06.1 Implement canonical core object graph (Account/Contact/Engagement/EngagementLine/WorkItem) or explicitly map current models to it and close gaps
- [ ] DOC-19.1 Provisioning + migrations per DB_SCHEMA_AND_MIGRATIONS (idempotent tenant provisioning workflow; migration runner logs)
- [ ] DOC-24.1 Security model minimums: secrets handling, rate limiting for portal, IDOR hardening, input validation for external content

**Billing (Ledger-First)**
- [ ] DOC-13.1 Ledger entry immutability + idempotency keys for posting APIs (unique constraints per spec)
- [ ] DOC-13.2 Implement allocations model + constraints (partial/over/under payments; retainer apply semantics; compensating entries)

**Governed Artifacts**
- [ ] DOC-14.4 Malware scan hook interface + recording scan status on versions + policy enforcement (portal vs staff)
- [ ] DOC-07.2 Retention/anonymization/erasure workflows consistent with DATA_GOVERNANCE (and audited)

**Engines**
- [ ] DOC-09.3 Ruleset publishing immutability + checksum enforcement + compatibility checks for schema versions
- [ ] DOC-12.2 Template publish immutability + instantiation audit trail + node traceability
- [ ] DOC-10.2 Recurrence pause/resume/cancel semantics without duplicates; backfill windows; deterministic as_of time
- [ ] DOC-11.2 Orchestration compensation boundaries + error classes aligned with retry matrix

**Integrations**
- [ ] DOC-15.2 IngestionAttempt logs + retry-safety + staleness heuristics; correction workflow is auditable
- [ ] DOC-16.2 Admin-gated resync tooling endpoints + replay of failed attempts (audited)

**Platform Blueprints / Quality**
- [ ] DOC-20.1 Workers/queues payload rules (tenant_id/correlation_id/idempotency_key) + concurrency locks + DLQ reprocessing
- [ ] DOC-21.2 No-content logging guarantees + PII minimization in telemetry
- [ ] DOC-23.1 Implement edge-case coverage from EDGE_CASES_CATALOG (DST, idempotency collisions, portal multi-account)

**Product Surface Maps**
- [ ] DOC-25.1 Staff app IA alignment: ensure route/modules exist or explicitly defer; keep permissions consistent
- [ ] DOC-26.1 Client portal IA alignment: account switcher behavior + scope gating; core flows (messages/uploads/booking/pay)
- [ ] DOC-27.1 Role-based default visibility + least privilege defaults for staff roles + portal scopes

**Additional Modules**
- [ ] DOC-35.1 Knowledge system MVP: KnowledgeItem + publishing/deprecation workflow + access control + audit

---

## 🗃️ Legacy Roadmap (Superseded by docs/1–docs/35)

The sections below are preserved for historical context only.
Do not update or prioritize legacy Tier/checklist items; add new work above as DOC-* items.

## 🎯 Current Focus: Tier 5 - Durability, Scale & Exit

**Tier 4 Status:** 100% Complete ✅

### Recently Completed (Tier 4)

- [x] **4.1** Enforce billing invariants ✅
- [x] **4.2** Package fee invoicing (Complete - see docs/tier4/PACKAGE_INVOICE_DEPLOYMENT.md) ✅
- [x] **4.3** Hourly billing with approval gates ✅
- [x] **4.4** Mixed billing reporting ✅
- [x] **4.5** Credit ledger ✅
- [x] **4.6** Recurring payments/autopay workflow (Complete - see docs/tier4/AUTOPAY_STATUS.md) ✅
- [x] **4.7** Payment failures, disputes, and chargebacks (Complete - see docs/tier4/PAYMENT_FAILURE_STATUS.md) ✅
- [x] **4.8** Renewal billing behavior ✅

---

## 🟢 Completed Tiers

### Tier 4: Billing & Monetization (100% Complete) ✅
- [x] 4.1: Enforce billing invariants
- [x] 4.2: Package fee invoicing
- [x] 4.3: Hourly billing with approval gates
- [x] 4.4: Mixed billing reporting
- [x] 4.5: Credit ledger
- [x] 4.6: Recurring payments/autopay workflow
- [x] 4.7: Payment failures, disputes, and chargebacks
- [x] 4.8: Renewal billing behavior

### Tier 0: Foundational Safety (100% Complete) ✅
- [x] Firm/Workspace tenancy
- [x] Firm context resolution
- [x] Firm + client scoping everywhere
- [x] Portal containment
- [x] Platform privacy enforcement (E2EE deferred - infrastructure dependency)
- [x] Break-glass audit records (fully integrated with Tier 3 audit system)

### Tier 1: Schema Truth & CI Truth (100% Complete) ✅
- [x] Fix deterministic backend crashes
- [x] Commit all missing migrations
- [x] Make CI honest
- [x] Add minimum safety test set

### Tier 2: Authorization & Ownership (100% Complete) ✅
- [x] Standardize permissions across all ViewSets
- [x] Replace direct User imports with AUTH_USER_MODEL
- [x] Add firm + client context to all async jobs
- [x] Firm-scoped querysets (zero global access)
- [x] Portal authorization (client-scoped, explicit allowlist)
- [x] Cross-client access within Organizations

### Tier 3: Data Integrity & Privacy (100% Complete) ✅
- [x] Purge semantics (tombstones, metadata retention)
- [x] Audit event taxonomy + retention policy
- [x] Audit review ownership and cadence
- [x] Privacy-first support workflows
- [x] Document signing lifecycle & evidence retention

---

## 🔜 Next: Tier 5 - Durability, Scale & Exit

### Upcoming Tasks (Not Yet Started)

- [x] **5.1** Hero workflow integration tests
- [x] **5.2** Performance safeguards (tenant-safe at scale)
- [x] **5.3** Firm offboarding + data exit flows
- [x] **5.4** Configuration change safety
- [x] **5.5** Operational observability (without content)

---

## 📋 Missing & Partially Implemented Features Checklist

**Prioritized by Implementation Complexity (Simple → Complex)**

**For detailed information on each feature, see [Platform Capabilities Inventory](docs/03-reference/platform-capabilities.md)**

### ✅ Simple - Core Model Enhancements (Quick Wins)

- [x] 1.1 Add computed lead scoring field with basic calculation logic (CRM)
- [x] 1.2 Add configurable pipeline stages with validation (CRM) *(hardcoded stages implemented)*
- [x] 1.3 Add task dependencies field and basic dependency checking (Projects)
- [x] 1.4 Add milestone tracking fields to projects (Projects)
- [x] 1.5 Add expense tracking model with billable flag (Finance/Projects)
- [x] 1.6 Add retainer balance tracking to client model (Finance)
- [x] 1.7 Add document retention policy fields (Documents)
- [x] 1.8 Add legal hold flag to documents (Documents)
- [x] 1.9 Add WIP (Work in Progress) tracking fields (Finance)
- [x] 1.10 Add activity type enum and activity timeline model (CRM)

### 🟡 Medium - Workflow & Business Logic

- [x] 2.1 Implement Contract → Project creation workflow (CRM → Projects) ✅
- [x] 2.2 Add project template system with cloning (Projects) ✅
- [x] 2.3 Implement milestone-triggered invoice generation (Finance) ✅
- [x] 2.4 Add basic approval workflow for expenses (Finance) ✅
- [x] 2.5 Add AP bill state machine (Received → Validated → Approved → Paid) (Finance) ✅
- [x] 2.6 Implement dunning workflow for overdue invoices (Finance) ✅
- [ ] 2.7 Add document approval workflow (Draft → Review → Approved → Published) (Documents)
- [ ] 2.8 Add client acceptance gate before invoicing (Projects/Finance)
- [ ] 2.9 Implement utilization tracking and reporting (Projects)
- [ ] 2.10 Add cash application matching (partial/over/under payments) (Finance)

### 🟠 Complex - New Subsystems & Integrations

- [ ] 3.1 Build Account & Contact relationship graph (CRM)
- [ ] 3.2 Implement resource planning & allocation system (Projects)
- [ ] 3.3 Add profitability reporting with margin analysis (Finance)
- [ ] 3.4 Build intake form system with qualification logic (CRM)
- [ ] 3.5 Implement CPQ (Configure-Price-Quote) engine (CRM)
- [ ] 3.6 Add Gantt chart/timeline view for projects (Projects)
- [ ] 3.7 Build general webhook platform (Integration)
- [ ] 3.8 Add email/calendar sync integration (Integration)
- [ ] 3.9 Implement document co-authoring with real-time collaboration (Documents)
- [ ] 3.10 Add secure external document sharing with permissions (Documents)

### 🔴 Advanced - Enterprise Features

- [ ] 4.1 Implement SSO/OAuth (Google/Microsoft) authentication (IAM)
- [ ] 4.2 Add SAML support for enterprise SSO (IAM)
- [ ] 4.3 Implement Multi-Factor Authentication (MFA) (IAM)
- [ ] 4.4 Build RBAC/ABAC policy system with object-level permissions (IAM)
- [ ] 4.5 Add QuickBooks Online integration (Integration)
- [ ] 4.6 Add Xero accounting integration (Integration)
- [ ] 4.7 Implement e-signature integration (DocuSign/HelloSign) (Integration)
- [ ] 4.8 Build general automation/workflow engine with rule builder (Automation)
- [ ] 4.9 Add API versioning strategy and backward compatibility (API)
- [ ] 4.10 Implement materialized views for reporting performance (Reporting)

### 🎯 Strategic - Platform Transformation

- [ ] 5.1 Build unified event bus for cross-module automation (Platform)
- [ ] 5.2 Implement SCIM provisioning for automated user management (IAM)
- [ ] 5.3 Add audit review UI with query/filter/export capabilities (Compliance)
- [ ] 5.4 Build integration marketplace scaffolding (Platform)
- [ ] 5.5 Implement records management system with immutability (Compliance)
- [ ] 5.6 Add operational observability without content access (Platform)
- [ ] 5.7 Build custom dashboard builder with widget system (Reporting)
- [ ] 5.8 Implement ERP connectors for enterprise customers (Integration)
- [ ] 5.9 Add AI-powered lead scoring and sales automation (CRM)
- [ ] 5.10 Build comprehensive PSA operations suite (Planning/Analytics)

---

### 📝 Implementation Notes

**Execution Strategy:**
1. Start with Simple features (1.1-1.10) - Low risk, immediate value
2. Progress to Medium features (2.1-2.10) - Build on existing foundations
3. Tackle Complex features (3.1-3.10) - New capabilities, higher ROI
4. Consider Advanced features (4.1-4.10) - Enterprise requirements
5. Plan Strategic features (5.1-5.10) - Long-term platform evolution

**Current Focus:** Complete Tier 5 first, then begin Simple checklist items.

---

## 📋 Legacy Roadmap Summary

### High Priority (Post-Tier 5)

1. **Identity & Access Management**
   - SSO/OAuth (Google/Microsoft), SAML, MFA, Advanced RBAC

2. **Integration Framework**
   - Webhook platform, Email/calendar sync, Accounting integrations, E-signature

3. **Automation Engine**
   - Rule-based workflows, Event-driven triggers, Approval routing

### Medium Priority

4. **CRM Enhancements** - Activities timeline, Pipeline governance, Lead scoring
5. **Project Management** - Dependencies, Resource allocation, Gantt charts
6. **Document Management** - Version control, Workflow automation, External collaboration

### Lower Priority

7. **Reporting & Analytics** - Custom dashboards, Materialized views, Export scheduling
8. **AP/AR Automation** - Bill capture, Collections & dunning, Cash application
9. **Practice Operations** - Resource planning, Utilization tracking, Profitability analysis

---

## ⚠️ Current Blockers

None - All tier work proceeding normally.

---

## 🚨 Critical Rules

1. **No tier may be skipped** - Complete each tier in order
2. **No tier may be partially completed** - Finish all tasks before moving on
3. **All changes preserve tenant isolation** - Security is non-negotiable
4. **CI must never lie** - Test failures must fail the build

---

## 📖 Reference

- **Tier Details:** [Tier System Reference](docs/03-reference/tier-system.md)
- **Activity Log:** [Activity Log](docs/03-reference/activity-log.md)
- **System Invariants:** [System Invariants](spec/SYSTEM_INVARIANTS.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
