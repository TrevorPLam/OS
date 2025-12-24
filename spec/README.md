# Specifications Index

These specifications codify frozen seam decisions into reviewable, testable build contracts.
They do not introduce new product decisions and are intended for implementation alignment.

## Index
- [System Invariants](SYSTEM_INVARIANTS.md)
- Billing
  - [Invoice Line Schema](billing/INVOICE_LINE.schema.json)
  - [Adjustments Schema](billing/ADJUSTMENTS.schema.json)
  - [Quote to Invoice Trace](billing/QUOTE_TO_INVOICE_TRACE.md)
- Contracts
  - [PM → Billing BillableEvent Schema](contracts/PM_BILLING_BILLABLE_EVENT.schema.json)
  - [PM → Billing Contract](contracts/PM_BILLING_CONTRACT.md)
- DMS
  - [Binding References](dms/BINDING_REFERENCES.md)
- Portal
  - [Portal Surface Spec](portal/PORTAL_SURFACE_SPEC.md)
- Reporting
  - [Reporting Metadata](reporting/REPORTING_METADATA.md)
- [Spec Completeness Checklist](CHECKLIST.md)

## How to use these specs
- Treat schemas as validation contracts for emitted/consumed data.
- Treat markdown specs as invariants and implementation guardrails.
- Do not reinterpret or expand these documents without explicit updates to frozen decisions.
