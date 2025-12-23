# 🔒 TIER 2 EXECUTION PROMPT — AUTHORIZATION & OWNERSHIP

You are executing Tier 2 only of a multi-tier build.
Tier 2 makes permissions explicit, centralized, and unbypassable. No new features.

## Authority

* `/docs/claude/NOTES_TO_CLAUDE.md` is authoritative.
* Assume Tier 0 (tenant safety) and Tier 1 (schema/CI truth) exist. Do not re-architect prior tiers unless a Tier 2 change requires a surgical fix.

## Scope (WHAT YOU MAY DO)

You may modify only what is required to:

1. Standardize permissions on every endpoint/ViewSet
2. Enforce firm-scoped querysets everywhere (and client-scoped where applicable)
3. Enforce portal containment via explicit allowlist + portal-only permission model
4. Implement cross-client access only within same Organization (and only where intended)
5. Replace direct User imports with AUTH_USER_MODEL / get_user_model()
6. Ensure background jobs enforce the same tenant/permission rules as request paths (authorization + firm/client context validation)

### Explicitly IN SCOPE

* Create/normalize permission classes:
  * PlatformOperator (metadata-only)
  * BreakGlassOperator (rare, audited)
  * FirmOwner / FirmAdmin / Staff (granular)
  * PortalUser (default-deny, allowlist)
* Ensure every ViewSet has:
  * explicit permission_classes
  * a tenant-scoped get_queryset() (or equivalent)
* Add reusable helpers/mixins:
  * firm-scoped queryset mixin
  * client-scoped queryset mixin
  * organization-sharing constraint helper
* Separate portal routing/namespace (if not already) or implement a strict allowlist check
* Replace all direct imports of `django.contrib.auth.models.User`
* Ensure async tasks validate:
  * firm context exists
  * client context exists when required
  * authorization rules are applied (no "system" bypass without break-glass)

### Explicitly OUT OF SCOPE (DO NOT TOUCH)

* Billing feature implementation (invoices/payments/credits logic changes)
* Renewal logic changes
* Encryption implementation details (beyond access boundaries)
* Performance tuning (except tenant-scope correctness)
* Large refactors not required for authorization correctness
* UI/UX improvements beyond what is required to enforce access control

## Invariants (MUST HOLD)

* Default deny: if an endpoint is not explicitly permitted, access is forbidden.
* No endpoint may return cross-firm data.
* Portal users must not access firm-admin endpoints.
* Cross-client visibility is allowed only when clients share the same Organization and the endpoint is explicitly designed for shared-org context.
* No permissions may rely on frontend hiding buttons.
* No "temporary" admin bypasses.

## Execution Steps (DO THESE IN ORDER)

1. Inventory all endpoints/ViewSets and classify into:
   * platform-only (metadata)
   * firm-only
   * portal-only
   * shared-org portal (explicitly)
2. Implement/standardize permission classes for each category.
3. Enforce tenant scoping in get_queryset() for every ViewSet:
   * firm_id filter always for firm-facing endpoints
   * portal endpoints must filter by firm_id AND portal client_id
4. Implement portal containment:
   * allowlist of portal endpoints
   * 403 for anything else
5. Implement shared-org rule:
   * only allow portal cross-client access in endpoints explicitly intended for org-shared views
6. Remove direct User imports and update references.
7. Ensure async tasks:
   * validate tenant context
   * never operate globally
   * apply equivalent authorization logic or require break-glass for exceptional operations

## Completion Checklist (STOP WHEN TRUE)

* [ ] Every endpoint has explicit permissions.
* [ ] Every endpoint has tenant-scoped querysets.
* [ ] Portal users cannot access non-portal endpoints (403).
* [ ] Cross-client access only works for shared-org context and only via explicit endpoints.
* [ ] No direct User imports remain.
* [ ] Async tasks cannot execute without required firm/client context and do not bypass permissions.

## Output Requirements

Before stopping, report:

1. Endpoint inventory summary (counts by category)
2. Permission classes introduced/updated (names + purpose)
3. Where tenant scoping is enforced (common mixins/helpers)
4. Portal allowlist mechanism (how enforced)
5. Shared-org access mechanism (how enforced)
6. User import refactor summary
7. What was intentionally NOT touched

## Stop Conditions

* If you discover endpoints that require product intent (e.g., should this be portal-visible?): STOP AND ASK.
* Do not proceed to Tier 3.
* Do not relax Tier 0–1 safeguards to "make things work."
