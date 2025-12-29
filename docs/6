# Domain Model (DOMAIN_MODEL)

This document defines the canonical domain entities, relationships, and state machines for the platform.

It is a normative reference for:
- entity definitions and relationships
- state machines and allowed transitions
- key invariants and forbidden transitions

Cross-domain invariants and system-wide authority rules are defined in SYSTEM_SPEC.md. If this document conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Conventions

### 1.1 Tenancy
All entities in this document are tenant-scoped and live in the tenant schema unless explicitly labeled “platform/global.”

### 1.2 Identifiers
- Primary keys SHOULD be UUID/ULID (implementation choice), consistent across the system.
- External integrations MUST store stable external IDs (e.g., `external_event_id`) with uniqueness constraints scoped to the integration connection.

### 1.3 Standard fields (recommended)
Entities SHOULD include:
- `id`
- `created_at`, `updated_at`
- `created_by` (actor reference when applicable)
- `deleted_at` (soft delete)
- `version` (integer for optimistic concurrency where relevant)
- `metadata` (optional JSON for non-critical extensions, bounded by governance rules)

### 1.4 Actors
Actors come from two identity domains:
- StaffUser (internal identity)
- PortalIdentity (external identity mapped to a Contact)

Audit events MUST record the actor type and actor id.

---

## 2) Canonical object graph

The canonical core object graph is:
- Account
- Contact
- Engagement
- EngagementLine
- WorkItem

All other artifacts (documents, messages, appointments, invoices, ledger entries) MUST associate to this graph using explicit association entities/foreign keys.

---

## 3) Entity catalog

### 3.1 Account
Represents a client organization or client household/individual.

Key fields (typical):
- `name`
- `type` (enum: organization | individual | household; optional)
- `primary_contact_id` (nullable)
- `status` (enum: active | inactive | archived)
- `tags` (optional)
- `risk_profile` (optional reference to qualification/risk artifacts)

Relationships:
- Account 1—N Contact
- Account 1—N Engagement
- Account 1—N DocumentLink
- Account 1—N ConversationLink
- Account 1—N AppointmentLink
- Account 1—N Invoice (or BillingAccount mapping)
- Account 1—N LedgerEntry (directly or via Invoice)

Invariants:
- An Account MAY exist without an Engagement.
- Portal access MUST be scoped to one or more Accounts linked to the portal identity (see PERMISSIONS_MODEL.md).

---

### 3.2 Contact
Represents a person associated with an Account (client-side identity anchor).

Key fields (typical):
- `account_id` (required)
- `first_name`, `last_name`
- `email` (nullable but recommended)
- `phone` (nullable)
- `role_label` (optional free-text: owner, controller, spouse, etc.)
- `status` (active | inactive)
- `is_primary` (boolean; optional)

Relationships:
- Contact N—1 Account
- Contact 0—1 PortalIdentity (optional mapping)
- Contact may be associated to communications and documents via links.

Invariants:
- A Contact MUST belong to exactly one Account in the base model.
  - If multi-account contacts are needed, model it explicitly with a join table `AccountContact` and treat Contact as person-global within tenant. Do not “fake” multi-account by duplicating Contacts without linkage.

---

### 3.3 StaffUser (internal identity)
Internal firm user.

Key fields (typical):
- `email`
- `display_name`
- `status` (active | disabled)
- `rbac_role_ids` (or join table)

Relationships:
- StaffUser N—M Role
- StaffUser may be assignee/owner for Engagement, EngagementLine, WorkItem, Appointment.
- StaffUser appears as actor in audit logs.

Invariants:
- StaffUser is not a PortalIdentity.
- StaffUser permissions derive from RBAC and MUST be enforced server-side.

---

### 3.4 PortalIdentity (external identity)
External login identity for a client contact.

Key fields (typical):
- `contact_id` (required)
- `status` (invited | active | disabled)
- `last_login_at`
- `auth_provider` (optional)
- `scopes` (or join table to scope grants)

Relationships:
- PortalIdentity 1—1 Contact
- PortalIdentity N—M AccountScopeGrant (if contact is allowed to access multiple Accounts)
- PortalIdentity appears as actor in audit logs for portal actions.

Invariants:
- PortalIdentity MUST be permission-constrained to explicitly granted accounts and scopes.
- PortalIdentity MUST NOT inherit staff roles.

