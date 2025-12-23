# 🔒 TIER 4 EXECUTION PROMPT — BILLING & MONETIZATION

You are executing Tier 4 only of a multi-tier build.
Tier 4 implements engagement-centric billing with package + hourly + mixed, credit ledger, autopay, and explicit failure/dispute handling. No Tier 5 scale/exit work.

## Authority

* `/docs/claude/NOTES_TO_CLAUDE.md` is authoritative.
* Assume Tier 0–3 are implemented. Do not weaken tenant/privacy/audit rules to make billing work.

## Scope (WHAT YOU MAY DO)

You may modify only what is required to implement:

1. Engagement-centric invoicing (invoice belongs to client; default requires engagement link)
2. Package fee invoicing (scheduled/auto invoice generation)
3. Hourly billing (time entries + staff/admin approval gate; optional client approval ready)
4. Mixed billing (package + hourly on one invoice)
5. Credit ledger (auditable credit balance and application)
6. Recurring payments (autopay invoices as issued)
7. Payment failures + disputes + chargebacks as first-class events
8. Renewal billing continuity (no retroactive mutation)

### Explicitly IN SCOPE

* Models and logic for:
  * engagements billing terms (package/hourly/mixed)
  * invoices + invoice line items (no plaintext "context" in platform logs)
  * time entries, approval states, billing inclusion gates
  * credit ledger entries and balance computation
  * payment methods (secure references), payment attempts, payment events
  * dispute/chargeback event tracking
* Default behavior:
  * invoice must link to engagement (Master Admin can override explicitly)
  * unapproved time cannot be invoiced
  * autopay triggers on invoice issuance
* Audit events (metadata only) for:
  * invoice issued
  * payment attempted / succeeded / failed
  * dispute opened / resolved
  * chargeback received
  * credits issued/applied
* Strict "no history mutation" rules:
  * renewal creates new engagement; past invoices remain unchanged

### Explicitly OUT OF SCOPE (DO NOT TOUCH)

* Pricing calculator module (configurable CPQ) beyond basic "firm enters package fee"
* Full accounting integrations
* Tier 5 (performance, exit flows, observability)
* UI polish beyond what is required to validate workflows
* Any change that exposes customer content to platform roles

## Invariants (MUST HOLD)

* Billing traces back to engagement terms by default.
* Signed engagements remain immutable; renewals do not rewrite history.
* Time entries are not invoiceable until approved.
* Credits are ledger-based (auditable).
* Payment failures/disputes do not corrupt invoice state.
* Platform retains billing metadata only; no customer content is logged.

## Execution Steps (DO THESE IN ORDER)

1. Confirm engagement billing term structure:
   * pricing_mode: package/hourly/mixed
   * package amount + cadence + start/end
   * hourly rates and rules (as minimal viable)
2. Implement invoice rules:
   * invoice belongs to client
   * default requires engagement_id (override flag controlled by Firm Master Admin)
   * optional project linkage
3. Implement package auto-invoicing:
   * scheduled job creates invoices from engagement terms
   * idempotent (no duplicates)
4. Implement hourly workflow:
   * time entry creation
   * approval states: draft/approved/rejected
   * only approved entries can be included on invoices
   * client approval optional (data model ready)
5. Implement mixed invoices:
   * invoice supports package line(s) + hourly line(s)
   * reporting clarity (separate categories)
6. Implement credit ledger:
   * credit issuance event
   * credit application event
   * balance derived from ledger entries
7. Implement autopay:
   * stored payment method references
   * on invoice issuance: attempt payment
   * record payment attempt outcomes
8. Implement failure + dispute + chargeback events:
   * event types and lifecycle
   * link to invoice/payment
   * preserve history and metadata
9. Implement renewal continuity:
   * renewal creates new engagement with new terms
   * no retroactive changes to invoices/payments for prior engagement
10. Add minimal billing invariant tests:
    * invoice requires engagement by default
    * unapproved time cannot be invoiced
    * mixed invoice totals reconcile
    * chargeback/dispute does not flip invoice state incorrectly

## Completion Checklist (STOP WHEN TRUE)

* [ ] Package invoicing can run on schedule without duplicates.
* [ ] Hourly time cannot be billed unless approved.
* [ ] Mixed invoices work (fixed + variable) and reconcile totals.
* [ ] Credits are ledger-based and auditable.
* [ ] Autopay triggers on invoice issuance; failures are recorded cleanly.
* [ ] Disputes/chargebacks are tracked as explicit events and do not delete history.
* [ ] Renewals do not mutate past invoices.

## Output Requirements

Before stopping, report:

1. Billing data model summary (engagement terms, invoices, time entries, credits, payments, disputes)
2. Default rules + override rules (engagement link requirement)
3. Package invoicing idempotency mechanism
4. Time approval gating mechanism
5. Credit ledger mechanics and reconciliation approach
6. Autopay workflow and failure paths
7. Dispute/chargeback event lifecycle
8. Renewal continuity guarantees
9. Tests added and what they assert
10. What was intentionally NOT touched

## Stop Conditions

* If payment processor choice or legal policy is required: STOP AND ASK (do not guess).
* Do not proceed to Tier 5.
* No shortcuts that weaken auditability or tenant/privacy boundaries.
