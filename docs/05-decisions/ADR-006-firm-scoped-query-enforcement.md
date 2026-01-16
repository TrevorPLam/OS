# ADR-006: Enforce firm-scoped queries as the default data access pattern

**Purpose:** Record the decision to require firm-scoped query utilities for tenant data access.

**Audience:** Developers, Operators

**Evidence Status:** STATIC-ONLY

---

**Status:** Accepted  
**Date:** 2026-01-16  
**Deciders:** Platform/Architecture Team  
**Tags:** architecture, security, data-access

## Context and Problem Statement

Firm-scoped row-level isolation depends on consistent query enforcement. Ad-hoc filtering
is error-prone, and unscoped queries can create cross-tenant data exposure. The codebase
implements explicit firm-scoped query utilities (querysets and mixins) to enforce firm
filters and require explicit firm context. This ADR documents the enforcement pattern
so data-access behavior stays consistent across modules.

**Code Commentary (Mapping):**
- **Firm-scoped query utilities:** `FirmScopedQuerySet` requires a firm and refuses to scope
  with `None`, preventing unscoped access. `FirmScopedMixin` ensures ViewSets always apply
  firm scoping automatically.
- **Job guardrails:** Background jobs require firm context via a job guard to prevent
  tenant leakage in asynchronous processing.

## Decision Drivers

- Prevent cross-tenant leakage by centralizing firm scoping in reusable utilities.
- Provide a predictable pattern for developers and agents when adding new queries.
- Align with the existing system spec and enforcement helpers already in the codebase.

## Considered Options

1. **Ad-hoc query filters** (Pros: minimal abstractions; Cons: easy to miss filters).
2. **Firm-scoped query utilities (QuerySet + Mixin)** (Pros: consistent enforcement, reuse;
   Cons: requires developer discipline to use the utilities everywhere).
3. **Database-level RLS only** (Pros: strong enforcement in DB; Cons: added operational
   complexity and still requires application awareness).

## Decision Outcome

Chosen option: **Firm-scoped query utilities**, because they are already implemented and
provide a consistent, code-level enforcement layer for firm isolation.

All tenant-scoped query access must flow through `FirmScopedQuerySet` or `FirmScopedMixin`,
and background jobs must guard firm context before accessing tenant data.

### Positive Consequences

- Consistent firm filtering across viewsets and query entry points.
- Clear, reusable API for tenant-safe data access.
- Reduced chance of cross-tenant leakage in async code paths.

### Negative Consequences

- Developers must learn and consistently apply firm-scoping patterns.
- Custom queries may need refactoring to fit the firm-scoped utilities.

## Implementation Plan

### Migration Steps

1. Keep `FirmScopedQuerySet` as the required access path for firm-scoped models.
2. Use `FirmScopedMixin` for API ViewSets that access tenant data.
3. Require job guard usage for asynchronous tasks that access tenant data.

### Rollback Plan

If firm-scoped utilities become infeasible:

1. Enforce firm filters via database policies (RLS) exclusively.
2. Update application code to rely on RLS and remove the utilities.

### Success Criteria

- [ ] All tenant data access flows through firm-scoped query utilities.
- [ ] Background jobs validate firm context before accessing tenant data.

## Constitution Impact

Not applicable.

## Related Decisions

- [ADR-005: Multi-tenancy uses firm-scoped row-level isolation](ADR-005-multi-tenancy-row-level-isolation.md)

## Links

- [Firm-scoped utilities](../../src/modules/firm/utils.py)
- [Job guard for firm context](../../src/job_guards.py)

---

## Notes

This ADR formalizes the existing firm-scoped query enforcement utilities used throughout
modules and APIs.

**Change Log:**

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Initial draft | AGENT |

---

**Last Updated:** 2026-01-16  
**Evidence Sources:**
- [Firm-scoped utilities](../../src/modules/firm/utils.py)
- [Job guard for firm context](../../src/job_guards.py)
