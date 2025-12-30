# Rollback Procedures

**Document Version:** 1.0  
**Last Updated:** December 30, 2025  
**Owner:** Platform Engineering Team  
**Constitution Reference:** Section 11.4

## Overview

This document defines rollback procedures for all deployment types to ensure quick recovery from bad deployments.

Per Constitution Section 11.4:
> "Rollback is defined, rehearsed, and scripted where possible."

## Rollback Decision Criteria

Initiate rollback if:
- **Critical bugs** affecting core functionality
- **Data integrity** issues detected
- **Security vulnerabilities** introduced
- **Performance degradation** exceeding SLA thresholds
- **Database migration failures** preventing application startup
- **High error rates** (>5% of requests failing)

## 1. Code Deployment Rollback

### Quick Rollback (Docker/Container)

**Time to Complete:** 5-10 minutes

```bash
# 1. Identify previous working version
docker images consultantpro --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}"

# 2. Update docker-compose to use previous tag
export IMAGE_TAG=<previous-version>
docker-compose -f docker-compose.prod.yml up -d --no-build

# 3. Verify health checks
curl https://api.consultantpro.com/health/ready/
```

## 2. Database Migration Rollback

**Time to Complete:** 5-30 minutes

**CRITICAL:** Always roll back database migrations BEFORE rolling back application code.

```bash
# 1. Put application in maintenance mode
kubectl scale deployment/consultantpro-api --replicas=0

# 2. Roll back to previous migration
cd src
python manage.py migrate clients 0042_previous_migration

# 3. Verify schema state
python manage.py dbshell

# 4. Exit maintenance mode
kubectl scale deployment/consultantpro-api --replicas=3
```

## 3. Feature Flag Rollback

**Time to Complete:** < 1 minute

```bash
# Disable problematic feature flag via API
curl -X PATCH https://api.consultantpro.com/api/feature-flags/<flag-id>/ \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"enabled": false}'
```

## 4. Post-Rollback Procedures

1. **Update Incident Ticket**
2. **Verify System Health**
3. **Communication** - Update status page
4. **Root Cause Analysis** - Schedule within 24 hours

## Related Documents

- [Incident Response Runbook](./INCIDENT_RESPONSE.md)
- [Deployment Procedures](./DEPLOYMENT.md)
- [Disaster Recovery Plan](./DISASTER_RECOVERY.md)

