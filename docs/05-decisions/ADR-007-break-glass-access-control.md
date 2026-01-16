# ADR-007: Require break-glass sessions for platform operator content access

**Purpose:** Document the decision to gate platform operator content access behind audited break-glass sessions.

**Audience:** Developers, Operators, Security Reviewers

**Evidence Status:** STATIC-ONLY

---

**Status:** Accepted  
**Date:** 2026-01-16  
**Deciders:** Platform/Architecture Team  
**Tags:** security, access-control, audit

## Context and Problem Statement

The platform includes operator accounts that can access metadata across tenants. To prevent
routine content access from bypassing tenant boundaries, the system requires explicit
break-glass sessions for content access by platform operators. The codebase contains
break-glass session models and permission checks; this ADR documents the requirement so
security and audit expectations remain explicit.

**Code Commentary (Mapping):**
- **Break-glass sessions:** `BreakGlassSession` records the operator, reason, expiration, and
  review metadata for audited access.
- **Permission enforcement:** Break-glass permission classes enforce that platform users
  must have an active break-glass session before accessing content models, and log
  audit events when break-glass access occurs.

## Decision Drivers

- Prevent routine operator access to customer content without explicit authorization.
- Ensure all elevated access is time-bound, reasoned, and auditable.
- Provide a consistent security posture for tenant isolation and incident response.

## Considered Options

1. **Operator access without break-glass** (Pros: simpler workflows; Cons: weak auditability,
   higher risk of inappropriate access).
2. **Break-glass sessions with auditing** (Pros: strong audit trail, explicit elevation;
   Cons: added operational steps for operators).
3. **No operator content access** (Pros: strict isolation; Cons: limits support and incident
   response capabilities).

## Decision Outcome

Chosen option: **Break-glass sessions with auditing**, because it balances support needs
with strict audit and least-privilege controls.

Platform operators must have an active, firm-scoped break-glass session to access customer
content models. Break-glass sessions are time-bound, require a reason, and are logged for
review.

### Positive Consequences

- Content access by operators is explicit, time-bound, and auditable.
- Security posture aligns with tenant isolation requirements.
- Break-glass sessions provide an operational mechanism for support escalations.

### Negative Consequences

- Support workflows require additional steps to activate and review break-glass sessions.
- Break-glass enforcement depends on consistent permission checks across endpoints.

## Implementation Plan

### Migration Steps

1. Continue using `BreakGlassSession` as the canonical record of elevated access.
2. Enforce break-glass permissions for platform operator access to content models.
3. Log audit events whenever break-glass access occurs.

### Rollback Plan

If break-glass enforcement is removed:

1. Remove break-glass permission checks from content endpoints.
2. Update operator roles and audit policies accordingly.

### Success Criteria

- [ ] Platform operators cannot access content models without an active break-glass session.
- [ ] Break-glass access is logged and tied to an operator, firm, and reason.

## Constitution Impact

Not applicable.

## Related Decisions

- [ADR-005: Multi-tenancy uses firm-scoped row-level isolation](ADR-005-multi-tenancy-row-level-isolation.md)
- [ADR-006: Enforce firm-scoped queries as the default data access pattern](ADR-006-firm-scoped-query-enforcement.md)

## Links

- [Break-glass session model](../../src/modules/firm/models.py)
- [Break-glass permissions](../../src/modules/firm/permissions.py)

---

## Notes

This ADR documents the implemented break-glass access control path used for platform
operator content access.

**Change Log:**

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Initial draft | AGENT |

---

**Last Updated:** 2026-01-16  
**Evidence Sources:** src/modules/firm/models.py; src/modules/firm/permissions.py
