# Recurrence Engine Specification (RECURRENCE_ENGINE_SPEC)

This document defines the recurrence engine: period definition rules, timezone policy, recurrence generation semantics, uniqueness constraints, worker processing algorithm, and pause/resume/cancel behavior.

This document is normative. If it conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals

1. The system MUST generate recurring work deterministically and without duplicates.
2. The system MUST behave correctly across timezones and DST transitions.
3. Recurrence generation MUST be safe under retries and concurrency.
4. The system MUST provide traceability for:
   - what was supposed to generate
   - what did generate
   - why something did or did not generate

---

## 2) Core concepts

### 2.1 RecurrenceRule
A definition of “what repeats” and “how to compute periods.”

Conceptual fields:
- `recurrence_rule_id`
- `scope` (WorkItemTemplateNode | DeliveryTemplate | EngagementLine | Engagement)
- `anchor_type` (calendar | fiscal | custom)
- `frequency` (daily | weekly | monthly | quarterly | yearly)
- `interval` (integer, default 1)
- `by_day` (optional; for weekly rules)
- `by_month_day` (optional; for monthly rules)
- `time_of_day` (optional; for deadlines/appointments)
- `timezone` (required; see Section 3)
- `start_at` (required)
- `end_at` (optional)
- `status` (active | paused | canceled)

Invariants:
- RecurrenceRule MUST be validated at creation/update time.
- If `end_at` is absent, the rule is open-ended.

### 2.2 Period
A computed interval representing a single recurrence instance (e.g., “January 2026 monthly close”).

A Period MUST have:
- `period_key` (stable string; see Section 4)
- `starts_at`, `ends_at` (in UTC, but derived from timezone-aware boundaries)
- `label` (human-friendly; e.g., “2026-01”)

### 2.3 RecurrenceGeneration (dedupe ledger)
A RecurrenceGeneration record represents the “fact” that the system generated (or attempted to generate) the instance for a given period.

RecurrenceGeneration MUST include:
- `recurrence_rule_id`
- `period_key`
- `target_object_type` (WorkItem | Appointment | other if extended)
- `target_object_id` (nullable until created)
- `status` (planned | generated | skipped | failed)
- `generated_at` (nullable)
- `idempotency_key` (see Section 5)
- `reason` (for skipped)
- `error` (redacted error summary for failed)
- `attempt_count`
- `last_attempt_at`

Invariants:
- RecurrenceGeneration MUST be the dedupe source of truth.
- Work generation MUST NOT bypass this table.

---

## 3) Timezone policy

### 3.1 Timezone authority
1. Every RecurrenceRule MUST specify a timezone.
2. If a tenant has a default timezone, it MAY be used as a default for new rules, but the rule MUST store its resolved timezone explicitly.

### 3.2 DST behavior
1. Period boundary calculations MUST be timezone-aware.
2. If a period includes a DST shift, the period MUST still represent the correct local boundaries.
3. When `time_of_day` is specified:
   - if local time is ambiguous (DST fall-back), the engine MUST choose a consistent policy:
     - policy A (recommended): pick the first occurrence
     - policy B: pick the second occurrence
   - the chosen policy MUST be documented and tested.

### 3.3 Deterministic clock
All recurrence calculations MUST be based on an explicit “as_of” time passed into the generator, not implicit wall-clock time, to support deterministic testing.

---

## 4) Period definition rules

### 4.1 Period key
Each generated instance MUST have a stable `period_key` string that is used for uniqueness.

Recommended format:
- monthly: `YYYY-MM` (e.g., `2026-01`)
- quarterly: `YYYY-QN` (e.g., `2026-Q1`)
- weekly: `YYYY-Www` (ISO week, e.g., `2026-W05`)
- daily: `YYYY-MM-DD`

If fiscal calendars are supported later, period_key MUST include fiscal markers (e.g., `FY2026-P01`).

### 4.2 Monthly periods
Monthly period boundaries:
- starts_at = first day of month at 00:00:00 local time
- ends_at = first day of next month at 00:00:00 local time

### 4.3 Quarterly periods
Quarter boundaries:
- Q1 = Jan–Mar, Q2 = Apr–Jun, Q3 = Jul–Sep, Q4 = Oct–Dec
- starts_at = first day of quarter 00:00:00 local
- ends_at = first day of next quarter 00:00:00 local

### 4.4 Weekly periods
Weekly boundaries (choose one and enforce consistently):
- Option A: ISO weeks (recommended)
- Option B: tenant-configured week start day

The chosen option MUST be recorded in DECISION_LOG.md and tested.

### 4.5 Custom periods (optional)
If custom periods are introduced:
- the period_key definition MUST be explicit
- uniqueness constraints MUST still hold

