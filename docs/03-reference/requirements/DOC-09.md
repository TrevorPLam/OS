# Pricing Engine Specification (PRICING_ENGINE_SPEC)

This document defines the pricing engine: the versioned JSON rule schema, evaluation context, evaluation outputs (including trace), and snapshotting rules into QuoteVersion.

This document is normative. If it conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals

1. Pricing MUST be reproducible and explainable.
2. Pricing MUST be auditable at the time of agreement.
3. Pricing rules MUST be versioned and snapshot-able.
4. Pricing evaluation MUST produce a trace that can be reviewed by staff and used for dispute/audit resolution.
5. The engine MUST support non-linear service structures common in professional services (tiers, add-ons, bundles, discounts, minimums).

---

## 2) Core concepts

### 2.1 RuleSet
A RuleSet is a named collection of pricing rules under a specific schema version.

Fields (conceptual):
- `ruleset_id`
- `ruleset_version` (semantic version or monotonic int)
- `schema_version` (pricing JSON schema version)
- `status` (draft | published | deprecated)
- `published_at`
- `checksum` (hash of normalized rules JSON)

Invariants:
- Published RuleSets MUST be immutable.
- A QuoteVersion MUST reference the exact RuleSet (id + version + checksum).

### 2.2 Quote and QuoteVersion
- Quote is the mutable working draft (optional).
- QuoteVersion is the immutable snapshot used for issuance/acceptance/audit.

A QuoteVersion MUST snapshot:
- evaluation context (bounded; see Section 4)
- ruleset reference (id/version/checksum)
- evaluation outputs
- evaluation trace
- issuance/acceptance metadata

---

## 3) JSON rule schema (high-level)

The engine consumes a JSON document conforming to a versioned schema.

### 3.1 Schema versioning
1. The schema MUST include `schema_version`.
2. Backwards-incompatible changes MUST increment major version.
3. The evaluator MUST reject rulesets with unknown schema versions unless an explicit compatibility layer exists.

### 3.2 Recommended top-level structure
Example shape (illustrative, not exhaustive):

- `schema_version`
- `ruleset_id`
- `ruleset_version`
- `currency` (default)
- `definitions` (reusable components)
- `products` (service offerings / line definitions)
- `rules` (pricing rules)
- `constraints` (global constraints, minimums, caps)
- `output_map` (how outputs are structured)
- `metadata` (labels, UI hints; non-normative)

### 3.3 Product / service line model
A product entry SHOULD represent a billable service line (maps naturally to EngagementLine).

Fields (typical):
- `product_code` (stable)
- `name`
- `description`
- `billing_model` (fixed | recurring | usage | hybrid)
- `unit` (month | quarter | project | hour | transaction)
- `default_quantity`
- `eligibility` (optional expression)
- `base_price` (optional)
- `components` (optional nested items)
- `tags` (for UI grouping)

Invariant:
- Pricing outputs MUST be representable as one or more EngagementLines.

---

## 4) Evaluation context (inputs)

Evaluation context is the structured input to pricing evaluation. It MUST be explicit, typed, and snapshot-able.

### 4.1 Context categories
Recommended categories:

A) Client / account context
- account type (org/individual)
- industry (optional)
- entity count (optional)
- locations (optional)

B) Engagement intent
- desired service package(s)
- start date / term length
- billing frequency preferences

C) Volume / complexity drivers
- transaction volume (monthly)
- bank accounts, credit cards
- payroll headcount
- number of entities/books
- historical backlog months
- cleanup severity indicators

D) Add-ons / options
- advisory add-ons
- sales tax, inventory, multi-currency, etc.

E) Constraints / discounts
- promo codes (optional)
- partner discounts (optional)
- minimum fee enforcement flag

### 4.2 Input typing and validation
1. Context MUST be validated before evaluation.
2. Unknown fields MUST be rejected or placed into an explicit `extensions` bag that is ignored by the evaluator unless whitelisted.

### 4.3 Snapshotting context
1. QuoteVersion MUST store a snapshot of the evaluation context used to produce results.
2. Snapshot MUST be bounded:
   - do not embed full account PII
   - store only fields required to reproduce evaluation
3. Snapshot MUST include timezone and currency where relevant.

---

## 5) Rule evaluation semantics

### 5.1 Determinism
1. Given identical:
   - ruleset (id/version/checksum),
   - evaluation context snapshot,
   - engine version (if applicable),
the engine MUST produce identical outputs and trace.

