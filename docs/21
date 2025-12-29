# Observability and SRE (OBSERVABILITY_AND_SRE)

Defines metrics, dashboards, alert thresholds, log correlation, and audit log access patterns.

Blueprint.

---

## 1) Correlation IDs
- Every API request and job MUST have a correlation_id.
- correlation_id MUST flow through logs, job payloads, and audit events.

---

## 2) Required metrics (minimum)
API:
- request count, error rate, p95 latency by route group
Workers:
- job latency, failures by job type, retry counts, DLQ depth
Integrations:
- email ingest success/failure rates, lag
- calendar sync success/failure rates, lag
Documents:
- upload/download failures, scan pending count
Billing:
- posting failures, idempotency collisions

---

## 3) Alerts (starter thresholds)
- sustained job failures over threshold
- DLQ depth increasing
- integration lag beyond threshold
- repeated permission denials spike (potential misconfig or abuse)

(Exact values can be tenant-size dependent; document defaults and allow config.)

---

## 4) Log requirements
Logs MUST include:
- tenant_id
- correlation_id
- actor (when applicable)
- primary object ids
Logs MUST redact HR and minimize PII (DATA_GOVERNANCE.md).

---

## 5) Audit log access patterns
- Audit logs are restricted
- Provide filtered views by:
  - actor
  - object id
  - action type
  - time range
- Access to audit viewer SHOULD itself be audited

---
