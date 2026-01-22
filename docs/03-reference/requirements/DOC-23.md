# Edge Cases Catalog (EDGE_CASES_CATALOG)

Catalog of known tricky cases that must be handled and tested.

---

## 1) Recurrence
- DST spring forward: missing local times
- DST fall back: ambiguous local times
- leap year Feb 29 rules
- pause mid-period then resume (no duplicates)
- backfill window overlaps previously generated periods

## 2) Email ingestion
- shared email address across multiple accounts
- thread contains mixed clients
- subject changes mid-thread
- attachments renamed across replies
- re-ingestion after connection reset (idempotency)

## 3) Permissions
- portal identity linked to multiple accounts; account switcher scope correctness
- document linked to multiple objects with mixed portal visibility
- role changes mid-session; token refresh and cached permissions

## 4) Billing ledger
- partial payments across multiple invoices
- retainer partially applied, then invoice voided (compensation entries)
- idempotency key reuse across retries
- allocation rounding/currency precision

## 5) Documents
- concurrent uploads without locks (should create versions or block)
- lock override by admin (audit)
- malware scan pending: portal download blocked
- signed URL reuse after expiry

---
