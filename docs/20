# Workers and Queues (WORKERS_AND_QUEUES)

Defines job types, payload schemas, priorities, concurrency model, locks, DLQ handling, and reprocessing rules.

Blueprint; must align with SYSTEM_SPEC idempotency rules.

---

## 1) Job categories
- ingestion: email fetch/parse/store/map
- sync: calendar pull/push
- recurrence: period generation + work creation
- orchestration: step execution
- documents: scan/index/classify hooks
- notifications: send email/in-app

---

## 2) Payload rules (MUST)
1. Payloads MUST be minimal and avoid embedding sensitive content.
2. Payloads MUST include:
- tenant_id
- correlation_id
- idempotency_key (when applicable)
- primary object refs (ids)
3. Payloads MUST be versioned if structure may evolve.

---

## 3) Concurrency model
Workers MUST ensure:
- at-most-one concurrent processing per idempotency key
Using either:
- SKIP LOCKED row claim pattern, or
- advisory locks keyed by idempotency_key

---

## 4) DLQ handling (MUST)
- Non-retryable or exhausted retries go to DLQ.
- DLQ items must be viewable and reprocessable (admin-gated).
- Reprocessing must be auditable and must preserve original payload and attempt history.

---

## 5) Retry policy alignment
Retry classes must align with ORCHESTRATION_ENGINE_SPEC.md error classes.

---
