# System Specification (SYSTEM_SPEC)

This document is the consolidated, normative specification for the UBOS platform.

Normative keywords:
- MUST / MUST NOT: binding requirements
- SHOULD / SHOULD NOT: strongly recommended; deviations require explicit justification
- MAY: optional

Explanatory material is included, but where conflicts arise, the normative statements govern.

This spec defines:
- system boundaries
- core concepts and invariants
- cross-domain contracts
- authority rules (who decides what)
- safety requirements (idempotency, auditability, permission enforcement)

Related docs:
- ARCHITECTURE_OVERVIEW.md (explanatory mental model)
- DOMAIN_MODEL.md (entity/state machine reference)
- PERMISSIONS_MODEL.md (authorization rules)
- DATA_GOVERNANCE.md (PII, retention, erasure)
- PRICING_ENGINE_SPEC.md
- RECURRENCE_ENGINE_SPEC.md
- ORCHESTRATION_ENGINE_SPEC.md
- DELIVERY_TEMPLATES_SPEC.md
- BILLING_LEDGER_SPEC.md
- DOCUMENTS_AND_STORAGE_SPEC.md
- EMAIL_INGESTION_SPEC.md
- CALENDAR_SYNC_SPEC.md
- API_CONTRACTS.md, DB_SCHEMA_AND_MIGRATIONS.md, WORKERS_AND_QUEUES.md, TEST_STRATEGY.md

---

## 1) System goals and non-goals

### 1.1 Goals
1. The platform MUST support a professional-services firm running end-to-end operations across CRM, engagements, delivery, documents, communications, calendar, and billing with auditability.
2. The platform MUST support external client participation via a permission-gated portal.
3. The platform MUST be resilient under retries, concurrency, and partial failures (integrations, workers, network).

### 1.2 Non-goals (for V1 unless explicitly added)
1. The platform is NOT required to replace the firm’s general ledger or tax filing software.
2. The platform is NOT required to provide general-purpose file sharing as a replacement for consumer storage tools; it must provide governed artifacts within this system.
3. The platform is NOT required to be a full marketing automation suite; CRM automation may exist but must be bounded and explicit.

---

## 2) Architecture boundaries and authority rules

### 2.1 Two apps + one brain
1. The system MUST consist of a Staff App, Client Portal, and shared platform services (“the brain”).
2. The brain MUST be the authority for:
   - state transitions
   - permission evaluation
   - pricing evaluation + quote snapshotting
   - recurrence generation semantics
   - orchestration execution semantics
   - document governance (versioning/locking/access logging)
   - billing ledger correctness and idempotency

3. The UI MUST NOT be the authority for:
   - permissions (UI may only reflect server decisions)
   - billing balances (UI displays server-derived results)
   - state transitions (UI requests transitions; server validates)

### 2.2 Domain-core boundary
1. Domain logic MUST be expressible independently of persistence and UI.
2. `domain-core` (or equivalent) MUST NOT call the database directly.
3. Side effects (email send, file upload, payment post, calendar sync) MUST be performed through explicit services/adapters and MUST be idempotent.

---

## 3) Tenancy and isolation

### 3.1 Tenancy model
1. The platform MUST use firm-scoped row-level isolation for tenant data. Every tenant-scoped model MUST have a `firm` ForeignKey.
2. All tenant-scoped queries MUST use `FirmScopedQuerySet` or equivalent enforcement to prevent cross-tenant data access.
3. Global/platform data (if any) MUST NOT contain tenant PII unless explicitly justified and governed in DATA_GOVERNANCE.md.

> **Note**: Schema-per-tenant was considered but row-level isolation was implemented for operational simplicity. See ADR-0010 in docs/03-reference/requirements/DOC-04.md.

### 3.2 Tenant provisioning
1. Tenant provisioning MUST be an explicit workflow with an auditable record.
2. Provisioning MUST include:
   - creating tenant identity (platform scope)
   - creating tenant schema
   - applying tenant migrations
   - seeding baseline configuration (roles, default templates, etc.) as defined in specs
3. Provisioning MUST be idempotent (safe to retry).

---

## 4) Canonical object graph and linking rules

### 4.1 Core object graph (canonical)
The canonical object graph is:
- Account
- Contact
- Engagement
- EngagementLine
- WorkItem

Normative requirements:
1. All cross-domain artifacts (documents, messages, appointments, invoices, ledger entries) MUST link to the canonical graph via explicit associations.
2. A WorkItem MUST belong to an Engagement OR to an EngagementLine (implementation may choose one as canonical), and the relationship MUST be consistent across the system.
3. If the system supports “pre-engagement” artifacts (intake drafts), they MUST be explicitly marked as such and MUST NOT be treated as active delivery objects.

