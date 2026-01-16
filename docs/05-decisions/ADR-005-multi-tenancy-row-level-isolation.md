# ADR-005: Multi-tenancy uses firm-scoped row-level isolation

**Purpose:** Document the canonical multi-tenant isolation pattern in the platform.

**Audience:** Developers, Operators

**Evidence Status:** STATIC-ONLY

---

**Status:** Accepted  
**Date:** 2026-01-16  
**Deciders:** Platform/Architecture Team  
**Tags:** architecture, security, multi-tenancy

## Context and Problem Statement

The codebase implements a multi-tenant SaaS where every record belongs to a Firm. The
platform needs a single, canonical tenancy model to prevent documentation drift and
ensure that data isolation aligns with the implemented Django patterns. The existing
implementation uses firm-scoped row-level isolation (Firm foreign keys + firm-scoped
query utilities), while earlier documentation mentions schema-per-tenant. This ADR
records the implemented pattern and explains the rationale for adopting row-level
isolation as the default.

**Code Commentary (Mapping):**
- **Tenant boundary:** `Firm` is the top-level tenant boundary, referenced by firm foreign
  keys across models and described as the tenant boundary in the firm module documentation.
- **Query enforcement:** `FirmScopedQuerySet` and `FirmScopedMixin` enforce firm filtering,
  rejecting unscoped access and ensuring request-level firm context is required.

## Decision Drivers

- Operational simplicity with a single schema for migrations, backups, and observability.
- Alignment with the existing Django ORM patterns and firm-scoped query utilities.
- Reduced risk of divergence between documentation and shipping code.
- Adequate isolation for current product scale when combined with firm-scoped query enforcement.

## Considered Options

1. **Schema-per-tenant** (Pros: physical isolation, strong blast-radius boundaries; Cons: higher
   operational overhead, more complex migrations, schema routing complexity in Django).
2. **Firm-scoped row-level isolation** (Pros: simpler operations, idiomatic Django patterns,
   already implemented; Cons: higher reliance on firm-scoping correctness).
3. **Hybrid isolation (schema-per-tenant for enterprise only)** (Pros: future flexibility; Cons:
   added platform complexity and branching migrations).

## Decision Outcome

Chosen option: **Firm-scoped row-level isolation**, because it matches the implemented system
and provides the best balance of isolation and operational simplicity for the current
product stage.

The platform’s canonical tenancy model is firm-scoped row-level isolation. Schema-per-tenant
is a future option only if enterprise requirements demand physical isolation.

### Positive Consequences

- Documentation and implementation are aligned with the actual Django data model.
- Operational workflows (migrations, backups, analytics) remain straightforward.
- Firm-scoped utilities provide a consistent enforcement point for tenant isolation.

### Negative Consequences

- Tenant isolation relies on correct firm-scoping in every query path.
- Cross-tenant leakage bugs have a larger blast radius if guards are bypassed.

## Implementation Plan

### Migration Steps

1. Confirm all tenant-scoped models continue to use firm foreign keys.
2. Keep firm-scoped query utilities as the required access path for tenant data.
3. Ensure documentation and training materials reference firm-scoped row-level isolation.

### Rollback Plan

If schema-per-tenant becomes mandatory in the future:

1. Introduce schema routing middleware (e.g., django-tenants or custom).
2. Implement per-firm schema provisioning.
3. Migrate firm data into per-tenant schemas with validation and rollbacks.

### Success Criteria

- [ ] Documentation references firm-scoped row-level isolation as canonical.
- [ ] Firm-scoped query utilities remain the required access path for tenant data.

## Constitution Impact

Not applicable.

## Related Decisions

- [ADR-006: Enforce firm-scoped queries as the default data access pattern](ADR-006-firm-scoped-query-enforcement.md)

## Links

- [Firm module overview](../../src/modules/firm/README.md)
- [Firm-scoped utilities](../../src/modules/firm/utils.py)

---

## Notes

This ADR documents the existing implementation rather than introducing a new tenancy model.

**Change Log:**

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Initial draft | AGENT |

---

**Last Updated:** 2026-01-16  
**Evidence Sources:**
- [Decision Log (ADR-lite)](../4)
- [Firm module overview](../../src/modules/firm/README.md)
- [Firm-scoped utilities](../../src/modules/firm/utils.py)
