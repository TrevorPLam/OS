# Calendar Sync Specification (CALENDAR_SYNC_SPEC)

Defines idempotent calendar synchronization with external providers (Google/Microsoft), sync logs, retries, and manual resync tooling.

Normative. If conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md governs.

---

## 1) Goals
1. Sync MUST be idempotent using stable external identifiers.
2. Sync MUST be retry-safe with explicit attempt logs.
3. The system MUST support manual resync and reconciliation tooling.
4. Appointment state MUST remain consistent with internal semantics (DOMAIN_MODEL.md).

---

## 2) Core concepts

### 2.1 CalendarConnection
Represents an authenticated connection.
- connection_id
- provider (google | microsoft)
- owner_staff_user_id (or firm-wide connection)
- scopes granted
- status (active | revoked)
- created_at, updated_at

### 2.2 External event identity
Appointments MUST store:
- external_event_id
- connection_id

Uniqueness:
- (connection_id, external_event_id) MUST be unique.

### 2.3 SyncAttemptLog
Records each sync attempt.
- attempt_id
- connection_id
- direction (pull | push)
- operation (list_changes | upsert | delete | resync)
- status (success | fail)
- error_class (transient | non_retryable | rate_limited)
- error_summary (redacted)
- started_at, finished_at
- correlation_id

---

## 3) Sync behavior (MUST)

### 3.1 Pull (external → internal)
- Fetch changes since last cursor/token.
- Upsert Appointment by (connection_id, external_event_id).
- Apply reconciliation rules:
  - if external time changes, update internal times and log change
  - if external cancel/delete occurs, apply policy (cancel appointment vs mark external_removed)
Policy must be explicit and tested.

### 3.2 Push (internal → external)
- When internal appointment is created/updated, push to provider.
- Store returned external_event_id.
- Retries MUST not create duplicates:
  - use provider idempotency if available
  - otherwise maintain a “pending create” record keyed by internal appointment id + connection

---

## 4) Retry behavior
- Transient/rate-limited errors: retry with backoff.
- Non-retryable errors: stop and surface to admin.

A retry matrix MUST exist (can be referenced from ORCHESTRATION/WORKERS docs).

---

## 5) Manual resync tooling (required)
Admin-gated tools MUST allow:
- resync a connection (full or date-bounded)
- resync a single appointment by id
- view last sync cursor/timestamp
- view and reprocess failed attempts (audited)

---

## 6) Observability
- metrics: sync success rate, failures by provider/operation, lag since last successful sync
- logs: include connection_id, external_event_id, appointment_id, correlation_id

---

## 7) Testing requirements
- idempotent upsert
- duplicate prevention under retries
- cancellation reconciliation
- timezone correctness
- manual resync correctness and audit

---
