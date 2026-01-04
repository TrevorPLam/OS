# Scaling Procedures

**Last Updated:** 2026-01-04  
**Owner:** SRE / Platform Engineering  
**Severity:** Medium

## Overview
Guidance for safely scaling application tiers (web, worker, database, cache) to handle increased load while preserving reliability.

## Symptoms
- Sustained CPU > 70% or memory pressure on web/worker nodes.
- Queue latency or backlog growth in `JobQueue`.
- Database slow queries or connection saturation.
- Cache eviction rate spikes or timeouts.

## Impact
- User-facing latency and timeouts.
- Automation or webhook delivery delays.
- Potential cascading failures if scaling is uncoordinated.

## Investigation Steps
1. **Validate demand spike vs. leak**:
   - Review dashboards for traffic patterns, queue depth, and error rates.
2. **Check application bottlenecks**:
   - Inspect slow queries (DB monitoring) and cache hit ratio.
   - Confirm background worker concurrency vs. queue size.
3. **Review deployment topology**:
   - Current replica counts for web/worker services.
   - Database instance size and connection limits.

## Resolution Steps
1. **Scale stateless services first**:
   - Increase web/worker replicas using orchestration tools (e.g., `docker compose up -d --scale web=3 --scale worker=3`).
   - Ensure environment variables and secrets are available for new replicas.
2. **Scale data stores carefully**:
   - For databases, prefer vertical scaling or read replicas with connection pooling adjustments.
   - For caches, increase memory and review eviction policy.
3. **Rebalance background jobs**:
   - Tune worker concurrency based on CPU cores and workload characteristics.
   - Temporarily pause non-critical jobs to prioritize user-facing tasks.
4. **Validate**:
   - Monitor latency, error rates, and queue depth for at least 15–30 minutes post-change.
   - Run smoke checks on critical endpoints.
5. **Document outcome** in the runbook log or incident ticket, including before/after metrics.

## Prevention
- Set autoscaling policies with safe limits for web/worker tiers.
- Budget database connections and enforce connection pooling.
- Load test major releases before turning on new features.

## Related Resources
- [Failed Jobs Recovery](./FAILED_JOBS.md)
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Backup and Restore](./BACKUP_RESTORE.md)