2. Evaluation MUST NOT depend on:
   - current wall-clock time (unless time is an explicit input in context)
   - external API calls during evaluation

### 5.2 Rule types (recommended)
The schema SHOULD support the following rule types:

- Eligibility rules
  - determine which products/tiers apply

- Pricing rules
  - compute base price, tier price, usage price

- Modifiers
  - discounts, surcharges, minimums, caps

- Bundles
  - package compositions, included quantities, bundle pricing

- Output shaping
  - map internal computed items into a stable output contract

### 5.3 Expression language (requirements)
1. If expressions are used (e.g., `if`, `and`, comparisons), the expression language MUST be:
   - sandboxed (no arbitrary code)
   - deterministic
   - validated with clear error messages
2. Expressions MUST support referencing only:
   - context fields
   - computed intermediate values
   - constants/definitions in the ruleset

---

## 6) Outputs (evaluation result contract)

### 6.1 Required outputs
The evaluator MUST output:

1. `line_items` (list)
Each line item SHOULD map to an EngagementLine candidate.

Fields (typical):
- `product_code`
- `name`
- `quantity`
- `unit_price`
- `amount`
- `billing_model` (fixed/recurring/usage)
- `unit` (month/quarter/etc.)
- `notes` (optional)
- `tax_category` (optional)

2. `totals`
- subtotal
- discounts
- taxes (optional)
- total

3. `assumptions`
- list of assumption statements derived from context and rules (for review)

4. `warnings`
- validation or policy warnings (e.g., “volume exceeds tier bounds; defaulting to highest tier”)

### 6.2 Trace output (required)
The evaluator MUST produce a trace containing:
- ruleset reference (id/version/checksum/schema_version)
- ordered list of evaluation steps
- per-step:
  - rule id/name
  - inputs used
  - intermediate values
  - outcome (applied/skipped)
  - reasons (eligibility decisions)
- final outputs checksum

Trace MUST be:
- machine-readable (JSON)
- safe to store (redacted of HR data; follow DATA_GOVERNANCE.md)

---

## 7) QuoteVersion snapshotting rules

### 7.1 Snapshot immutability
1. Once a QuoteVersion is `accepted`, it MUST be immutable.
2. Any change requires a new QuoteVersion.

### 7.2 Binding to Engagement / EngagementLines
1. Engagement activation MUST reference the accepted QuoteVersion.
2. EngagementLines created from pricing MUST retain:
   - `product_code`
   - reference to QuoteVersion
   - reference to the line item id (stable within QuoteVersion)

### 7.3 Pricing rule evolution
1. Published RuleSets MAY evolve across time, but existing QuoteVersions MUST remain reproducible via:
   - stored ruleset checksum reference
   - stored context snapshot
   - stored outputs and trace

---

## 8) Idempotency and concurrency

1. Quote issuance and acceptance operations MUST be idempotent.
2. If multiple accept attempts occur, the system MUST ensure:
   - only one accepted QuoteVersion per acceptance action
   - no double-activation of the Engagement

---

## 9) API requirements (high-level)

Exact endpoints are defined in API_CONTRACTS.md. Minimum behaviors:

1. Evaluate quote (draft)
- input: context + selected products/options
- output: evaluation result + trace

2. Issue quote version
- input: evaluation result reference or re-evaluation request
- output: QuoteVersion id + immutable snapshot

3. Accept quote version
- actor: staff or portal (policy-defined)
- output: acceptance record + optional engagement activation trigger

4. Retrieve quote version
- includes outputs + trace (permission-gated)

---

## 10) Validation and testing requirements

The platform MUST include contract tests for:
1. Determinism: same inputs produce identical outputs/trace.
2. Schema validation: invalid rulesets are rejected with actionable errors.
3. Backward compatibility: when schema changes, old rulesets remain evaluable or explicitly blocked.
4. Trace completeness: applied/skipped rules produce explainable outcomes.
5. Edge cases: volume bounds, missing optional fields, promo conflicts, minimum fee enforcement.

---

## 11) Open items

1. Authoring surface:
- Will rules be edited directly as JSON, or through a UI that compiles to JSON?

2. Expression language choice:
- custom minimal DSL vs JSON-logic-like expression structure

3. Discount stacking policy:
- whether multiple discounts can stack, and ordering rules

4. Tax handling:
- whether taxes are in-scope in V1 (if not, outputs must still allow future extension)

These must be resolved via DECISION_LOG.md and reflected here.

---

