# Orchestration Engine Specification (ORCHESTRATION_ENGINE_SPEC)

This document defines the orchestration engine: execution model, step semantics, retries, DLQ, idempotency, error classification, and compensation boundaries.

Orchestration is not the same as Delivery Templates:
- Delivery Templates define the plan of work (WorkItems) as a DAG.
- Orchestration defines machine-enforced execution control (steps, retries, safe side effects).

This document is normative. If it conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals

1. Orchestration MUST enable reliable automation of cross-step processes with safe retries.
2. The engine MUST be resilient to partial failures, duplicated jobs, and concurrency.
3. The engine MUST provide explicit observability:
   - what ran
   - what failed
   - what retried
   - why something is blocked
4. Orchestration MUST support compensation boundaries for steps that cannot be safely retried.

---

## 2) Core concepts

### 2.1 OrchestrationDefinition
Defines a workflow template (steps + transitions + policies).

Conceptual fields:
- `orchestration_definition_id`
- `name`
- `version`
- `status` (draft | published | deprecated)
- `steps[]` (see 2.2)
- `policies` (timeouts, retry policies, concurrency)
- `input_schema` (validation)
- `output_schema` (optional)

Invariants:
- Published definitions MUST be immutable.
- Executions MUST reference a specific published definition version.

### 2.2 Step
A step is a unit of orchestration work with explicit side-effect boundaries.

Step fields (conceptual):
- `step_id` (stable within definition)
- `name`
- `type` (task | decision | wait | external_call | notify | human_approval)
- `handler` (service/action reference)
- `timeout_ms`
- `retry_policy` (see Section 5)
- `idempotency_strategy` (see Section 6)
- `compensation_handler` (optional)
- `on_success` (next step reference)
- `on_failure` (next step reference or terminal)
- `on_timeout` (next step reference or terminal)

### 2.3 OrchestrationExecution
Represents a single run of a definition for a specific target.

Conceptual fields:
- `execution_id`
- `definition_id`, `definition_version`
- `status` (running | succeeded | failed | canceled | paused | waiting_approval)
- `tenant_id`
- `target_object_type` (Engagement | WorkItem | Invoice | etc.)
- `target_object_id`
- `input` (validated snapshot)
- `output` (optional)
- `started_at`, `completed_at`
- `correlation_id` (root)
- `idempotency_key` (execution-level)
- `attempt_count` (for execution restarts; optional)

Invariants:
- Execution MUST be idempotent at the creation boundary (same idempotency_key => same execution).
- Execution MUST store sufficient data to reconstruct what happened (step history).

### 2.4 StepExecution
Represents an attempt of a specific step within an execution.

Fields (conceptual):
- `step_execution_id`
- `execution_id`
- `step_id`
- `status` (pending | running | succeeded | failed | retrying | timed_out | skipped | awaiting_approval)
- `attempt_number`
- `started_at`, `finished_at`
- `error_class` (see Section 4)
- `error_summary` (redacted)
- `retry_after_at` (if scheduled)
- `idempotency_key` (step-level)
- `result` (bounded)
- `logs_ref` (optional pointer to external logs)

Invariants:
- StepExecution is append-only in history; retries create new attempts, not overwrite history.

---

## 3) Execution lifecycle

### 3.1 Execution statuses
- running
- waiting_approval
- paused
- succeeded
- failed
- canceled

Allowed transitions:
- running → waiting_approval
- waiting_approval → running (after approval)
- running → paused
- paused → running
- running → succeeded
- running → failed
- running → canceled
- paused → canceled
- waiting_approval → canceled

### 3.2 Step statuses
- pending
- running
- succeeded
- failed
- retrying
- timed_out
- skipped
- awaiting_approval

---

## 4) Error classification (normative)

Errors MUST be classified to determine retry behavior and DLQ routing.

Minimum classes:
- TRANSIENT
  - network timeouts, temporary service unavailability
- RETRYABLE
  - known retry-safe domain errors (e.g., optimistic lock conflict)
- NON_RETRYABLE
  - validation errors, permission errors, invariant violations
- RATE_LIMITED
  - external service rate limit; requires backoff
- DEPENDENCY_FAILED
  - upstream dependency failure that might resolve (treated like RETRYABLE with longer backoff)
- COMPENSATION_REQUIRED
  - partial side effect occurred and cannot be safely retried without compensation

Classification MUST be deterministic from error type/codes and documented in a retry matrix.

---

## 5) Retry policy and retry matrix

### 5.1 Retry policy fields
Each step MUST specify:
- `max_attempts`
- `backoff_strategy` (fixed | exponential | jittered)
- `initial_delay_ms`
- `max_delay_ms`
- `timeout_ms` (per attempt)
- `retry_on_classes[]` (subset of error classes)

