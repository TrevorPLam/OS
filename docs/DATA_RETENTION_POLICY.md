# Data Retention Policy (SEC-3)

**Status:** Active  
**Last Updated:** January 3, 2026  
**Security Task:** SEC-3 - Document and implement data retention policies

## Overview

This document defines the data retention policies for ConsultantPro in accordance with security best practices, compliance requirements (GDPR, CCPA), and operational needs.

## Retention Periods

### System Logs and Monitoring

| Data Type | Retention Period | Rationale | Action After Expiry |
|-----------|-----------------|-----------|---------------------|
| Application Logs | 90 days | Debugging and operational monitoring | Delete |
| Error Logs (Sentry) | 90 days | Error tracking and resolution | Delete |
| Access Logs | 90 days | Security monitoring and troubleshooting | Delete |
| Performance Metrics | 90 days | System performance analysis | Archive |

**Implementation:**
- Sentry retention configured via SENTRY_RETENTION_DAYS
- Application logs rotated and deleted after 90 days
- Access logs archived to cold storage after 30 days, deleted after 90 days

### Webhook Events

| Data Type | Retention Period | Rationale | Action After Expiry |
|-----------|-----------------|-----------|---------------------|
| Stripe Webhook Events | 180 days | Payment dispute resolution and audit | Archive |
| Square Webhook Events | 180 days | Payment dispute resolution and audit | Archive |
| DocuSign Webhook Events | 180 days | E-signature verification and audit | Archive |
| SMS/Twilio Webhook Events | 180 days | Delivery audit and compliance | Archive |

**Implementation:**
- Webhook events stored in database tables:
  - `finance_stripe_webhook_events`
  - `finance_square_webhook_events`
  - `esignature_webhook_events`
  - `sms_webhook_events`
- Automated cleanup job runs weekly (see Automated Cleanup section)
- Events older than 180 days are moved to cold storage, then deleted after 365 days

### Audit Trails

| Data Type | Retention Period | Rationale | Action After Expiry |
|-----------|-----------------|-----------|---------------------|
| User Action Audit Logs | 7 years | Compliance (SOX, HIPAA, financial regulations) | Archive |
| Security Event Logs | 7 years | Security compliance and forensics | Archive |
| Data Access Logs | 7 years | Privacy compliance (GDPR, CCPA) | Archive |
| Configuration Changes | 7 years | Audit and compliance requirements | Archive |

**Implementation:**
- Audit logs stored in `core_audit_log` table
- Archived to cold storage (S3 Glacier) after 1 year
- Preserved for 7 years minimum per compliance requirements
- Never deleted if under legal hold

### Business Data

| Data Type | Retention Period | Rationale | Action After Expiry |
|-----------|-----------------|-----------|---------------------|
| Financial Records | 7 years | Tax and accounting requirements | Archive |
| Client Documents | 5 years after engagement end | Legal and professional liability | Archive |
| Communications | 3 years | Business continuity and compliance | Archive |
| Marketing Data (Leads) | 1 year after conversion/loss | GDPR/CCPA data minimization | Anonymize |

**Implementation:**
- Configurable per-firm retention policies (see `modules.core.retention`)
- Executed via management command: `execute_retention_policies`
- Respects legal hold flags

## Automated Cleanup

### Scheduled Jobs

Automated cleanup jobs run on the following schedule:

```bash
# Weekly cleanup job (Sundays at 2 AM UTC)
0 2 * * 0 python manage.py cleanup_webhook_events

# Weekly retention policy execution (Mondays at 2 AM UTC)
0 2 * * 1 python manage.py execute_retention_policies

# Daily log rotation (Daily at 3 AM UTC)
0 3 * * * python manage.py rotate_logs
```

### Webhook Event Cleanup

**Command:** `python manage.py cleanup_webhook_events`

**Behavior:**
- Identifies webhook events older than 180 days
- Archives events to cold storage (S3 Glacier)
- Deletes events from active database
- Logs cleanup statistics (records processed, archived, deleted)
- Sends alert if cleanup fails

**Dry Run:**
```bash
python manage.py cleanup_webhook_events --dry-run
```

**Options:**
- `--retention-days N` - Override default 180-day retention (e.g., 90, 365)
- `--provider stripe|square|docusign|sms` - Clean up specific provider only
- `--dry-run` - Show what would be deleted without making changes

### Retention Policy Execution

**Command:** `python manage.py execute_retention_policies`

**Behavior:**
- Executes all active retention policies for all firms
- Archives/anonymizes/deletes data based on policy configuration
- Skips records under legal hold
- Creates execution record with statistics
- Sends alert if execution fails

**Example:**
```bash
# Execute all policies (dry run)
python manage.py execute_retention_policies --dry-run

# Execute for specific firm
python manage.py execute_retention_policies --firm-id 123

# Execute for specific data type
python manage.py execute_retention_policies --data-type webhook_events
```

