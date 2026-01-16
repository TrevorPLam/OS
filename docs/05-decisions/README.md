# Architecture Decision Records (ADRs)

**Purpose:** Explain what ADRs are, when to write them, and list active decisions.  
**Audience:** Developers, Operators, Reviewers  
**Evidence Status:** STATIC-ONLY

---

This directory contains Architecture Decision Records for ConsultantPro.

Per Constitution Section 2.2:
> "A rule may be changed only by: An ADR in `docs/05-decisions/` that:
> - states the proposed change,
> - explains why the old rule is insufficient,
> - includes migration/transition steps,
> - includes a rollback plan if applicable."

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## When to Write an ADR

Create an ADR for decisions that:
- ✅ Affect system architecture or design patterns
- ✅ Change or amend the Coding Constitution
- ✅ Introduce new technologies or frameworks
- ✅ Modify data models or database schema patterns

Don't create ADRs for:
- ❌ Routine bug fixes
- ❌ Minor refactoring
- ❌ Code style preferences

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [ADR-0000](ADR-0000-template.md) | ADR Template | - | - |
| [ADR-004](ADR-004-esignature-provider-selection.md) | E-Signature Provider Selection | Accepted | 2026-01-01 |
| [ADR-005](ADR-005-multi-tenancy-row-level-isolation.md) | Multi-tenancy uses firm-scoped row-level isolation | Accepted | 2026-01-16 |
| [ADR-006](ADR-006-firm-scoped-query-enforcement.md) | Enforce firm-scoped queries as the default data access pattern | Accepted | 2026-01-16 |
| [ADR-007](ADR-007-break-glass-access-control.md) | Require break-glass sessions for platform operator content access | Accepted | 2026-01-16 |
| [ADR-008](ADR-008-ledger-first-billing.md) | Use a ledger-first billing model with immutable entries | Accepted | 2026-01-16 |

## Related Documents

- [Coding Constitution](../codingconstitution.md)

---

**Last Updated:** 2026-01-16  
**Owner:** Architecture Team  
**Evidence Sources:**
- [ADR-0000](ADR-0000-template.md)
- [ADR-004](ADR-004-esignature-provider-selection.md)
- [ADR-005](ADR-005-multi-tenancy-row-level-isolation.md)
- [ADR-006](ADR-006-firm-scoped-query-enforcement.md)
- [ADR-007](ADR-007-break-glass-access-control.md)
- [ADR-008](ADR-008-ledger-first-billing.md)
