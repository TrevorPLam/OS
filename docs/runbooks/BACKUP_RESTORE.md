# Backup and Restore Runbook

**Last Updated:** 2026-01-04  
**Owner:** Database Engineering  
**Severity:** High

## Overview
Procedures for safeguarding and restoring critical data stores (databases and file storage) to meet RPO/RTO objectives.

## Symptoms
- Scheduled backup window.
- Data corruption, accidental deletion, or failed migration requiring restore.
- Audit request to verify backup integrity.

## Impact
- Potential data loss or prolonged downtime if backups are missing or invalid.

## Investigation Steps
1. **Identify scope**: database(s) and storage buckets affected.
2. **Confirm latest backups**:
   - Check backup logs/monitoring dashboard for success status and timestamps.
   - Validate snapshot availability in the backup storage location.
3. **Verify integrity**:
   - Restore the latest backup to a staging database and run smoke checks where possible.
4. **Lock writes if needed**: place the application in maintenance mode or temporarily disable write paths to prevent divergence.

## Resolution Steps
1. **Create an additional safety snapshot** before proceeding with restore (if system is still reachable).
2. **Database restore**:
   - Provision restore target (temporary instance or production replacement).
   - Initiate restore from the selected snapshot/backup.
   - Run migrations if schema drift exists.
3. **File/object storage restore**:
   - Restore objects from the most recent consistent snapshot to the target bucket/path.
   - Rebuild derived assets (e.g., thumbnails) if necessary.
4. **Validation**:
   - `python src/manage.py check` to confirm connectivity and configuration.
   - Run targeted smoke tests on data-critical workflows (record retrieval, uploads/downloads).
5. **Return to service**:
   - Re-enable writes and background processing.
   - Monitor logs and metrics for anomalies during the first hour after restore.

## Prevention
- Schedule automated backup verification (periodic test restores in staging).
- Track backup freshness in monitoring with alerts for missed windows.
- Keep restore runbooks updated after each test.

## Related Resources
- [Deployment Procedures](./DEPLOYMENT.md)
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Scaling Procedures](./SCALING.md)
