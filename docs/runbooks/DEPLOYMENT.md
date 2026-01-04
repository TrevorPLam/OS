# Deployment Procedures

**Last Updated:** 2026-01-04  
**Owner:** Release Engineering  
**Severity:** High (user-impacting changes)

## Overview
Standardized deployment checklist for ConsultantPro services to reduce risk, ensure observability, and provide rollback guidance.

## Symptoms
- Planned release window for new code or configuration.
- Hotfix required for production incident.

## Impact
- Deployment errors can cause downtime, migrations can stall, and users may see inconsistent behavior if not coordinated.

## Investigation Steps
1. **Pre-flight checks**
   - Confirm CI is green for the release commit.
   - Review changelog entries and migration notes.
2. **Verify configuration**
   - Ensure required environment variables are set for the target environment.
   - Validate secrets are provisioned via the secrets manager (never in code).
3. **Dry run critical commands**
   - `python src/manage.py check` for configuration issues.
   - `python src/manage.py makemigrations --check --dry-run` to confirm no pending schema drift.

## Resolution Steps
1. **Deploy application**
   - Build and publish artifacts using the CI pipeline or `docker compose build` for manual flows.
   - Apply database migrations: `python src/manage.py migrate --noinput`.
   - Restart services: `docker compose up -d web worker`.
2. **Post-deploy verification**
   - Run smoke tests on auth, deals, automation triggers, and webhooks (happy paths).
   - Check background jobs backlog: `python src/manage.py shell -c "from modules.jobs.models import JobQueue; print(JobQueue.objects.pending().count())"`.
   - Tail logs for errors: `docker compose logs web --tail=100`.
3. **Rollback if needed**
   - Re-deploy previous artifact/tag.
   - If migrations introduced failures, execute documented rollback procedures.
4. **Communicate**
   - Announce start/end of deployment in #engineering and incident channels if applicable.
   - Update release notes/CHANGELOG.md with user-impacting changes.

## Prevention
- Keep migrations small and reversible.
- Use feature flags for risky changes and roll forward when safe.
- Automate smoke tests in CI/CD to catch issues before production.

## Related Resources
- [Rollback Procedures](./ROLLBACK.md)
- [Backup and Restore](./BACKUP_RESTORE.md)
- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
