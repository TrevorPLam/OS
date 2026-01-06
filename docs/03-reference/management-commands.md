# Management Commands Reference

Document Type: Reference
Last Updated: 2026-01-06

This document lists all Django management commands available in ConsultantPro.

## Overview

Management commands are run using:
```bash
python manage.py <command_name> [options]
```

Or using Docker Compose:
```bash
docker-compose exec web python manage.py <command_name> [options]
```

## Finance Module Commands

### reconcile_stripe
Reconciles Invoice records with Stripe API to detect mismatches.

**Purpose**: Daily cron job to cross-check local invoice status vs Stripe API (ASSESS-G18.5).

**Usage**:
```bash
python manage.py reconcile_stripe [--firm-id FIRM_ID]
```

**Options**:
- `--firm-id`: Reconcile invoices for a specific firm only (optional)

**Example**:
```bash
# Reconcile all firms
python manage.py reconcile_stripe

# Reconcile specific firm
python manage.py reconcile_stripe --firm-id 123
```

### refresh_materialized_views
Refreshes materialized views for billing ledger and financial analytics.

**Purpose**: Maintains up-to-date financial reporting views.

**Usage**:
```bash
python manage.py refresh_materialized_views
```

### process_recurring_charges
Processes recurring charges for active subscriptions.

**Purpose**: Generates invoices for recurring billing cycles.

**Usage**:
```bash
python manage.py process_recurring_charges
```

### generate_package_invoices
Generates package-based invoices for clients with pre-purchased service packages.

**Purpose**: Creates invoices from package allocations.

**Usage**:
```bash
python manage.py generate_package_invoices
```

## Firm Management Commands

### provision_firm
Provisions a new firm with baseline configuration (DOC-19.1).

**Purpose**: Initial firm setup with admin user, default settings, and permissions.

**Usage**:
```bash
python manage.py provision_firm \
    --name "Acme Consulting" \
    --slug acme-consulting \
    --admin-email admin@acme.com \
    --admin-password secure123 \
    --timezone "America/Los_Angeles" \
    --currency USD \
    --tier professional
```

**Required Options**:
- `--name`: Firm name
- `--slug`: URL-safe slug for the firm
- `--admin-email`: Admin user email address
- `--admin-password`: Admin user password

**Optional Options**:
- `--timezone`: Default timezone (default: UTC)
- `--currency`: Default currency code (default: USD)
- `--tier`: Subscription tier (default: professional)

## Data Management & Compliance Commands

### execute_retention_policies
Executes data retention policies for all active firms (ASSESS-L19.4).

**Purpose**: Automates data cleanup according to configured retention schedules.

**Usage**:
```bash
python manage.py execute_retention_policies [options]
```

**Options**:
- `--firm-id FIRM_ID`: Execute policies for a specific firm only
- `--data-type TYPE`: Execute policies for a specific data type only
  - Choices: `emails`, `documents`, `audit_logs`, `webhooks`, `sessions`
- `--dry-run`: Show what would be processed without modifying data

**Examples**:
```bash
# Execute all retention policies
python manage.py execute_retention_policies

# Dry run for specific firm
python manage.py execute_retention_policies --firm-id 123 --dry-run

# Process only webhook event cleanup
python manage.py execute_retention_policies --data-type webhooks
```

### export_user_data
Exports user data for GDPR/CCPA compliance (right to data portability).

**Purpose**: Generates comprehensive data export for a specific user.

**Usage**:
```bash
python manage.py export_user_data --user-id USER_ID [--output-dir PATH]
```

**Options**:
- `--user-id`: User ID to export data for (required)
- `--output-dir`: Directory for export files (default: current directory)

**Example**:
```bash
python manage.py export_user_data --user-id 456 --output-dir /exports/
```

### execute_erasure_request
Executes a user data erasure request (GDPR right to be forgotten).

**Purpose**: Permanently removes or anonymizes user data per erasure request.

**Usage**:
```bash
python manage.py execute_erasure_request --request-id REQUEST_ID [--dry-run]
```

**Options**:
- `--request-id`: Erasure request ID (required)
- `--dry-run`: Preview what would be erased without making changes