### 5.2 Retry matrix (minimum)
- TRANSIENT: retry (bounded attempts, exponential backoff)
- RATE_LIMITED: retry (respect Retry-After or backoff policy)
- RETRYABLE: retry (bounded, may require short backoff)
- DEPENDENCY_FAILED: retry (bounded, longer backoff)
- NON_RETRYABLE: do not retry → fail
- COMPENSATION_REQUIRED: do not auto-retry; route to compensation/human review

DLQ routing:
- Steps that exceed max attempts or hit NON_RETRYABLE/COMPENSATION_REQUIRED MUST be routed to DLQ or terminal failure state as defined.

---

## 6) Idempotency strategy (normative)

### 6.1 Execution-level idempotency
1. Creating an OrchestrationExecution MUST accept an idempotency key.
2. If called multiple times with the same idempotency key, the system MUST return the same execution_id (no duplicate execution).

### 6.2 Step-level idempotency
1. Every StepExecution attempt MUST have a step-level idempotency key derived from:
   - tenant_id
   - execution_id
   - step_id
   - (optional) attempt_number for tracking, but the external side effect should use a stable key per step, not per attempt

Recommended:
- `step_idempotency_key = hash(tenant_id + execution_id + step_id)`

2. Any external side effect handler MUST:
   - accept the step idempotency key, and
   - either be intrinsically idempotent or enforce idempotency via storage/unique constraints.

Examples:
- creating a DocumentVersion: unique by (document_id, source_step_id)
- posting a LedgerEntry: unique by (idempotency_key)
- sending an email: store a SentNotification record unique by (step_idempotency_key)

### 6.3 Safe retry boundary
A step MUST declare one of:
- SAFE_TO_RETRY: side effect is idempotent
- NOT_SAFE_TO_RETRY: requires compensation or manual action
- SAFE_TO_RETRY_WITH_GUARD: safe if a pre-check confirms no prior completion

This declaration MUST be enforced by the engine. The engine MUST NOT retry NOT_SAFE_TO_RETRY steps automatically.

---

## 7) Compensation and manual intervention

### 7.1 Compensation handler
If a step is NOT_SAFE_TO_RETRY or can partially apply side effects, it SHOULD define:
- compensation handler
- compensation policy (auto vs manual approval)

Examples:
- partially created downstream records
- external API calls without idempotency support

### 7.2 Manual review queue
The platform MUST provide a way to surface:
- failed orchestrations
- steps requiring compensation
- DLQ items

This can be:
- an admin UI module
- a structured log + reprocessing tool
but it MUST exist and be permission-gated.

---

## 8) Concurrency control

1. The engine MUST prevent multiple workers from executing the same StepExecution concurrently.
2. Concurrency control MAY be implemented via:
   - row-level locking with SKIP LOCKED
   - advisory locks keyed by execution_id/step_id
3. The engine MUST ensure at-most-once concurrent execution per step per execution, while still allowing retries over time.

---

## 9) Integration with domain state machines

Orchestration MUST respect domain invariants:
1. Any step that transitions a domain entity MUST:
   - call the domain transition endpoint/service
   - fail with NON_RETRYABLE if transition is forbidden
2. Orchestration MUST not “force” state transitions by direct DB updates.

---

## 10) Observability requirements

The system MUST provide:
- metrics:
  - executions started/succeeded/failed
  - step retries by error class
  - DLQ counts
  - p50/p95 step duration by step type
- logs:
  - correlation IDs at execution and step level
  - idempotency keys
  - error classifications and summaries (redacted)
- audit events for:
  - orchestration started/completed
  - manual approvals
  - manual retries / reprocessing
  - compensation actions

---

## 11) API / tooling requirements (high-level)

Minimum operations:
- Create execution (idempotent)
- Get execution status + step history
- Retry failed execution/step (permission-gated, auditable)
- Cancel execution
- Approve step (for human approval steps)
- DLQ listing and reprocessing controls

Endpoints and payload conventions live in API_CONTRACTS.md.

---

## 12) Testing requirements (minimum)

Contract tests MUST cover:
1. Idempotent creation of executions.
2. Step idempotency across duplicate jobs and retries.
3. Retry matrix correctness (classes map to correct behavior).
4. DLQ routing for non-retryable and exhausted retries.
5. Concurrency safety: two workers cannot run the same step concurrently.
6. Compensation-required path produces correct halt and surfaces manual action.

---

## 13) Open items

1. Definition authoring surface:
- Will orchestration definitions be code-defined, JSON-defined, or UI-authored?

2. Step handler interface standard:
- exact signature, result model, error model

3. Pause semantics:
- whether pausing stops current step or only prevents next steps

These must be resolved via DECISION_LOG.md and reflected here.

---