---

### 3.5 Engagement
Represents a service relationship container (the “project space” for a client engagement).

Key fields (typical):
- `account_id` (required)
- `name` (required)
- `status` (see state machine below)
- `owner_staff_user_id` (nullable)
- `active_quote_version_id` (nullable; required to activate in V1 unless admin override exists)
- `start_at`, `end_at` (optional)
- `notes` (optional)

Relationships:
- Engagement N—1 Account
- Engagement 1—N EngagementLine
- Engagement 1—N WorkItem (depending on modeling choice)
- Engagement 1—N DocumentLink / ConversationLink / AppointmentLink
- Engagement 1—N QuoteVersion (history)
- Engagement 1—N Invoice (optional direct association)

Invariants:
- An Engagement MUST belong to an Account.
- An Engagement MUST NOT be “active delivery” without an accepted QuoteVersion, unless an explicit admin override path exists and is auditable.

---

### 3.6 EngagementLine
Represents a scoped service line within an engagement (tier/service stream/deliverable stream).

Key fields (typical):
- `engagement_id` (required)
- `name` (required)
- `status` (see state machine below)
- `service_code` (optional stable identifier)
- `pricing_snapshot_ref` (optional reference to QuoteVersion line item / rule output)
- `owner_staff_user_id` (nullable)

Relationships:
- EngagementLine N—1 Engagement
- EngagementLine 1—N WorkItem
- EngagementLine 1—N DocumentLink / ConversationLink

Invariants:
- EngagementLine MUST belong to exactly one Engagement.
- WorkItems generated from templates SHOULD attach to an EngagementLine when the work is tied to that service line.

---

### 3.7 WorkItem
Unit of execution (task/work packet). WorkItems may be manually created or instantiated from DeliveryTemplates and/or recurrence.

Key fields (typical):
- `engagement_id` (required OR derived)
- `engagement_line_id` (nullable but recommended when applicable)
- `title` (required)
- `description` (optional)
- `status` (see state machine below)
- `assignee_staff_user_id` (nullable)
- `due_at` (nullable)
- `priority` (low | normal | high | urgent; optional)
- `template_instance_id` (nullable; if created from template)
- `recurrence_generation_id` (nullable; if created from recurrence)
- `blocked_by_work_item_id` / dependency modeling (optional)
- `completed_at` (nullable)

Relationships:
- WorkItem N—1 Engagement
- WorkItem N—1 EngagementLine (optional)
- WorkItem 1—N DocumentLink / ConversationLink
- WorkItem may be referenced by OrchestrationExecution steps.

Invariants:
- A WorkItem MUST be anchored to an Engagement.
- A WorkItem MUST NOT be created twice for the same recurrence generation uniqueness key (see RECURRENCE_ENGINE_SPEC.md).
- If a WorkItem is created from a DeliveryTemplate node, it SHOULD retain a stable template node reference for traceability.

---

### 3.8 Quote and QuoteVersion
Pricing output objects.

QuoteVersion is the immutable snapshot used for acceptance and audit.

Quote (optional) is the mutable “working draft” container.

QuoteVersion key fields (typical):
- `account_id`, `engagement_id` (nullable until bound)
- `version_number`
- `status` (draft | issued | accepted | rejected | expired | voided)
- `ruleset_version` (pricing rules schema version)
- `input_context_snapshot` (bounded, governed snapshot)
- `output_snapshot`
- `trace_snapshot`
- `issued_at`, `accepted_at`
- `accepted_by_actor` (staff or portal actor ref)

Invariants:
- Accepted QuoteVersions MUST be immutable.
- Engagement activation MUST reference an accepted QuoteVersion in V1 (unless override).

---

### 3.9 Appointment
Represents a bookable meeting slot and the booked event.

Key fields (typical):
- `account_id` (nullable for prospective bookings; required once linked)
- `contact_id` (nullable; required for client-attended appointments)
- `staff_user_id` (nullable; may be pooled/team booking)
- `status` (see state machine below)
- `starts_at`, `ends_at` (required)
- `timezone` (required)
- `location` (optional)
- `external_event_id` (nullable)
- `calendar_connection_id` (nullable)
- `created_via` (portal | staff | sync)

Relationships:
- Appointment N—1 Account (optional)
- Appointment N—1 Contact (optional)
- Appointment N—1 StaffUser (optional)
- Appointment 1—N AppointmentSyncAttempt (log)

