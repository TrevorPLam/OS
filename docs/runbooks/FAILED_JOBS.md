# Failed Jobs Recovery

**Last Updated:** 2026-01-04  
**Owner:** Backend Engineering / SRE  
**Severity:** Medium

## Overview
Procedures for diagnosing and recovering failed background jobs tracked in `JobQueue` without losing auditability.

## Symptoms
- Alerts about growing pending/failed counts in `JobQueue`.
- Users reporting missing notifications, webhooks, or automations.
- Workers repeatedly retrying the same payload.

## Impact
- Delayed or dropped user-facing actions (emails, webhooks, automations).
- Potential duplication if retries are not idempotent.

## Investigation Steps
1. **Assess queue health**:
   - `python src/manage.py shell -c "from modules.jobs.models import JobQueue; print(JobQueue.objects.failed().count(), JobQueue.objects.pending().count())"`
2. **Inspect recent failures**:
   - Query a few failed jobs for error messages and payload metadata.
3. **Check worker status**:
   - `docker compose ps worker` and `docker compose logs worker --tail=200`.
4. **Validate dependencies**:
   - External services (email provider, webhook targets) reachable.
   - Database and cache healthy (see relevant runbooks).

## Resolution Steps
1. **Fix root cause** (credentials, network, code regression, or bad payload).
2. **Retry safe jobs**:
   - Mark jobs for retry using admin tooling or Django shell, ensuring idempotency rules are enforced.
3. **Quarantine bad jobs**:
   - Move malformed payloads to a dead-letter state for manual review.
4. **Monitor recovery**:
   - Track backlog drain rate and error logs until counts stabilize.

## Prevention
- Add circuit breakers and idempotency keys for external calls.
- Set alert thresholds on failed and pending job counts.
- Include integration tests for job handlers covering transient failures and retries.

## Related Resources
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Scaling Procedures](./SCALING.md)
- Job queue model reference: `src/modules/jobs/models.py`
