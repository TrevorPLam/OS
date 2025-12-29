# Permissions Model (PERMISSIONS_MODEL)

This document defines the platform authorization model: RBAC for staff, scoped access for portal identities, document permission evaluation rules, and requirements for permission simulation and auditability.

This document is normative. If it conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals and principles

1. Authorization MUST be enforced server-side for every read and mutation.
2. The UI MUST NOT be treated as an enforcement layer; it only reflects authorization decisions.
3. Least privilege MUST be the default for all roles and portal scopes.
4. All permission grants, changes, and revocations MUST be auditable (who, when, what changed, correlation ID).

---

## 2) Identity domains

### 2.1 Staff identity (internal)
- StaffUsers authenticate as internal users.
- Staff access is governed by RBAC roles and optional fine-grained grants.

### 2.2 Portal identity (external)
- PortalIdentity authenticates as an external user mapped to a Contact.
- Portal access is governed by:
  - explicit Account association(s)
  - explicit scope grants per Account
  - object-level rules derived from the canonical graph

PortalIdentity MUST NOT inherit staff roles.

---

## 3) Authorization surface: what we authorize

Authorization decisions MUST be expressed as:

- Actor: StaffUser or PortalIdentity
- Action: a normalized verb (see Section 4)
- Resource: an entity instance or resource type (see Section 5)
- Context: tenant_id, account_id, engagement_id, object state, and request metadata (IP, device, etc. optional)

The authorization engine MUST return:
- allow/deny
- a reason trace (machine-readable) sufficient for debugging and audits

---

## 4) Action registry (canonical verbs)

Actions MUST be standardized so enforcement is consistent across domains.

Base CRUD verbs (apply to most resources):
- `read`
- `create`
- `update`
- `delete` (soft delete; hard delete requires separate action)

State/flow verbs:
- `transition` (state machine transitions)
- `assign` (change assignee/owner)
- `approve` (approval gates)
- `override` (admin-only bypass paths)

Data verbs:
- `export`
- `import`
- `download` (documents)
- `upload` (documents)

Billing verbs:
- `issue_invoice`
- `post_payment`
- `apply_retainer`
- `void_invoice`

Integration verbs:
- `connect_integration`
- `sync_integration`
- `resync_integration`

Admin verbs:
- `manage_roles`
- `grant_portal_access`
- `revoke_portal_access`
- `set_legal_hold`
- `run_migrations` (platform/staff-superadmin only, if applicable)

Each domain’s API endpoints MUST map to one of these actions (or define a new one in this registry).

---

## 5) Resource types (canonical)

Authorization MUST be defined for these resource types at minimum:

Core graph:
- Account
- Contact
- Engagement
- EngagementLine
- WorkItem

Supporting:
- Quote / QuoteVersion
- Appointment
- Conversation
- Message
- Document / DocumentVersion
- Invoice
- LedgerEntry

Operational:
- AuditEvent (read-only, restricted)
- IntegrationConnection (email/calendar)
- SyncAttemptLog (read-only, restricted)
- OrchestrationExecution / StepExecution
- RecurrenceGeneration
- DeliveryTemplate

---

## 6) Staff RBAC

### 6.1 RBAC model
1. Staff permissions MUST be granted via one or more Roles.
2. Roles MUST map to a Permissions Registry (explicit allowlist).
3. The registry MUST be the authoritative source of staff permissions and SHOULD be version-controlled in code or migrations.

Role assignment MUST be auditable:
- assigned_by_actor
- assigned_at
- role_id(s)
- reason (optional)
- correlation_id

### 6.2 Baseline staff roles (recommended defaults)

These are recommended defaults. Tenants MAY customize roles, but customization MUST remain an explicit allowlist.

- FirmAdmin
  - full tenant administration (roles, portal grants, integrations, governance controls)
- Partner / Owner
  - full operational access; may not manage system-level settings unless explicitly granted
- Manager
  - manage engagements, assign work, approve milestones; limited admin
- Staff
  - execute work, create/edit items they own or are assigned; limited billing/admin
- Billing
  - invoice and payment operations; limited operational edits
