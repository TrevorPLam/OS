# Runbooks Directory

This directory contains operational runbooks for ConsultantPro platform.

Per Constitution Section 12.6:
> "Runbooks exist for: common failures, critical workflows, incident response and recovery."

## Available Runbooks

### Core Operational Runbooks

1. **[Rollback Procedures](./ROLLBACK.md)** (CONST-7) ✅
   - Code deployment rollback
   - Database migration rollback
   - Feature flag rollback
   - Configuration rollback

2. **[Incident Response](./INCIDENT_RESPONSE.md)** 🚧 Tracked in TODO: T-012
   - Incident classification
   - Communication protocols
   - Escalation procedures
   - Post-incident review

3. **[Deployment Procedures](./DEPLOYMENT.md)** 🚧 Tracked in TODO: T-012
   - Pre-deployment checklist
   - Deployment steps
   - Smoke testing
   - Monitoring

4. **[Backup and Restore](./BACKUP_RESTORE.md)** 🚧 Tracked in TODO: T-012
   - Database backup procedures
   - File storage backup
   - Restore procedures
   - DR testing

5. **[Scaling Procedures](./SCALING.md)** 🚧 Tracked in TODO: T-012
   - Horizontal scaling (adding instances)
   - Vertical scaling (increasing resources)
   - Database scaling
   - Cache scaling

6. **[Failed Jobs Recovery](./FAILED_JOBS.md)** 🚧 Tracked in TODO: T-012
   - Job queue monitoring
   - DLQ processing
   - Manual retry procedures
   - Job cleanup

### Common Failure Runbooks

7. **[Database Connection Issues](./db-connection-failure.md)** 🚧 Tracked in TODO: T-013
8. **[Cache Failures](./cache-failure.md)** 🚧 Tracked in TODO: T-013
9. **[High Error Rate](./high-error-rate.md)** 🚧 Tracked in TODO: T-013
10. **[Slow Response Times](./slow-response-times.md)** 🚧 Tracked in TODO: T-013

## Runbook Template

Each runbook should follow this structure:

```markdown
# [Runbook Title]

**Last Updated:** [Date]  
**Owner:** [Team/Role]  
**Severity:** [Critical/High/Medium/Low]

## Overview
Brief description of what this runbook covers.

## Symptoms
How to identify this issue is occurring.

## Impact
What breaks when this issue occurs.

## Investigation Steps
1. Check X
2. Verify Y
3. Review Z

## Resolution Steps
1. Step-by-step resolution
2. With specific commands
3. And verification steps

## Prevention
How to prevent this issue in the future.

## Related Resources
- Links to relevant docs
- Dashboard URLs
- Slack channels
```

## Constitution Compliance

This runbooks directory fulfills Constitution Section 12.6 requirements:
- ✅ Rollback procedures documented
- 🚧 Common failure scenarios (Tracked in TODO: T-013)
- 🚧 Critical workflow documentation (Tracked in TODO: T-012)
- 🚧 Incident response procedures (Tracked in TODO: T-012)

## Contributing

When adding a new runbook:
1. Follow the runbook template above
2. Test all commands on staging
3. Get review from on-call engineer
4. Update this README with link
5. Announce in #engineering channel

---

**Status Legend:**
- ✅ Complete
- 🚧 TODO
- 🔄 In Progress
