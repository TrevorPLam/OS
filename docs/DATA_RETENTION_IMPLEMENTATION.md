# Data Retention Policy Implementation (ASSESS-L19.4)

**Status:** Implemented  
**Last Updated:** December 2025

## Overview

This document describes the implementation of configurable data retention policies and auto-purge functionality for old data per firm requirements.

## Features

### Retention Policy Configuration

Firms can configure retention policies for different data types:

- **Audit Logs**
- **Documents**
- **Invoices**
- **Projects**
- **Time Entries**
- **Communications**
- **Email Artifacts**
- **Support Tickets**
- **Leads**
- **Prospects**

### Retention Actions

When retention period expires, one of three actions can be taken:

1. **Archive** - Move to cold storage (preserves data, reduces active storage)
2. **Anonymize** - Remove PII while preserving data structure
3. **Delete** - Permanent removal (with safeguards)

### Policy Configuration Options

- **Retention Days**: Number of days to retain data (0 = no limit)
- **Action**: What to do when retention expires
- **Only If Inactive**: Only apply to inactive/closed records
- **Preserve Legal Hold**: Never purge data under legal hold

## Usage

### Execute Retention Policies

Run retention policies for all active firms:

```bash
python manage.py execute_retention_policies
```

**Options:**
- `--firm-id`: Execute for specific firm only
- `--data-type`: Execute for specific data type only
- `--dry-run`: Show what would be processed without modifying data

**Examples:**
```bash
# Dry run for all firms
python manage.py execute_retention_policies --dry-run

# Execute for specific firm
python manage.py execute_retention_policies --firm-id 123

# Execute for specific data type
python manage.py execute_retention_policies --data-type leads

# Execute for specific firm and data type
python manage.py execute_retention_policies --firm-id 123 --data-type documents
```

### Create Retention Policy

Retention policies are created via Django admin or API:

```python
from modules.core.retention import RetentionPolicy

policy = RetentionPolicy.objects.create(
    firm=firm,
    data_type='leads',
    retention_days=365,  # 1 year
    action=RetentionPolicy.ACTION_ANONYMIZE,
    only_if_inactive=True,  # Only anonymize lost/converted leads
    preserve_legal_hold=True
)
```

## Retention Execution

### Execution Record

Each execution creates a `RetentionExecution` record with:
- Execution timestamp
- Records processed/archived/anonymized/deleted/skipped
- Detailed execution results
- Error messages (if any)

### Safeguards

1. **Legal Hold**: Data under legal hold is never purged
2. **Active Records**: Can optionally preserve active records
3. **Audit Trail**: All executions are logged
4. **Dry Run**: Test policies before execution

## Default Policies

Recommended default retention policies:

- **Audit Logs**: 7 years (compliance requirement)
- **Documents**: 5 years (or per engagement end date)
- **Invoices**: 7 years (tax/accounting requirement)
- **Projects**: 3 years after completion
- **Time Entries**: 7 years (payroll/tax requirement)
- **Leads**: 1 year after lost/converted (anonymize)
- **Prospects**: 1 year after won/lost (anonymize)

## Scheduling

Retention policies should be executed regularly (e.g., daily cron):

```bash
# Add to crontab
0 2 * * * cd /path/to/app && python manage.py execute_retention_policies
```

## Integration

### With Erasure Workflow

Retention policies work alongside the erasure workflow:
- Retention policies: Automated bulk purging
- Erasure requests: Manual individual requests

### With Legal Hold

Data under legal hold is automatically skipped:
- Check `legal_hold` field on documents
- Check `metadata.legal_hold` on audit logs
- Never purge data under legal hold

## Compliance

### GDPR

- Retention policies respect GDPR requirements
- Data can be anonymized instead of deleted
- Legal hold overrides retention policies

### Industry Standards

- Financial records: 7 years (invoices, time entries)
- Audit logs: 7 years (compliance)
- Marketing data: 1 year (leads, prospects)

## Future Enhancements

- Automated scheduling via Django Q/Celery
- Per-engagement retention policies
- Retention policy templates
- Notification before data purging
- Granular retention rules (e.g., by document type)

## References

- **ASSESS-L19.4:** Data retention policy implementation
- **GDPR Article 5(1)(e):** Storage limitation principle
- [Erasure Implementation](./ERASURE_ANONYMIZATION_IMPLEMENTATION.md)