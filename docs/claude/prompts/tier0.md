# 🔒 TIER 0 EXECUTION PROMPT — FOUNDATIONAL SAFETY

You are executing Tier 0 only of a multi-tier build.
Tier 0 is foundational safety. Nothing else is allowed.

## Authority

* `/docs/claude/NOTES_TO_CLAUDE.md` is authoritative.
* If code conflicts with Notes, code must change.
* Do not assume or invent requirements.

## Scope (WHAT YOU MAY DO)

You may modify only what is required to enforce:

1. Firm / Workspace tenancy
2. Firm context resolution
3. Portal containment (default-deny)
4. Platform privacy (metadata-only access)
5. Break-glass access framework
6. Tenant-safe background job context

### Explicitly IN SCOPE

* Firm (Workspace) model + relationships
* User → Firm → Client ownership wiring
* Firm context resolution (subdomain + session + token)
* Request-level firm enforcement
* Firm-scoped query helpers/mixins
* Portal permission classes & endpoint allowlist
* Platform role restrictions (no content access)
* Break-glass activation + impersonation safeguards
* Audit logging for break-glass actions
* Background job payload validation (firm/client required)

### Explicitly OUT OF SCOPE (DO NOT TOUCH)

* Billing, pricing, invoices, payments
* Engagement logic beyond ownership wiring
* UI/UX changes (unless required for enforcement)
* Performance optimization
* Feature flags
* CI, tests, or migrations beyond what Tier 0 strictly requires
* "Temporary" bypasses or weakening constraints

## Invariants (MUST HOLD)

* Every request resolves an active Firm context or fails.
* No firm user can access another firm's data.
* Portal users are default-denied outside portal endpoints.
* Platform operators cannot read customer content by default.
* Break-glass access is:
  * explicit
  * time-limited
  * reason-required
  * fully audited
* Background jobs cannot run without firm (and client if applicable).

## Break-Glass Rules

* Triggered only by firm consent OR emergency policy.
* Impersonation mode must be obvious and auto-expire.
* All actions during break-glass are logged.
* No silent or persistent elevation.

## Completion Checklist (STOP WHEN TRUE)

* [ ] Firm tenancy enforced everywhere.
* [ ] Firm context resolution is deterministic and mandatory.
* [ ] Portal containment blocks all non-portal access.
* [ ] Platform roles cannot access content models.
* [ ] Break-glass exists and is auditable.
* [ ] Async jobs fail without tenant context.

## Output Requirements

Before stopping, report:

1. Files modified
2. How firm context is resolved
3. How portal containment is enforced
4. How platform content access is blocked
5. How break-glass is implemented
6. What was intentionally NOT touched

## Stop Conditions

* If blocked by ambiguity or missing info: STOP AND ASK
* Do not proceed to Tier 1.
* Do not "stub" future functionality.

---

**Until Tier 0 is complete, nothing else is safe to build.**