## Compliance Considerations

### GDPR (General Data Protection Regulation)

- **Storage Limitation:** Data retained only as long as necessary (Article 5(1)(e))
- **Right to Erasure:** Automated deletion honors data subject rights (Article 17)
- **Data Minimization:** Old data anonymized when retention period expires (Article 5(1)(c))
- **Accountability:** Audit trail of all retention policy executions (Article 5(2))

### CCPA (California Consumer Privacy Act)

- **Data Deletion:** Consumers can request deletion of personal information
- **Retention Periods:** Documented and disclosed in privacy policy
- **Audit Trail:** Records of data deletion for compliance verification

### Industry Standards

- **SOX (Sarbanes-Oxley):** 7-year retention for financial records and audit logs
- **HIPAA:** 6-year minimum retention for healthcare-related records
- **Tax Regulations:** 7-year retention for financial records (IRS requirement)

## Legal Hold

Data under legal hold is **never** automatically purged:

- Legal hold flag checked before any deletion/anonymization
- Applies to: Documents, audit logs, communications, emails
- Override available only by authorized legal/compliance team
- Audit trail of all legal hold changes

**Implementation:**
```python
# Check legal hold before deletion
if record.legal_hold:
    logger.warning(f"Skipping record {record.id} - under legal hold")
    continue
```

## Monitoring and Alerts

### Metrics Tracked

- `data_retention.webhook_events_deleted` - Webhook events deleted
- `data_retention.webhook_events_archived` - Webhook events archived
- `data_retention.logs_deleted` - Log entries deleted
- `data_retention.audit_logs_archived` - Audit logs archived
- `data_retention.retention_policy_executed` - Retention policies run

### Alerts

- **Cleanup Failures:** Alert if automated cleanup fails 2 consecutive times
- **Storage Threshold:** Alert if webhook event table exceeds 1M records
- **Compliance Risk:** Alert if audit logs older than 7 years not yet archived

## Privacy Policy Updates

This data retention policy is reflected in the application privacy policy:

- **Location:** `PRIVACY_POLICY.md` and `/legal/privacy` endpoint
- **Disclosure:** Retention periods disclosed per data category
- **User Rights:** Instructions for requesting data deletion
- **Contact:** Data protection officer contact for retention questions

## Configuration

### Environment Variables

```bash
# Webhook event retention (default: 180 days)
WEBHOOK_RETENTION_DAYS=180

# Application log retention (default: 90 days)
LOG_RETENTION_DAYS=90

# Audit log cold storage threshold (default: 365 days)
AUDIT_LOG_ARCHIVE_DAYS=365

# Enable automated cleanup jobs (default: true in production)
ENABLE_AUTOMATED_CLEANUP=true
```

### Settings Configuration

Configure in `src/config/settings.py`:

```python
# Data Retention Configuration (SEC-3)
WEBHOOK_RETENTION_DAYS = int(os.environ.get("WEBHOOK_RETENTION_DAYS", "180"))
LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "90"))
AUDIT_LOG_ARCHIVE_DAYS = int(os.environ.get("AUDIT_LOG_ARCHIVE_DAYS", "365"))
AUDIT_LOG_RETENTION_YEARS = 7  # Compliance requirement
```

## Manual Data Deletion

For manual data deletion requests (e.g., GDPR erasure requests):

```bash
# Execute erasure request
python manage.py process_erasure_requests --request-id <request_id>

# Verify deletion
python manage.py verify_erasure --request-id <request_id>
```

See [Erasure Implementation](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md) for details.

## Audit and Verification

### Retention Policy Compliance Check

```bash
# Verify retention policies are configured for all firms
python manage.py check_retention_policies

# Audit retention policy execution history
python manage.py audit_retention_history --days 90
```

### Data Volume Reports

```bash
# Report on webhook event volumes
python manage.py report_webhook_volumes

# Report on audit log volumes
python manage.py report_audit_volumes

# Report on storage by firm
python manage.py report_storage_by_firm
```

## Related Documentation

- [Data Retention Implementation](./DATA_RETENTION_IMPLEMENTATION.md) - Technical implementation details
- [GDPR Data Export](./GDPR_DATA_EXPORT_IMPLEMENTATION.md) - Right to access and data portability
- [Erasure Implementation](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md) - Data anonymization and deletion
- [SECURITY.md](../SECURITY.md) - Overall security policy and practices

## Change History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-03 | 1.0 | Initial data retention policy (SEC-3) | Security Team |

## Approval

This policy has been reviewed and approved by:

- [ ] Security Team
- [ ] Legal/Compliance Team
- [ ] Engineering Leadership
- [ ] Data Protection Officer

**Next Review Date:** 2026-07-03 (6 months)