- ReadOnly
  - read access across allowed objects; no mutations
- IT / Integrations (optional)
  - manage integration connections and sync tooling; limited to integrations and logs

### 6.3 Object ownership and scoping (staff)
RBAC defines “what actions are possible,” but access SHOULD be further scoped by:
- ownership (owner_staff_user_id)
- assignment (assignee_staff_user_id)
- team/department (if modeled later)

Minimum rule set (V1):
1. Staff roles MAY grant broad access across the tenant, but sensitive actions SHOULD require elevated roles (Admin/Partner/Billing).
2. If an object has `owner_staff_user_id`, the system MAY support “owner-only” edits for certain roles (e.g., Staff can update only owned objects), but this MUST be explicit and consistent.

---

## 7) Portal scopes (external access)

### 7.1 Account association
A PortalIdentity MUST be linked to one or more Accounts via explicit grants (even if the underlying Contact belongs to one Account). Multi-account access MUST be deliberate.

Model options (choose one and enforce consistently):
- Option A: PortalIdentity has `AccountScopeGrant(account_id, scopes...)`
- Option B: PortalIdentity has `AccountMembership(account_id)` plus `ScopeGrant(account_id, scope)`

### 7.2 Portal scope registry (recommended)
Portal scopes SHOULD be limited and composable. Examples:

Messaging:
- `portal:message:read`
- `portal:message:send`

Documents:
- `portal:document:list`
- `portal:document:download`
- `portal:document:upload`

Appointments:
- `portal:appointment:book`
- `portal:appointment:read`
- `portal:appointment:cancel` (optional)

Billing:
- `portal:invoice:read`
- `portal:invoice:pay`

Work visibility (optional, if you expose work status to clients):
- `portal:work:read` (view limited WorkItem summaries)
- `portal:engagement:read` (view engagement status and key dates)

Account management (usually restricted):
- `portal:contact:read`
- `portal:contact:update` (very limited; e.g., phone number)

### 7.3 Portal least-privilege defaults
Default portal access SHOULD include only:
- messaging read/send
- document list/download/upload (to approved locations)
- appointment booking (if enabled)
- invoice read/pay (if enabled)

It SHOULD NOT include:
- viewing internal staff notes
- editing engagements/work items
- exporting data
- viewing other accounts unless explicitly granted

---

## 8) Document permissions (hierarchy and evaluation)

Documents are governed artifacts and MUST follow explicit evaluation rules.

### 8.1 Document anchors
A Document MUST be visible only if it is:
- associated to an object in the canonical graph via DocumentLink, OR
- located in an explicit governed triage bucket with its own access rules

### 8.2 Effective access model
Effective document permissions MUST be computed from:
1. Actor identity domain (staff vs portal)
2. Actor permissions/scopes
3. Document classification (DATA_GOVERNANCE.md)
4. DocumentLink associations (what objects it is linked to)
5. Optional explicit overrides (rare; must be auditable)

### 8.3 Inheritance rules (normative)
1. A document linked to an object inherits that object’s visibility constraints.
2. If a document is linked to multiple objects, visibility is the union of allowed viewers across those objects, unless restricted by classification.
3. Classification restrictions MUST be applied last as a “cap”:
   - even if the object is visible, the document may be hidden/redacted if its classification exceeds the actor’s clearance.

### 8.4 Portal document rules
1. Portal identities MUST NOT access documents unless:
   - they have `portal:document:list` for the Account, AND
   - the document is linked to an object within an Account they are granted, AND
   - the document is marked as portal-shareable (one of):
     - DocumentLink role indicates client-facing (e.g., `deliverable`, `evidence_shared`, `invoice_pdf`)
     - or explicit “portal_visible=true” metadata on the link (bounded, auditable)
2. Uploads by portal identities MUST land in a controlled intake location with explicit linkage rules and scanning hooks.

### 8.5 Signed URL enforcement
1. `download` and `upload` MUST be permission-checked before generating signed URLs.
2. Signed URLs MUST be short-lived and least-privilege (single object, single operation).

---

