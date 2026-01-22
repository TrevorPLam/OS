# Alert Configuration

Per docs/03-reference/requirements/DOC-21.md OBSERVABILITY_AND_SRE section 3: Alert thresholds for operational monitoring.

## Default Alert Thresholds

These are baseline thresholds for operational alerts. Values can be adjusted based on tenant size and workload patterns.

### Worker Alerts

**Job Failure Rate**
- **Threshold:** 10% failure rate
- **Window:** 5 minutes (sustained)
- **Action:** Investigate job errors, check for infrastructure issues
- **Severity:** High

**DLQ Depth**
- **Threshold:** 100 items
- **Window:** Immediate
- **Action:** Review DLQ items, identify non-retryable errors, fix and reprocess
- **Severity:** High

### Integration Alerts

**Email Ingest Lag**
- **Threshold:** 900 seconds (15 minutes)
- **Window:** 5 minutes (sustained)
- **Action:** Check email provider connectivity, OAuth token expiration, rate limiting
- **Severity:** Medium

**Calendar Sync Lag**
- **Threshold:** 900 seconds (15 minutes)
- **Window:** 5 minutes (sustained)
- **Action:** Check calendar provider connectivity, OAuth token expiration, rate limiting
- **Severity:** Medium

**Integration Failure Rate**
- **Threshold:** 10% failure rate
- **Window:** 5 minutes (sustained)
- **Action:** Check provider API status, review error logs for classification
- **Severity:** High

### API Alerts

**API Error Rate**
- **Threshold:** 5% error rate (5xx responses)
- **Window:** 5 minutes (sustained)
- **Action:** Check server health, database connectivity, infrastructure
- **Severity:** Critical

**API Latency (p95)**
- **Threshold:** 2000ms
- **Window:** 5 minutes (sustained)
- **Action:** Check database slow queries, infrastructure performance
- **Severity:** Medium

### Document Alerts

**Scan Pending Count**
- **Threshold:** 50 pending scans
- **Window:** Immediate
- **Action:** Check malware scanning service availability
- **Severity:** Medium

**Upload/Download Failure Rate**
- **Threshold:** 5% failure rate
- **Window:** 5 minutes (sustained)
- **Action:** Check S3 connectivity, presigned URL expiration, permissions
- **Severity:** Medium

### Billing Alerts

**Posting Failure Rate**
- **Threshold:** 1% failure rate
- **Window:** Immediate
- **Action:** Review ledger entry errors, check for constraint violations
- **Severity:** Critical (affects revenue)

**Idempotency Collision Rate**
- **Threshold:** 10% collision rate
- **Window:** 5 minutes (sustained)
- **Action:** Normal during retries; investigate if sustained without failures
- **Severity:** Info (monitoring only)

### Security Alerts

**Permission Denial Spike**
- **Threshold:** 5% denial rate
- **Window:** 5 minutes (sustained)
- **Action:** Investigate for misconfiguration or potential abuse
- **Severity:** High

**Repeated Permission Denials (Same Actor)**
- **Threshold:** 10 denials in 1 minute
- **Window:** Immediate
- **Action:** Investigate for unauthorized access attempts
- **Severity:** Critical

## Tenant-Specific Overrides

Thresholds can be customized per tenant based on:
- Tenant size (number of users, volume of data)
- Workload patterns (batch processing vs real-time)
- SLA requirements

Configuration stored in: `FirmConfiguration.alert_thresholds` (JSON field)

Example:
```json
{
  "job_failure_rate": 0.05,
  "dlq_depth": 50,
  "api_error_rate": 0.02
}
```

## Alert Routing

**Critical:** Page on-call engineer immediately
**High:** Slack alert to ops channel, escalate if not resolved in 30 minutes
**Medium:** Slack alert to ops channel
**Info:** Log only, review in daily operational review

## Metric Collection

All metrics are collected via `modules.core.observability` utilities:
- `track_api_request()`
- `track_job_execution()`
- `track_dlq_depth()`
- `track_email_ingest()`
- `track_calendar_sync()`
- `track_document_upload()`
- `track_document_download()`
- `track_billing_posting()`
- `track_idempotency_collision()`

## Correlation IDs

All metrics and logs include `correlation_id` for end-to-end tracing (per docs/03-reference/requirements/DOC-21.md section 1).

Correlation IDs:
- Generated per API request (middleware)
- Flow through job payloads
- Included in audit events
- Returned in `X-Correlation-ID` response header

## Log Requirements

All operational logs include (per docs/03-reference/requirements/DOC-21.md section 4):
- `tenant_id`: Firm/tenant identifier
- `correlation_id`: Request/job correlation ID
- `actor`: User or system performing action (when applicable)
- `object_type` and `object_id`: Primary resource being operated on

Logs automatically redact HR-classified data and minimize PII (per docs/03-reference/requirements/DOC-07.md DATA_GOVERNANCE).
