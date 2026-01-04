# Database Connection Issues

**Last Updated:** 2026-01-04  
**Owner:** Database Engineering / SRE  
**Severity:** High

## Overview
Steps to diagnose and resolve database connectivity issues affecting the application or background workers.

## Symptoms
- Application errors such as `OperationalError` or connection timeout.
- Health checks failing on database reachability.
- Spike in failed jobs with DB-related traces.

## Impact
- Read/write operations unavailable; potential data loss for in-flight transactions.

## Investigation Steps
1. **Confirm outage scope**:
   - `python src/manage.py dbshell -c "SELECT 1;"` (returns error on connectivity issues).
   - Check monitoring dashboards for DB availability and connection counts.
2. **Inspect application side**:
   - Verify database credentials and host/port in environment variables.
   - `docker compose logs web --tail=100` for recent DB errors.
3. **Check database service**:
   - Ensure the database process/container is running.
   - Inspect server logs for restarts, disk pressure, or connection limit errors.

## Resolution Steps
1. **Restore connectivity**:
   - Restart database service if down and verify storage availability.
   - Increase connection limits or pool size only after confirming saturation is the root cause.
2. **Application recovery**:
   - Restart web/worker containers to refresh connections once DB is healthy.
3. **Validation**:
   - `python src/manage.py check` should pass.
   - Smoke test critical read/write paths.

## Prevention
- Enforce connection pooling with sensible defaults.
- Set alerts on connection saturation and disk usage.
- Schedule vacuum/maintenance tasks to avoid unplanned outages.

## Related Resources
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Scaling Procedures](./SCALING.md)
- [Backup and Restore](./BACKUP_RESTORE.md)
