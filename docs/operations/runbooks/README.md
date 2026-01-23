# Operational Runbooks

Step-by-step procedures for common operational tasks.

## Runbook Categories

### Deployment
- [Deploy to Staging](deployment-staging.md)
- [Deploy to Production](deployment-production.md)
- [Rollback Procedure](rollback.md)

### Maintenance
- [Database Migrations](database-migrations.md)
- [Scheduled Maintenance](maintenance.md)
- [Backup Procedures](backup.md)

### Incident Response
- [Incident Response](incident-response.md)
- [Service Recovery](service-recovery.md)
- [Post-Incident Review](post-incident.md)

### Monitoring
- [Check System Health](health-check.md)
- [Review Logs](log-review.md)
- [Performance Investigation](performance.md)

## Runbook Template

Each runbook should include:
- **Purpose** - What this runbook does
- **Prerequisites** - Required access, tools, knowledge
- **Steps** - Detailed step-by-step instructions
- **Verification** - How to verify success
- **Rollback** - How to undo if needed
- **Related** - Links to related runbooks

## Creating New Runbooks

1. Use runbook template from `.repo/templates/RUNBOOK_TEMPLATE.md`
2. Include all required sections
3. Test the procedure
4. Review with team
5. Add to this index

## Related Documentation

- [Operations](../README.md) - Operations overview
- [Troubleshooting](../troubleshooting.md) - Common issues
- [Monitoring](../monitoring.md) - Monitoring setup