Invariants:
- External sync updates MUST be idempotent using `external_event_id` + connection scope.
- Appointment meaning MUST be preserved across sync reconciliation rules (see CALENDAR_SYNC_SPEC.md).

---

### 3.10 Invoice
Represents an issued billing artifact. In a ledger-first system, Invoice may be a “document-like” summary whose financial truth comes from ledger entries.

Key fields (typical):
- `account_id` (required)
- `engagement_id` (nullable but recommended when applicable)
- `status` (see state machine below)
- `invoice_number` (unique within tenant)
- `issued_at`
- `due_at` (optional)
- `currency`
- `total_amount` (derived or stored with reconciliation rules)
- `terms_snapshot` (optional)
- `pdf_document_id` (optional link)

Relationships:
- Invoice N—1 Account
- Invoice N—1 Engagement (optional)
- Invoice 1—N LedgerEntry (invoice issuance entry; payment application entries; adjustments)

Invariants:
- Invoice totals MUST be explainable from ledger entries when ledger-first is used.
- Payment posting MUST be idempotent (BILLING_LEDGER_SPEC.md).

---

### 3.11 LedgerEntry
Canonical money movement record.

Key fields, types, and constraints are defined in BILLING_LEDGER_SPEC.md. Domain-model level anchors:
- LedgerEntry MUST link to Account
- LedgerEntry MAY link to Invoice, Engagement, EngagementLine
- LedgerEntry MUST be immutable after posting except via compensating entries.

---

### 3.12 Document and DocumentVersion
Governed artifact records.

Key fields and semantics defined in DOCUMENTS_AND_STORAGE_SPEC.md. Domain-model anchors:
- Document is the logical artifact
- DocumentVersion is the immutable content revision
- Document locks (if used) prevent concurrent writes for specific document classes

Documents MUST be linked to the object graph via DocumentLink (below) unless placed into governed triage.

---

### 3.13 Conversation and Message
Communications records.

Detailed semantics live in COMMUNICATIONS_SPEC.md (to be created). Domain-model anchors:
- Conversation is the thread
- Message is an entry in the thread
- Attachments are Documents (governed artifacts), not raw blobs

Conversations MUST be linked to the object graph via ConversationLink.

---

### 3.14 Association entities (linking layer)

#### DocumentLink
Explicit association between Document and a domain object.

Fields (typical):
- `document_id`
- `object_type` (Account | Engagement | EngagementLine | WorkItem | Invoice | Appointment | Conversation | ...)
- `object_id`
- `role` (supporting | deliverable | evidence | intake | invoice_pdf | other)
- `created_at`, `created_by`

Invariant:
- A document MUST NOT be “visible” unless it is linked and permission evaluation permits it (PERMISSIONS_MODEL.md).

#### ConversationLink
Explicit association between Conversation and a domain object.

Fields (typical):
- `conversation_id`
- `object_type`, `object_id`
- `role` (general | workitem_context | billing_context | onboarding | other)

#### AppointmentLink
Optional explicit association if Appointment needs multiple anchors beyond its direct fields.

---

## 4) State machines

State machines below define allowed statuses and transitions. The canonical list of statuses MUST be implemented consistently across API, DB, and UI.

### 4.1 Engagement state machine

Statuses:
- `draft` (pre-activation; not active delivery)
- `active` (delivery ongoing)
- `paused` (delivery intentionally paused)
- `completed` (delivery completed; no new work expected)
- `canceled` (stopped before completion; reason required)
- `archived` (inactive record kept for reference; not operational)

Allowed transitions:
- draft → active (requires accepted QuoteVersion unless admin override; auditable)
- active → paused
- paused → active
- active → completed
- active → canceled
- paused → canceled
- completed → archived
- canceled → archived

Forbidden transitions (examples):
- completed → active (MUST NOT; create a new engagement or explicitly “reopen” via an admin-only path that creates an audit event and new state version)
- archived → active (MUST NOT)

Required fields by transition:
- draft → active: `active_quote_version_id` required (unless override), `activated_at`, `activated_by_actor`
- active/paused → canceled: `canceled_reason` required

---

### 4.2 EngagementLine state machine

Statuses:
- `draft`
- `active`
- `paused`
- `completed`
- `canceled`

