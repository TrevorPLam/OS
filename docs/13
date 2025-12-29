# Billing Ledger Specification (BILLING_LEDGER_SPEC)

Defines a ledger-first billing system for invoices, payments, retainers, and allocations.
Normative. If conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals
1. All money-impacting actions MUST be represented as immutable ledger entries.
2. Balances and reports MUST be explainable from ledger entries.
3. Posting operations MUST be idempotent and auditable.
4. Retainers and allocations MUST have explicit constraints.

---

## 2) Core concepts

### 2.1 LedgerEntry (immutable)
Conceptual fields:
- ledger_entry_id
- entry_type (invoice_issued | payment_received | retainer_deposit | retainer_applied | credit_memo | adjustment | write_off)
- account_id (required)
- invoice_id (nullable)
- engagement_id / engagement_line_id (nullable)
- amount (signed; currency required)
- currency
- occurred_at (business time)
- posted_at (system time)
- idempotency_key (required for posting APIs)
- reference (external processor ref, check number, etc. — governed)
- metadata (bounded)
- created_by_actor + correlation_id

Invariants:
- LedgerEntry MUST NOT be edited after posting.
- Corrections MUST occur via compensating entries.

### 2.2 Allocation
Allocations map value from one entry to another (e.g., payment applied to invoice; retainer applied to invoice).

Conceptual fields:
- allocation_id
- from_ledger_entry_id
- to_ledger_entry_id
- amount (positive)
- created_at, created_by_actor

Constraints:
- Sum(allocations from an entry) MUST NOT exceed available unapplied amount.
- Allocations MUST be idempotent (unique key or derived from idempotency key).

---

## 3) Entry types and semantics (minimum)

1. invoice_issued
- Creates AR for an invoice.
- amount MUST be positive.

2. payment_received
- Reduces AR when allocated to invoices.
- amount MUST be positive.
- Unallocated payments are allowed but must be visible in reports.

3. retainer_deposit
- Increases retainer balance.
- amount positive.

4. retainer_applied
- Moves value from retainer to invoice (typically via allocation semantics).
- Implement as either:
  A) allocation from retainer_deposit to invoice_issued, or
  B) explicit retainer_applied entry + allocation links
Choose one and enforce consistently.

5. credit_memo / adjustment
- Reduces AR or adjusts balances; requires explicit reason codes.

6. write_off
- Marks uncollectible AR; requires policy + audit.

---

## 4) Reporting outputs (derived)

Must be derivable from entries + allocations:

- AR balance by account
- AR aging by invoice (requires invoice issued_at/due_at)
- Retainer balance by account
- Earned revenue (policy-defined; may require service delivery linkage; if deferred, mark as out-of-scope)

Reports MUST be explainable (drill-down to entries and allocations).

---

## 5) Idempotency requirements
1. Posting endpoints MUST accept idempotency keys.
2. The system MUST enforce uniqueness on idempotency_key scoped to tenant + entry_type.
3. Replaying a request with same key MUST return the original posted entry.

---

## 6) Invoice integration rules
1. Invoice status MUST reconcile with allocations:
- issued → partially_paid when allocated payments < invoice amount
- → paid when allocated payments == invoice amount
2. Voids/write-offs MUST produce compensating entries; never delete history.

---

## 7) Permissions and audit
- Only Billing/Admin roles can post payments, issue invoices, apply retainers, write off.
- All posting, voiding, and allocation actions MUST create audit events.

---

## 8) Testing requirements
- Idempotent posting
- Allocation constraints (over-allocation prevented)
- Partial payments and retainer applications
- Void/write-off correctness
- Report derivations and explainability

---
