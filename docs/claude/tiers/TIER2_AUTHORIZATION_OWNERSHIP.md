# TIER 2 — AUTHORIZATION & OWNERSHIP (FULL EXPANSION)

> **Rule:** Tier 2 ensures who can do what is explicit, enforced, and impossible to bypass.
>
> If Tier 2 is weak, privacy and tenancy fail even if Tier 0 and Tier 1 are correct.

---

## 2.1 Standardize Authorization Model Across the Codebase

### Purpose

Eliminate inconsistent, ad-hoc permission checks and replace them with a single, predictable authorization system.

### Scope

Applies to:

* all API endpoints
* all ViewSets
* all admin-accessible surfaces
* all background-triggered actions

### What must be true

* Every endpoint has an explicit permission class.
* Authorization logic is centralized, not duplicated.
* Permissions reflect role + tenant context, not UI assumptions.

### Required actions

* Inventory all ViewSets and endpoints.
* Attach explicit permission classes everywhere.
* Remove inline or duplicated permission checks.

### Acceptance criteria

* No endpoint relies on implicit access.
* Permission logic is discoverable in one place.
* Unauthorized requests fail with 403, not empty results.

### Failure modes to avoid

* Mixing authorization with business logic
* Relying on frontend to hide actions
* "Temporary" bypasses left in place

---

## 2.2 Firm-Scoped Querysets (Zero Global Access)

### Purpose

Make cross-firm access structurally impossible at the query level.

### Scope

Applies to:

* all ORM querysets
* list/detail views
* background queries

### What must be true

* Querysets always filter by firm_id.
* Client-scoped data also filters by client_id.
* Platform roles cannot bypass scoping except via break-glass.

### Required actions

* Introduce firm-scoped queryset mixins/helpers.
* Refactor existing queries to use them.
* Forbid Model.objects.all() in firm-facing code.

### Acceptance criteria

* Removing firm filter breaks tests.
* Code review can easily spot unscoped queries.
* Portal users cannot infer other clients or firms.

### Failure modes to avoid

* Filtering in serializers instead of querysets
* Applying scoping conditionally
* Using raw SQL without tenant constraints

---

## 2.3 Portal Authorization (Client-Scoped, Explicit Allowlist)

### Purpose

Ensure portal users are fully contained within their allowed surface area.

### Scope

Applies to:

* portal APIs
* client-facing views
* file access endpoints

### What must be true

* Portal users can access only allowlisted endpoints.
* Every portal queryset enforces firm + client scope.
* Portal permissions are separate from firm permissions.

### Required actions

* Create portal-specific permission classes.
* Define an explicit portal endpoint allowlist.
* Ensure portal users never hit firm admin endpoints.

### Acceptance criteria

* Portal users receive 403 on any non-portal endpoint.
* Portal users cannot access other clients' data.
* Portal users cannot elevate privileges.

### Failure modes to avoid

* Reusing firm endpoints for portal access
* Assuming read-only equals safe
* Missing scoping in "harmless" endpoints

---

## 2.4 Cross-Client Access Within Organizations

### Purpose

Allow intentional collaboration while preventing accidental data leakage.

### Scope

Applies only when:

* multiple clients share the same organization
* access is explicitly enabled

### What must be true

* Cross-client visibility is limited to shared-org context.
* No access across orgs or firms.
* Permissions are explicit and revocable.

### Required actions

* Enforce org-based access checks in addition to client checks.
* Ensure shared-org views are clearly scoped.
* Prevent default cross-client visibility.

### Acceptance criteria

* Clients only see other clients when org-shared.
* No cross-org or cross-firm leakage.
* Access can be disabled without data loss.

### Failure modes to avoid

* Treating orgs as tenants
* Implicit sharing assumptions
* Hard-to-audit sharing rules

---

## 2.5 Replace Direct User Model Imports

### Purpose

Prevent auth model drift and future breakage.

### Scope

Applies to:

* all backend code referencing User
* serializers, permissions, signals

### What must be true

* All references use AUTH_USER_MODEL or get_user_model().
* No direct imports from django.contrib.auth.models.User.

### Required actions

* Search and replace direct imports.
* Update type hints and serializers accordingly.

### Acceptance criteria

* Changing the user model does not break code.
* No direct User imports remain.

### Failure modes to avoid

* Partial refactors
* Leaving User references in signals or admin

---

## 2.6 Background Job Authorization & Context Enforcement

### Purpose

Ensure async operations respect the same authorization and tenancy rules as requests.

### Scope

Applies to:

* Celery/RQ tasks
* scheduled jobs
* webhook handlers

### What must be true

* Jobs include firm_id and client_id where applicable.
* Jobs enforce authorization rules explicitly.
* Jobs cannot escalate privileges.

### Required actions

* Define standard job payload schema.
* Validate tenant context on job execution.
* Apply permission checks inside jobs where relevant.

### Acceptance criteria

* Jobs fail without tenant context.
* Jobs cannot affect other firms' data.
* Logs clearly show firm/client per job.

### Failure modes to avoid

* Trusting caller context implicitly
* Using shared helpers without scoping
* Silent failures in background tasks

---

## Tier 2 Completion Definition

Tier 2 is complete only when:

* Every endpoint has explicit permissions.
* All data access is tenant-scoped.
* Portal users are fully contained.
* Cross-client access is intentional and auditable.
* Async jobs obey the same rules as synchronous code.

**Until Tier 2 is complete, privacy and trust guarantees are unenforceable.**
