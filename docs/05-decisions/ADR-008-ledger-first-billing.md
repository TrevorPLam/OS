# ADR-008: Use a ledger-first billing model with immutable entries

**Purpose:** Document the decision to implement billing as an immutable ledger with derived balances.

**Audience:** Developers, Finance Operations, Auditors

**Evidence Status:** STATIC-ONLY

---

**Status:** Accepted  
**Date:** 2026-01-16  
**Deciders:** Platform/Finance Engineering  
**Tags:** billing, audit, data-integrity

## Context and Problem Statement

Billing and financial reporting require an auditable source of truth. Mutable invoice
records alone are insufficient for compliance and reconciliation. The codebase implements
a ledger-first billing system where all money-impacting actions are immutable ledger
entries, and balances are derived from ledger allocations. This ADR records that
decision so financial logic remains consistent across modules.

**Code Commentary (Mapping):**
- **Ledger entries:** `BillingLedgerEntry` enforces immutability and uses idempotency keys
  to prevent duplicate postings for the same firm and entry type.
- **Derived balances:** Helper functions calculate accounts receivable and retainer balances
  directly from ledger entries and allocations.

## Decision Drivers

- Need for immutable, auditable financial records.
- Support for reconciliation and derived balances without relying on mutable state.
- Clear separation between operational invoices/payments and ledger truth.

## Considered Options

1. **Mutable invoice/payment records only** (Pros: simpler models; Cons: weak audit trail,
   difficult reconciliation).
2. **Ledger-first billing with immutable entries** (Pros: strong auditability, deterministic
   balances; Cons: additional modeling complexity).
3. **Hybrid with soft locks** (Pros: easier corrections; Cons: weaker audit guarantees).

## Decision Outcome

Chosen option: **Ledger-first billing with immutable entries**, because it provides the
strongest audit trail and deterministic financial reporting.

All money-impacting actions are recorded as immutable ledger entries. Invoices and balances
are derived from ledger entries and allocations, not from mutable state.

### Positive Consequences

- Strong audit trail with immutable entries and idempotency safeguards.
- Deterministic balances derived from ledger data.
- Clear foundation for reconciliation and compliance workflows.

### Negative Consequences

- Corrections require compensating entries rather than updates.
- Additional complexity in ledger allocation logic and reporting.

## Implementation Plan

### Migration Steps

1. Continue using `BillingLedgerEntry` for all money-impacting actions.
2. Use ledger helper functions to derive balances and invoice status.
3. Maintain idempotency keys to prevent duplicate ledger postings.

### Rollback Plan

If reverting to mutable billing records:

1. Remove ledger enforcement and convert balances to mutable fields.
2. Update reporting logic to rely on invoice/payment state instead of ledger entries.

### Success Criteria

- [ ] Money-impacting actions are represented as immutable ledger entries.
- [ ] Balance calculations derive from ledger entries and allocations.

## Constitution Impact

Not applicable.

## Related Decisions

- [ADR-005: Multi-tenancy uses firm-scoped row-level isolation](ADR-005-multi-tenancy-row-level-isolation.md)

## Links

- [Billing ledger implementation](../../src/modules/finance/billing_ledger.py)
- [Billing ledger implementation guide](../BILLING_LEDGER_IMPLEMENTATION.md)

---

## Notes

This ADR documents the implemented ledger-first billing model and its immutability
requirements.

**Change Log:**

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Initial draft | AGENT |

---

**Last Updated:** 2026-01-16  
**Evidence Sources:** src/modules/finance/billing_ledger.py; docs/BILLING_LEDGER_IMPLEMENTATION.md
