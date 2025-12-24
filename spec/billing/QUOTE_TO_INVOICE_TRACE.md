# Quote → Invoice Lineage Trace

## Lineage objects and links
- **Quote** (`quote_id`) → **Acceptance** (`acceptance_id`) → **Invoice** (`invoice_id`) → **Adjustments** (`adjustments[]`).

## Immutable elements by step
- **Quote**: Quote record content and identifier are immutable once issued.
- **Acceptance**: Acceptance captures the approval of a specific quote; acceptance identifiers are immutable.
- **Invoice**: Invoice identifiers and issued invoice content are immutable once finalized.
- **Adjustments**: Adjustments are append-only records; they never overwrite invoices or invoice lines.

## Trace rules
- Each invoice must reference the acceptance that justified issuance.
- Each adjustment must reference the invoice (and line if applicable) it affects.
- Historical links are never mutated; corrections are represented as new adjustment records.
