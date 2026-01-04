# High Error Rate

**Last Updated:** 2026-01-04  
**Owner:** SRE / On-Call Engineer  
**Severity:** High

## Overview
Runbook for investigating and mitigating sudden spikes in 4xx/5xx error rates across services.

## Symptoms
- Alert for HTTP 5xx/4xx rate exceeding threshold.
- Customer reports of repeated failures on specific endpoints.
- Error tracking tool showing burst of new exceptions.

## Impact
- User-facing failures, incomplete workflows, and possible data inconsistency if writes partially succeed.

## Investigation Steps
1. **Identify scope**:
   - Review monitoring dashboards to pinpoint affected endpoints and services.
   - Check recent deploys/releases for correlation.
2. **Inspect logs and traces**:
   - `docker compose logs web --tail=200` for stack traces.
   - Query error tracker for the top 3 error signatures.
3. **Validate dependencies**:
   - Database and cache health (see respective runbooks).
   - Third-party integrations reachable (status pages or connectivity tests).

## Resolution Steps
1. **Stabilize service**:
   - Roll back recent deployment or feature flag if correlated.
   - Apply hotfix or configuration override for the failing code path.
2. **Mitigate impact**:
   - Rate limit or temporarily disable non-critical endpoints amplifying failures.
   - Retry failed background jobs only after fixing the root cause.
3. **Verify recovery**:
   - Monitor error rate returning to baseline for at least 15 minutes.
   - Execute smoke tests for affected endpoints.
4. **Communicate**:
   - Share status updates in incident channel until resolved.

## Prevention
- Add regression tests for the failing path and enforce pre-deploy smoke tests.
- Strengthen input validation and error handling in impacted modules.
- Ensure dashboards include golden signals per service.

## Related Resources
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Deployment Procedures](./DEPLOYMENT.md)
- [Cache Failures](./cache-failure.md)