### 4.2 Association integrity
1. Orphaned artifacts MUST be prevented by design:
   - Documents MUST be associated to at least one owning object (Account/Engagement/WorkItem/etc.) at creation time, or placed into a governed “Unassigned” intake bucket with explicit triage workflow.
   - Ingested email artifacts MUST be associated or triaged (see EMAIL_INGESTION_SPEC.md).
2. Deleting an owning object MUST follow governance rules (soft delete, retention, legal hold) and MUST NOT silently drop dependent audit artifacts.

---

## 5) Identity and access control (system-level)

### 5.1 Identity domains
1. The system MUST separate:
   - Staff identity (internal users)
   - Portal identity (external client contacts)
2. Staff identity MUST be governed by RBAC.
3. Portal identity MUST be constrained by:
   - explicit Contact association(s)
   - explicit Account association(s)
   - explicit scopes/permissions for portal-visible objects

### 5.2 Server-side enforcement
1. Every API mutation MUST enforce permissions server-side using PERMISSIONS_MODEL.md.
2. Every API read that returns tenant data MUST enforce permissions server-side.
3. “Filtering by UI” MUST NOT be considered access control.

### 5.3 Least privilege defaults
1. Default roles and portal scopes MUST follow least-privilege.
2. Any permission escalation MUST be auditable (who granted, when, what changed).

---

## 6) State machines and invariants (cross-domain)

State machines are defined in DOMAIN_MODEL.md, but the system-level invariants below are binding.

### 6.1 Engagement lifecycle
1. An Engagement MUST have an explicit status indicating whether it is active delivery work.
2. A QuoteVersion acceptance MUST be the only path (in V1) to activating an Engagement unless a documented admin override exists.
3. Activation MUST snapshot the relevant pricing/terms context (see PRICING_ENGINE_SPEC.md).

### 6.2 Work execution lifecycle
1. WorkItems MUST have explicit state.
2. Forbidden transitions MUST be enforced server-side.
3. Any automated transitions MUST be attributable (actor = user/system; correlation IDs required).

### 6.3 Appointment lifecycle
1. Appointments MUST have explicit state (requested/confirmed/canceled/etc.) and MUST support idempotent updates from sync.
2. External calendar changes MUST not silently rewrite internal meaning; reconciliation rules must be explicit (CALENDAR_SYNC_SPEC.md).

### 6.4 Billing lifecycle
1. All money-impacting operations MUST be represented as ledger entries (BILLING_LEDGER_SPEC.md).
2. Ledger posting APIs MUST be idempotent.
3. Derived balances (AR, retainer balance, earned revenue) MUST be explainable from ledger entries.

---

## 7) Engines: pricing, recurrence, orchestration, templates

### 7.1 Pricing engine
1. Pricing rules MUST be versioned.
2. A quote evaluation MUST produce:
   - outputs
   - a trace sufficient to explain the outputs
3. Accepted quotes MUST produce an immutable QuoteVersion snapshot.
4. The system MUST support retrieving the QuoteVersion and trace for audit.

### 7.2 Delivery templates
1. DeliveryTemplates MUST define the plan of work as a DAG (DELIVERY_TEMPLATES_SPEC.md).
2. Templates MUST be validated at creation/update time (acyclic, required fields, etc.).
3. Instantiation MUST produce WorkItems in a deterministic way (given the same inputs).

### 7.3 Recurrence engine
1. Recurrence generation MUST be idempotent and deduplicated via constraints (RECURRENCE_ENGINE_SPEC.md).
2. Timezone policy MUST be explicit and consistently applied.
3. Pause/resume/cancel MUST not duplicate already-generated work.

### 7.4 Orchestration engine
1. Orchestration MUST model executions and steps with retry semantics and DLQ.
2. Every step MUST have a defined idempotency strategy.
3. Compensation MUST be explicitly defined for any step that is not safely retryable.

---

## 8) Documents and storage (governed artifacts)

### 8.1 Storage adapter contract
1. The system MUST support an S3-compatible storage contract (DOCUMENTS_AND_STORAGE_SPEC.md).
2. Storage operations MUST be permission-gated and audited.

### 8.2 Versioning and locking
1. Documents MUST support versioning.
2. Locking MUST be supported for document types that require write coordination.
3. The system MUST log access and key write events (upload, new version, lock/unlock).