## 9) Resource-level authorization rules (high-level)

### 9.1 Account
Staff:
- `read`: per role scope; defaults should allow staff to read accounts they service (policy-defined)
- `update`: restricted (Manager+)
Portal:
- `read`: only for granted Accounts, and only fields allowed by scope and governance
- `update`: highly limited (typically none in V1)

### 9.2 Engagement / EngagementLine
Staff:
- full lifecycle actions per role (Manager+ can activate/pause/cancel; Admin override requires explicit action)
Portal:
- `read` (optional): only status-level visibility if scope granted; no internal notes

### 9.3 WorkItem
Staff:
- Staff role can update assigned work items (status, notes, attachments) within policy
- Managers can assign/override/approve
Portal:
- typically `read` only if you expose limited status; never internal fields

### 9.4 Conversation / Message
Staff:
- access if linked to an accessible object (Account/Engagement/WorkItem) OR created in internal-only channels
Portal:
- only conversations explicitly created as client-visible threads within granted Account scope

### 9.5 QuoteVersion
Staff:
- view, issue, accept (depending on role)
Portal:
- may accept and view if explicitly delivered to portal identity (policy-defined)

### 9.6 Billing (Invoice/Ledger)
Staff:
- Billing role and Admin/Partner control posting operations
Portal:
- invoice read/pay if scopes granted; never ledger-level detail unless explicitly designed

---

## 10) Permission evaluation algorithm (normative)

The authorization engine MUST evaluate in this order:

1. Verify tenant boundary
   - Actor MUST belong to tenant
   - Resource MUST belong to tenant

2. Determine actor domain
   - StaffUser → RBAC path
   - PortalIdentity → scope path

3. Resolve base permission
   StaffUser:
   - if Role grants Action on ResourceType → candidate allow
   PortalIdentity:
   - if Scope grants Action on ResourceType for the relevant Account → candidate allow

4. Apply resource scoping rules
   - If resource is account-scoped, actor must be allowed for that Account
   - If resource is linked to Account via Engagement/WorkItem/etc., resolve the Account and enforce account membership

5. Apply ownership/assignment constraints (if enabled)
   - e.g., Staff can update only assigned WorkItems unless elevated role

6. Apply classification caps (documents and sensitive fields)
   - deny or redact if actor clearance insufficient

7. Return decision with trace
   - decision: allow/deny
   - trace: list of checks performed, rules matched, and final cap applied

The engine MUST support “why denied” explanations without leaking restricted data.

---

## 11) Permission simulator requirements

A permission simulator MUST exist (at least as an internal tool) that can answer:

- Given:
  - actor (staff or portal)
  - action
  - resource (type + id)
  - optional hypothetical role/scope changes
- Return:
  - allow/deny
  - full evaluation trace (rule path)
  - the minimal rule/grant that would change the outcome (optional but recommended)

Simulator MUST support:
- “What can this actor do?” enumeration for a resource type within an Account (bounded; avoid expensive global scans)
- Portal scope testing across accounts
- Document access reasoning (link + portal-visible rules + classification caps)

Simulator access MUST be restricted (Admin role or platform admin only).

---

## 12) Audit requirements (permissions-specific)

The system MUST emit audit events for:
- staff role assignment changes
- portal scope grant/revoke changes
- document sharing visibility changes (e.g., link role changes to portal-visible)
- admin overrides used for state transitions
- permission simulator access (recommended; at least record usage by admins)

Audit events MUST include:
- actor
- target (user/portal identity)
- delta (what changed)
- timestamp
- correlation ID

---

## 13) Open items (must be decided and logged)

1. Whether field-level permissions are required in V1 (beyond document classification caps and basic redaction).
2. Whether staff access is strictly account-scoped (assigned accounts only) or role-wide within tenant by default.
3. Whether portal work visibility is included in V1 (and if so, the exact fields exposed).
4. Whether “share-by-link” exists for documents (and if so, link expiry, revocation, logging).

All open items must be captured in OPEN_QUESTIONS.md and resolved via DECISION_LOG.md with corresponding spec updates.

---

