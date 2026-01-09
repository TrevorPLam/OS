# OBSERVABILITY.md

Last Updated: 2026-01-09

Applies to repos that run services (API, worker, cron, etc.). For libraries/CLI, keep logging conventions only.

## Logging (required)
- Structured logs (JSON) for services.
- Include a correlation/request id on every request.
- Never log secrets or full PII.

## Metrics (recommended)
- Request count, latency, error rate
- Queue depth (workers)
- CPU/memory (if containerized)

### SLO targets (baseline)
- API availability: 99.9% monthly
- API latency: p95 < 250ms, p99 < 750ms (business hours)
- Background jobs: 99% completed within 5 minutes of enqueue
- Webhooks: 99.5% delivery success within 10 minutes
- Frontend Core Web Vitals (P75): LCP < 2.5s, INP < 200ms, CLS < 0.1

## Tracing (optional)
- Add distributed tracing when there are multiple services or external dependencies.

## Error handling
- Fail fast on configuration errors.
- Use consistent error codes/messages.
- Add alerting later; start with good logs now.

## Alert thresholds (initial)
Define alert thresholds with clear severity and ownership. Page only for user-impacting
or data-integrity issues. Everything else should route to the on-call Slack channel.

### Critical (page 24/7)
- API error rate > 2% for 5 minutes OR p95 latency > 1s for 10 minutes
- Authentication failures > 5% for 5 minutes
- Worker queue depth > 500 for 10 minutes (or > 2x daily baseline)
- Webhook delivery failures > 5% for 10 minutes
- Database availability loss or replica lag > 60 seconds
- Payment processing failures > 2% for 10 minutes

### Warning (Slack only)
- API error rate > 0.5% for 10 minutes
- p95 latency > 500ms for 15 minutes
- Worker queue depth > 200 for 15 minutes
- Webhook delivery failures > 1% for 15 minutes
- Disk utilization > 80% or memory > 85% for 15 minutes
- Background job retries > 3% for 15 minutes

## 24/7 paging metrics
The following metrics require immediate paging because they indicate direct user impact,
revenue loss, or potential data loss:
- API availability and error rate
- Authentication success rate
- Worker queue depth and job completion latency
- Webhook delivery success rate (for payment/signature providers)
- Database availability and replication lag
- Payment failure rate

## Runbook: common failure scenarios
Use these steps as the first response. If a scenario repeats or takes >30 minutes to
resolve, create a post-incident task in TODO.md.

### API error rate spike
1) Confirm scope: check recent deploys, error logs, and request IDs.
2) Identify top failing endpoints and recent schema changes.
3) Roll back the last deploy if errors correlate with release.
4) If DB-related, inspect connection pool saturation and query latency.

### Latency regression
1) Identify endpoints with increased p95/p99 latency.
2) Check database slow queries and background job backlog.
3) Validate cache hit rate; warm caches if cold start detected.
4) If no root cause, throttle heavy clients and open incident.

### Queue backlog / worker failure
1) Validate worker health and concurrency settings.
2) Inspect queue size growth rate and stuck jobs.
3) Restart workers if memory leak suspected.
4) Temporarily scale workers if available.

### Webhook delivery failures
1) Confirm provider status page (Stripe/DocuSign/etc.).
2) Inspect webhook signature verification and retry logs.
3) Requeue failed deliveries if idempotency keys are in place.
4) Notify support if downstream providers are degraded.

### Database saturation or outages
1) Check replication lag and connection pool saturation.
2) Identify long-running queries; terminate if needed.
3) Fail over to replica if primary is unhealthy.
4) Validate app read-only mode if writes must be paused.

### Payment failure spike
1) Check payment provider status and error codes.
2) Verify webhook ingestion and reconciliation jobs are running.
3) Pause auto-charges if failure rate exceeds threshold.
4) Notify finance and support teams with impact estimate.