### 8.3 Secure access
1. Downloads and uploads MUST use signed URLs or equivalent secure mechanism.
2. Signed URL policies MUST enforce least privilege and short-lived access.
3. Malware scanning hooks MUST be supported (implementation may be deferred, but the interface must exist).

---

## 9) Communications and integrations (system-level)

### 9.1 Communications model (system requirement)
1. The system MUST support native conversation threads for staff↔staff and staff↔client communications.
2. Attachments in conversations MUST be governed documents (not opaque blobs without governance).
3. Communication access MUST be permission-gated and auditable.

Note: the detailed thread model, message types, and retention policies live in COMMUNICATIONS_SPEC.md (to be created).

### 9.2 Email ingestion
1. Email ingestion MUST store email artifacts and attachments as governed artifacts.
2. The system MUST provide mapping suggestions with confidence scoring and correction workflow.
3. The system MUST record ingest attempts and support safe retries.

### 9.3 Calendar sync
1. Calendar sync MUST be idempotent with stable external IDs.
2. Sync attempt logs MUST exist with retry behavior and manual resync tooling.

---

## 10) Data governance, auditability, and retention

### 10.1 PII and classification
1. The platform MUST classify PII and sensitive data as defined in DATA_GOVERNANCE.md.
2. PII handling MUST be consistent across apps, APIs, workers, and integrations.

### 10.2 Soft delete and retention
1. Soft delete MUST be the default for tenant data unless explicitly exempt.
2. Hard delete/anonymization MUST follow governed workflows (retention, legal hold, audit requirements).
3. Audit log records MUST follow retention rules and MUST be protected against tampering.

### 10.3 Audit event requirements
1. The system MUST record audit events for:
   - permission changes
   - role assignments
   - portal access grants/revocations
   - quote acceptance/changes
   - ledger posting
   - document access (at least download/view) and document writes
2. Audit events MUST include:
   - actor (user/system)
   - time
   - object references
   - correlation ID / request ID

---

## 11) Reliability requirements: idempotency, concurrency, and retries

### 11.1 Idempotency
1. Any API endpoint that creates side effects MUST support idempotency keys (or be provably idempotent by unique constraints).
2. All worker jobs MUST be idempotent.
3. Idempotency MUST be testable (TEST_STRATEGY.md) and include edge cases (EDGE_CASES_CATALOG.md).

### 11.2 Concurrency control
1. Workers that process shared queues MUST use a documented concurrency model (SKIP LOCKED, advisory locks, or equivalent).
2. Recurrence generation and orchestration MUST prevent duplicate work under concurrent execution.

### 11.3 Failure handling
1. Retries MUST follow an explicit retry matrix (ORCHESTRATION_ENGINE_SPEC.md / WORKERS_AND_QUEUES.md).
2. Dead-letter queues MUST exist for non-retryable failures.
3. DLQ reprocessing MUST be controlled and auditable.

---

## 12) Observability (minimum requirements)

1. Every request and job MUST have a correlation ID.
2. Logs MUST include:
   - tenant identifier
   - correlation ID
   - actor (when applicable)
   - primary object references
3. The system SHOULD expose metrics for:
   - job latency and failures by type
   - integration sync success/failure rates
   - API error rates and p95 latency by endpoint group
   - document operations (upload/download) counts and failures
4. Alert thresholds and dashboards MUST be defined in OBSERVABILITY_AND_SRE.md.

---

## 13) API design requirements (system-level)

1. APIs MUST be organized by domain boundaries and follow consistent pagination/filtering/sorting conventions (API_CONTRACTS.md).
2. Permission enforcement MUST follow a consistent pattern and be centralized or standardized.
3. Event emission (if used) MUST be consistent and documented (event catalog may be added).

---

## 14) Testing requirements (system-level)

1. The system MUST have unit tests for:
   - pricing evaluation determinism and trace correctness
   - permission evaluation correctness
   - recurrence period generation and dedupe behavior
   - ledger posting idempotency and allocation constraints

2. The system MUST have integration tests for:
   - tenant provisioning and migrations
   - ingestion/sync idempotency under retries
   - document versioning/locking behavior

3. Time-dependent logic MUST be tested with deterministic time control and explicit timezone tests.

---

## 15) Open questions and decision linkage

Any unresolved decision that affects invariants MUST be captured in:
- OPEN_QUESTIONS.md (short, with options and consequences)

Any accepted decision MUST be captured in:
- DECISION_LOG.md
and reflected here and/or in the appropriate canonical spec.

---

