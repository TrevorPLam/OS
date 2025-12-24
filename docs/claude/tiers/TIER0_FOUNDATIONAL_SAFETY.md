# TIER 0 — FOUNDATIONAL SAFETY (FULL EXPANSION)

> **Rule:** Tier 0 must be complete before any feature, billing, or UX work proceeds.
>
> If Tier 0 is wrong or incomplete, privacy, tenancy, and trust all fail.

---

## 0.1 Firm / Workspace Tenancy (Hard Tenant Boundary)

### Purpose

Establish Firm as the top-level tenant boundary in a multi-firm SaaS. All isolation, authorization, and privacy guarantees depend on this.

### Scope

Applies to:

* all firm-side users
* all clients
* all engagements, projects, tasks, documents, billing records
* all API requests
* all background jobs

### What must be true

* Every firm-side object belongs to exactly one Firm (directly or via Client).
* No firm user can ever access another firm's data.
* Platform operators cannot bypass firm boundaries except via break-glass.

### Required components

* Firm (Workspace) model
* Firm ↔ User relationship
* Firm ↔ Client relationship
* Firm propagation through request lifecycle

### File / area targets (conceptual)

* New Firm module (models, admin)
* User profile or membership model (user → firm)
* Client model (client → firm)
* Shared permission helpers
* Request context resolution (middleware or equivalent)

### Acceptance criteria

* Any attempt to query another firm's data returns zero results or 403.
* Removing firm scoping from a queryset causes tests to fail.
* A firm user cannot infer the existence of other firms.

### Failure modes to avoid

* "Global admin" querysets
* Implicit joins without firm filtering
* Assuming client_id alone is sufficient isolation

---

## 0.2 Firm Context Resolution (Explicit, Deterministic)

### Purpose

Ensure the system always knows which firm it is acting for, in every request and job.

### Decision (locked)

Firm context is resolved via a combination of:

* subdomain / URL
* user-selected firm (session)
* token or session claims

### Scope

Applies to:

* API requests
* admin views
* background jobs
* webhooks
* scheduled tasks

### What must be true

* A request without a resolved firm context must fail.
* Firm context is resolved before authorization or queries.
* Background jobs must explicitly carry firm context.

### Required components

* Firm context resolver
* Firm context attached to request object
* Firm context validation guard

### Acceptance criteria

* Requests without firm context are rejected.
* Logs always include firm identifier.
* Background jobs cannot run without firm context.

### Failure modes to avoid

* Defaulting to "first firm"
* Using user alone to infer firm
* Background jobs that assume global access

---

## 0.3 Platform Privacy Enforcement (Metadata-Only by Default)

### Purpose

Enforce the privacy-first posture: platform staff cannot read customer content.

### Scope

Applies to:

* documents
* messages
* comments
* notes
* invoice line items
* engagement/project/task content

### What must be true

* Platform roles can access only:
  * billing metadata
  * subscription state
  * audit logs
  * operational metadata
* Customer content is end-to-end encrypted.
* No admin convenience shortcuts exist.

### Required components

* Platform role separation
* Explicit deny rules for content models
* Metadata/content separation in models and APIs

### Acceptance criteria

* Platform Operator APIs never return content fields.
* Attempts to access content tables as platform user are blocked.
* Content encryption keys are not available to platform roles.

### Failure modes to avoid

* "Support admin" with silent read access
* Mixing metadata and content in the same API responses
* Logging content accidentally

---

## 0.4 Break-Glass Access (Rare, Audited, Controlled)

### Purpose

Allow exceptional access for emergencies or consented support without normalizing surveillance.

### Decision (locked)

Break-glass can be triggered by:

* explicit firm owner consent OR
* predefined emergency policy

### Scope

Applies to:

* debugging
* legal obligations
* critical outages

### What must be true

* Break-glass is time-limited.
* Reason is mandatory.
* All actions are logged.
* Impersonation is obvious and bounded.

### Required components

* Break-glass activation mechanism
* Impersonation mode indicator
* Automatic expiration
* Immutable audit records

### Acceptance criteria

* Break-glass sessions auto-expire.
* Every action taken is attributable.
* Normal platform roles cannot access content.

### Failure modes to avoid

* Silent impersonation
* Long-lived elevated sessions
* Unlogged emergency access

---

## 0.5 Portal Containment (Client Default-Deny)

### Purpose

Ensure portal users cannot escape the client portal surface, even accidentally.

### Scope

Applies to:

* all portal users
* all API endpoints
* all ViewSets

### What must be true

* Portal users can access only explicitly allowed endpoints.
* All portal querysets are client-scoped and firm-scoped.
* No "shared" admin endpoints are accessible.

### Required components

* Portal-only permission classes
* Separate routing or namespace
* Explicit allowlist of portal endpoints

### Acceptance criteria

* Portal user receives 403 on any non-portal endpoint.
* Portal user cannot access other clients' data.
* Portal user cannot infer firm-level data.

### Failure modes to avoid

* Reusing firm endpoints for portal
* Assuming frontend hides access is sufficient
* Missing queryset scoping in read-only endpoints

---

## 0.6 Background Job Tenant Safety

### Purpose

Prevent cross-tenant data leaks via async processing, the most common SaaS failure mode.

### Scope

Applies to:

* billing runs
* renewal generation
* notifications
* document processing
* scheduled jobs

### What must be true

* Every job explicitly includes:
  * firm_id
  * client_id (if applicable)
* Jobs fail if context is missing.
* Logs include firm/client context.

### Required components

* Job payload schema
* Validation on job execution
* Context-aware logging

### Acceptance criteria

* No job executes without firm context.
* Jobs cannot accidentally operate across firms.
* Errors are traceable to firm/client.

### Failure modes to avoid

* "Global" scheduled jobs
* Implicit queries inside async tasks
* Reusing requestless helpers

---

## Tier 0 Completion Definition

Tier 0 is complete only when:

* Firm isolation is provable.
* Platform cannot read content by default.
* Portal users are fully contained.
* Break-glass is rare, visible, and audited.
* Async jobs are tenant-safe.

**Until then, nothing else is safe to build.**
