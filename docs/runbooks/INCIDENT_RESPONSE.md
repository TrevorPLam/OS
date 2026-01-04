# Incident Response Runbook

**Last Updated:** 2026-01-04  
**Owner:** SRE / On-Call Engineer  
**Severity:** Critical

## Overview
This runbook standardizes how the on-call team triages and resolves platform incidents while maintaining clear communication and auditability.

## Symptoms
- Multiple services returning 5xx errors or elevated latency.
- Alert manager paging for uptime, error rate, or saturation thresholds.
- Users reporting inability to log in or access core workflows.

## Impact
- Customer-facing downtime or degraded experience.
- Risk of data inconsistency if writes are partially applied.
- Escalated support volume and potential SLA breaches.

## Investigation Steps
1. **Acknowledge alerts** in the paging system to stop duplicate escalations.
2. **Capture incident metadata** (start time, alerts, affected services) in the incident channel/ticket.
3. **Check application health**:
   - `python src/manage.py check`
   - `docker compose ps` (or hosting provider dashboard) for container status.
4. **Inspect recent deploys and migrations**:
   - `git log -5 --oneline` for recent merges.
   - `python src/manage.py showmigrations --plan | tail -n 5` for recent schema changes.
5. **Review logs** for correlated errors:
   - `docker compose logs web --tail=200`
   - `docker compose logs worker --tail=200` if background jobs are involved.
6. **Validate dependencies** (DB/cache/queue):
   - Database: `python src/manage.py dbshell -c "SELECT 1;"` (or equivalent health check command).
   - Cache: `redis-cli PING` (if Redis is deployed).
   - Job queue: `python src/manage.py shell -c "from modules.jobs.models import JobQueue; print(JobQueue.objects.pending().count())"`

## Resolution Steps
1. **Stabilize production**:
   - Roll back the most recent deploy if errors correlate with a release.
   - Disable new traffic to failing components using feature flags or load balancer rules when available.
2. **Mitigate acute failures**:
   - Clear bad configuration toggles; restart unhealthy services (`docker compose restart web worker`).
   - Pause automation that is amplifying errors (e.g., automation executor) via admin controls when possible.
3. **Validate recovery**:
   - Re-run smoke checks on critical endpoints (authentication, deals, automation triggers).
   - Confirm background jobs are draining and error rates return to baseline.
4. **Communicate**:
   - Post updates to the incident channel every 15–30 minutes.
   - Notify stakeholders once impact is mitigated and when fully resolved.
5. **Document**:
   - Record root cause, timeline, actions taken, and follow-ups in the incident ticket.

## Prevention
- Add regression tests for the root cause area.
- Expand health checks and dashboards for the failing component.
- Schedule a postmortem review with owners and assign action items.

## Related Resources
- [Deployment Procedures](./DEPLOYMENT.md)
- [Rollback Procedures](./ROLLBACK.md)
- [Failed Jobs Recovery](./FAILED_JOBS.md)
