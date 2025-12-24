# PM → Billing Contract

## Purpose
Define the seam where PM emits BillableEvents and Billing consumes them to generate invoice lines. This contract is limited to existing frozen decisions and does not introduce new behaviors.

## Emission (PM)
- PM emits a **BillableEvent** only after internal approval (`approved_by`, `approved_at`).
- Each BillableEvent must include:
  - `billable_event_id` (immutable)
  - `client_id`
  - `engagement_id` or `project_id` (anchor)
  - `work_item_ref` (when a task/work item is the source)
  - `event_type` and typed `event_payload`
  - `approved_by`, `approved_at`
  - `overrides` metadata if an exception is allowed

## Consumption (Billing)
- Billing accepts BillableEvents as **triggers** for invoice line creation.
- **One trigger per invoice line**: each invoice line references exactly one BillableEvent or internal approval record in `trigger_ref`.
- Billing stores the BillableEvent identifier and approval metadata as part of the line’s audit trail.

## Overrides
- Overrides are **explicit, auditable metadata** on the BillableEvent (`overrides.allowed`, `overrides.justification`, `overrides.approver`).
- Billing must not infer or apply silent overrides; it only accepts overrides when explicitly provided.

## Non-mutation guarantees
- BillableEvents are immutable once emitted.
- Billing does not alter or overwrite BillableEvents; corrections are handled via adjustments on billing records.