**Example**:
```bash
# Preview erasure
python manage.py execute_erasure_request --request-id 789 --dry-run

# Execute erasure
python manage.py execute_erasure_request --request-id 789
```

### cleanup_webhook_events
Cleans up old webhook event records based on retention policy.

**Purpose**: Removes webhook events older than configured retention period (SEC-3).

**Usage**:
```bash
python manage.py cleanup_webhook_events [--days DAYS] [--dry-run]
```

**Options**:
- `--days`: Number of days to retain (default: from WEBHOOK_RETENTION_DAYS env var)
- `--dry-run`: Show what would be deleted without making changes

**Example**:
```bash
# Use default retention period
python manage.py cleanup_webhook_events

# Custom retention period
python manage.py cleanup_webhook_events --days 90
```

## Document Management Commands

### send_file_request_reminders
Sends reminder notifications for pending file requests.

**Purpose**: Reminds clients to upload requested documents.

**Usage**:
```bash
python manage.py send_file_request_reminders [--firm-id FIRM_ID]
```

**Options**:
- `--firm-id`: Process reminders for specific firm only (optional)

### reconcile_s3
Reconciles document records with S3 storage.

**Purpose**: Detects and reports mismatches between database records and S3 objects.

**Usage**:
```bash
python manage.py reconcile_s3 [--firm-id FIRM_ID]
```

**Options**:
- `--firm-id`: Reconcile documents for specific firm only (optional)

## Calendar & Workflow Commands

### execute_pending_workflows
Executes pending calendar workflow actions (meeting prep, follow-ups).

**Purpose**: Processes scheduled workflow tasks from calendar events.

**Usage**:
```bash
python manage.py execute_pending_workflows
```

## CRM Commands

### check_stale_deals
Checks for stale deals based on configured thresholds.

**Purpose**: Identifies deals with no activity for extended periods.

**Usage**:
```bash
python manage.py check_stale_deals [--firm-id FIRM_ID]
```

**Options**:
- `--firm-id`: Check deals for specific firm only (optional)

### send_stale_deal_reminders
Sends reminder notifications for stale deals.

**Purpose**: Alerts deal owners about deals requiring attention.

**Usage**:
```bash
python manage.py send_stale_deal_reminders [--firm-id FIRM_ID]
```

**Options**:
- `--firm-id`: Send reminders for specific firm only (optional)

## Active Directory Integration Commands

### sync_ad
Synchronizes users from Active Directory (LDAP).

**Purpose**: Imports and updates user accounts from Active Directory.

**Usage**:
```bash
python manage.py sync_ad --firm-id FIRM_ID [options]
```

**Required Options**:
- `--firm-id`: Firm ID with Active Directory integration enabled

**Optional Options**:
- `--dry-run`: Preview sync without making changes
- `--full-sync`: Perform full sync instead of incremental

**Examples**:
```bash
# Preview sync
python manage.py sync_ad --firm-id 123 --dry-run

# Full synchronization
python manage.py sync_ad --firm-id 123 --full-sync
```

## Scheduling Commands

Most management commands should be scheduled as cron jobs or Celery periodic tasks in production.

### Recommended Schedule

**Daily**:
- `reconcile_stripe` - 2:00 AM
- `reconcile_s3` - 3:00 AM
- `cleanup_webhook_events` - 4:00 AM
- `send_file_request_reminders` - 9:00 AM
- `check_stale_deals` - 10:00 AM
- `send_stale_deal_reminders` - 10:30 AM

**Weekly**:
- `execute_retention_policies` - Sunday 1:00 AM

**Hourly**:
- `process_recurring_charges` - Top of each hour
- `execute_pending_workflows` - Every 15 minutes

**As Needed**:
- `provision_firm` - Manual or API-triggered
- `export_user_data` - On user request
- `execute_erasure_request` - On user request
- `generate_package_invoices` - Based on billing cycles

## See Also
- [Django Management Commands Documentation](https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/)
- [OPERATIONS.md](../OPERATIONS.md) - Operational procedures
- [docs/03-reference/environment-variables.md](environment-variables.md) - Environment configuration