---

## 5) Uniqueness and idempotency

### 5.1 Uniqueness constraint (normative)
The system MUST enforce a uniqueness constraint that prevents duplicates:

Unique key (minimum):
- `(recurrence_rule_id, period_key)`

If a rule can target multiple objects per period, extend the unique key with:
- `target_discriminator` (e.g., template_node_id)

Example unique key:
- `(recurrence_rule_id, period_key, template_node_id)`

### 5.2 Idempotency key strategy
Each generation attempt MUST have an idempotency key derived from the unique key:

`idempotency_key = hash(tenant_id + recurrence_rule_id + period_key + discriminator)`

This key MUST be used by:
- worker job payloads
- downstream creation calls (e.g., WorkItem create)

---

## 6) Worker processing algorithm

### 6.1 Inputs
The generator runs for a tenant and a time window:
- `tenant_id`
- `as_of` (timezone-aware)
- `lookback_window` (optional; for recovery)
- `lookahead_window` (required; generate upcoming periods)

### 6.2 High-level algorithm (normative)
For each active RecurrenceRule:
1. Compute candidate periods within the generation window using timezone-aware boundaries.
2. For each candidate period:
   a) Attempt to insert RecurrenceGeneration with unique key `(rule_id, period_key, discriminator)`.
   b) If insert succeeds:
      - enqueue a generation job for that RecurrenceGeneration id (or proceed inline).
   c) If insert fails due to uniqueness:
      - do nothing (already planned/generated), unless status indicates failed and retry policy allows reprocessing.

3. Worker job execution:
   a) Acquire concurrency control:
      - advisory lock keyed by idempotency_key OR
      - DB row lock on RecurrenceGeneration with SKIP LOCKED
   b) Load RecurrenceGeneration; if status is generated/skipped, exit (idempotent).
   c) Create the target object (e.g., WorkItem) in an idempotent manner:
      - include idempotency_key in create call
      - apply unique constraints on target if needed (e.g., WorkItem unique by recurrence_generation_id)
   d) Update RecurrenceGeneration:
      - status = generated
      - target_object_id
      - generated_at
   e) On non-retryable errors:
      - status = failed
      - store redacted error summary
      - enqueue DLQ if applicable

### 6.3 Required idempotency and safety
1. All generator and worker operations MUST be safe under:
   - retries
   - duplicate job dispatch
   - concurrent workers
2. The system MUST NOT create duplicate WorkItems for a given RecurrenceGeneration unique key.

---

## 7) Pause, resume, cancel semantics

### 7.1 Pause
When a rule is paused:
1. No new RecurrenceGeneration rows SHOULD be created for periods after the pause effective time.
2. Existing planned generations MAY remain, but:
   - jobs should stop generating new WorkItems unless explicitly allowed
   - a “paused” check MUST occur at execution time as well (defense in depth)

### 7.2 Resume
When resumed:
1. The generator MUST continue creating RecurrenceGeneration rows for future periods.
2. The system MAY support backfilling missed periods via an explicit “backfill” operation that:
   - is permission-gated
   - is auditable
   - is bounded by a specified time range

### 7.3 Cancel
When canceled:
1. No new generations occur after cancellation.
2. Previously generated WorkItems MUST NOT be deleted automatically unless explicitly requested; cancel affects future generation, not history.
3. The cancellation MUST be auditable.

---

## 8) Skip behavior

The engine MUST support “skipped” outcomes when generation is not appropriate, with explicit reasons.

Examples:
- Engagement not active during period
- Template disabled
- Legal hold blocks creation
- Capacity cap (if implemented later)

Skip MUST record:
- status = skipped
- reason code
- reason message (bounded)

---

## 9) Observability requirements

The system MUST provide:
- metrics per tenant:
  - generated count
  - skipped count
  - failed count
  - latency (time from planned to generated)
- logs with correlation IDs and idempotency keys
- audit events for:
  - pause/resume/cancel actions
  - backfill operations
  - manual reprocessing

---

## 10) Testing requirements (minimum)

Contract tests MUST cover:
1. DST transitions (spring forward, fall back) for at least two timezones.
2. Leap year behavior for daily/monthly rules.
3. Concurrency: two workers racing the same generation.
4. Retry safety: duplicate job dispatch does not create duplicates.
5. Pause/resume and backfill behavior.
6. Period key correctness and stability across runs.

---

## 11) Open items

1. Week definition choice (ISO vs tenant-configurable week start).
2. Fiscal calendar support (if required).
3. Whether recurrence can generate beyond WorkItems (appointments, invoices) in V1.

These must be resolved via DECISION_LOG.md and reflected here.

---

