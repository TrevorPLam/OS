# Cache Failures

**Last Updated:** 2026-01-04  
**Owner:** Platform Engineering  
**Severity:** Medium

## Overview
Troubleshooting steps for cache outages or degradation impacting application performance.

## Symptoms
- Increased latency on cached endpoints.
- Cache miss ratio spikes or eviction rates increase.
- Application logs showing connection errors to cache host.

## Impact
- Higher load on the database due to bypassed caching.
- User-visible slowdowns and possible rate limiting.

## Investigation Steps
1. **Validate cache availability**:
   - `redis-cli PING` (or cache provider equivalent) should return `PONG`.
   - Check cache metrics for memory usage and eviction rates.
2. **Inspect application errors**:
   - `docker compose logs web --tail=100` for cache connection errors.
   - Review error tracking for elevated latency tied to cache calls.
3. **Review configuration**:
   - Confirm cache host/port/env vars are correct.
   - Ensure TLS/auth settings match the cache service configuration.

## Resolution Steps
1. **Restore cache service**:
   - Restart cache process/container if unhealthy.
   - Increase memory allocation or adjust eviction policy if memory pressure is the cause.
2. **Warm critical keys** where possible to reduce cold-start impact after restart.
3. **Validate**:
   - `redis-cli INFO stats | head` to confirm stable stats.
   - Monitor application latency and database load returning to baseline.

## Prevention
- Set alerts on memory pressure, eviction rate, and connection errors.
- Use connection pooling and reasonable timeouts to avoid cascading failures.
- Document cache key TTLs and eviction strategies.

## Related Resources
- [Scaling Procedures](./SCALING.md)
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Database Connection Issues](./db-connection-failure.md)