Allowed transitions:
- draft → active (usually at engagement activation)
- active → paused
- paused → active
- active → completed
- active → canceled
- paused → canceled

Invariant:
- EngagementLine MUST NOT be active if its parent Engagement is not active, unless explicitly modeled as “pre-staged” (avoid in V1).

---

### 4.3 WorkItem state machine

Statuses:
- `planned` (created but not yet ready)
- `ready` (actionable)
- `in_progress`
- `blocked`
- `waiting` (external dependency; not blocked by internal work item)
- `completed`
- `canceled`

Allowed transitions:
- planned → ready
- ready → in_progress
- in_progress → blocked
- blocked → in_progress
- in_progress → waiting
- waiting → in_progress
- ready → canceled
- in_progress → canceled
- blocked → canceled
- waiting → canceled
- in_progress → completed
- blocked → completed (ONLY if block is informational; otherwise forbid; implementation choice MUST be explicit)
- ready → completed (ONLY for trivial/auto-complete work; must be auditable)

Required semantics:
- `completed_at` MUST be set on transition to completed.
- `canceled_reason` SHOULD be captured on canceled.
- If `blocked_by_work_item_id` exists, unblocking rules MUST be defined (template/orchestration may manage this).

Forbidden transitions (examples):
- completed → in_progress (MUST NOT; reopen requires explicit admin path and audit trail or create a new WorkItem)
- canceled → in_progress (MUST NOT)

---

### 4.4 Appointment state machine

Statuses:
- `requested` (client requested; awaiting confirmation if applicable)
- `confirmed`
- `rescheduled` (optional intermediate; often modeled as confirmed with new times)
- `canceled`
- `no_show`
- `completed`

Allowed transitions:
- requested → confirmed
- requested → canceled
- confirmed → canceled
- confirmed → completed
- confirmed → no_show
- confirmed → confirmed (time update via reschedule; must preserve audit)
- any → canceled (by sync) ONLY if reconciliation rules permit and must be logged

Invariants:
- Calendar sync MUST not create duplicate Appointments for the same external event and connection.
- Updates from sync MUST be idempotent.

---

### 4.5 Invoice state machine

Statuses:
- `draft`
- `issued`
- `partially_paid`
- `paid`
- `voided`
- `written_off` (optional)

Allowed transitions:
- draft → issued
- issued → partially_paid
- partially_paid → paid
- issued → paid
- issued → voided
- partially_paid → voided (only if allowed by policy; requires compensating entries)
- issued/partially_paid → written_off (if supported; requires ledger entries)

Invariants:
- Status transitions MUST reconcile with ledger entries (ledger-first truth).
- Payment application MUST be idempotent and traceable.

---

## 5) Key invariants (system-critical)

1. Every operational artifact MUST be anchored to the canonical object graph (Account/Engagement/WorkItem, etc.) or placed into an explicit governed triage bucket with workflow.
2. Accepted QuoteVersions MUST be immutable.
3. Ledger entries MUST be immutable after posting except via compensating entries.
4. Permission enforcement MUST be server-side for every read and mutation.
5. Recurrence and orchestration workers MUST be idempotent and deduplicated by design.
6. Documents and attachments MUST be governed artifacts with access logging and permission checks.

---

## 6) Forbidden transition catalog (minimum set)

Engagement:
- completed → active (without explicit admin “reopen” semantics)
- archived → active

EngagementLine:
- completed → active (without explicit admin semantics)

WorkItem:
- completed → in_progress
- canceled → ready/in_progress

Appointment:
- completed → confirmed (create a new appointment instead)

Invoice:
- paid → issued (requires new invoice or explicit reversal logic)
- voided → issued (new invoice required)

---

## 7) Open modeling choices (must be resolved by decision + spec update)

1. Contact modeling for multi-account portal users:
- Option A: Contact is per-account (simpler) + join table for multi-account portal identity
- Option B: Person entity + AccountPerson join (more correct, more complex)

2. WorkItem anchoring:
- Option A: WorkItem always belongs to EngagementLine (Engagement derived)
- Option B: WorkItem belongs to Engagement; EngagementLine optional

3. Dependency modeling:
- WorkItem-to-WorkItem dependencies vs template DAG-only dependencies

These should be resolved via DECISION_LOG.md and reflected in the model consistently.

---

