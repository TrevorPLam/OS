# Slow Response Times

**Last Updated:** 2026-01-04  
**Owner:** Platform Engineering  
**Severity:** Medium

## Overview
Guidance for diagnosing and mitigating elevated latency across API endpoints or background workflows.

## Symptoms
- Apdex/latency alerts triggering for web endpoints.
- Users reporting sluggish UI or timeouts.
- Slow background processing or queue backlog growth without failures.

## Impact
- Poor user experience and potential request timeouts leading to retries or duplicate actions.

## Investigation Steps
1. **Confirm scope**:
   - Identify affected endpoints and time window using dashboards.
   - Check if the issue is regional or global.
2. **Check resource utilization**:
   - CPU/memory on web/worker nodes.
   - Database CPU and slow query logs.
3. **Inspect code paths**:
   - Review recent deployments touching affected endpoints.
   - Look for N+1 queries or missing indexes in traces.

## Resolution Steps
1. **Reduce load**:
   - Scale out web/worker replicas temporarily (see Scaling runbook).
   - Enable caching for hot paths when safe.
2. **Optimize data access**:
   - Add or adjust indexes for slow queries (with DBA approval).
   - Batch expensive operations or move them to background jobs.
3. **Validate**:
   - Re-run latency dashboards after changes; target return to baseline.
   - Execute user-level smoke tests for the affected flows.
4. **Communicate** progress and resolution in the incident or release channel.

## Prevention
- Add performance tests for critical endpoints.
- Monitor queue depth and latency with alerts before saturation.
- Review query plans regularly and prune unused indexes.

## Related Resources
- [Scaling Procedures](./SCALING.md)
- [Cache Failures](./cache-failure.md)
- [High Error Rate](./high-error-rate.md)
