# Test Strategy (TEST_STRATEGY)

Defines unit/integration/e2e boundaries and contract tests for correctness-critical engines.

Normative for testing expectations.

---

## 1) Boundaries
Unit tests:
- pure domain logic, evaluators, state machines, permission evaluator
Integration tests:
- DB + migrations + tenancy provisioning
- worker idempotency and locking behavior
- storage adapter signed URL flows (mocked object store ok)
E2E tests:
- staff app + portal flows (happy paths + a few critical failures)

---

## 2) Required contract tests (MUST)
Pricing:
- determinism (same inputs -> same outputs + trace)
Permissions:
- allow/deny matrix for key roles and portal scopes
Recurrence:
- DST/leap-year correctness
- dedupe under concurrency + retries
Orchestration:
- retry matrix behavior and DLQ routing
Billing ledger:
- idempotent posting
- allocation constraints
Documents:
- versioning, locking, portal visibility, access logging

---

## 3) Time and timezone testing
- Use deterministic time control in tests
- Include at least two DST-observing timezones in recurrence tests

---

