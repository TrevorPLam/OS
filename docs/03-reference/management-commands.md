# Management Commands Reference

Document Type: Reference
Last Updated: 2026-01-24

This document lists all Django management commands available in ConsultantPro with verified options.

**Why this structure:** Commands are grouped by module so operators can map CLI operations back to domain ownership. Evidence references link to the command implementation to avoid drift.

## Usage

Run locally:
```bash
python manage.py <command_name> [options]
```

Run via Docker Compose:
```bash
docker-compose exec web python manage.py <command_name> [options]
```

## Finance Module Commands

### reconcile_stripe
Reconciles invoice records with Stripe API and reports mismatches.

**Usage:**
```bash
python manage.py reconcile_stripe [--firm-id FIRM_ID]
```

**Options:**
- `--firm-id`: Reconcile invoices for a specific firm (optional).

**Evidence:** `src/modules/finance/management/commands/reconcile_stripe.py`

### refresh_materialized_views
Refreshes reporting materialized views (revenue/utilization).

**Usage:**
```bash
python manage.py refresh_materialized_views [--view VIEW] [--firm-id FIRM_ID] [--no-concurrent]
```

**Options:**
- `--view`: `all` (default), `revenue`, `utilization_user`, `utilization_project`.
- `--firm-id`: Accepted but refreshes all data (Postgres MV limitation).
- `--no-concurrent`: Disable concurrent refresh (blocks reads).

**Evidence:** `src/modules/finance/management/commands/refresh_materialized_views.py`

### process_recurring_charges
Charges invoices due for autopay.

**Usage:**
```bash
python manage.py process_recurring_charges [--dry-run] [--firm-id FIRM_ID]
```

**Options:**
- `--dry-run`: List invoices that would be charged.
- `--firm-id`: Process invoices for a specific firm.

**Evidence:** `src/modules/finance/management/commands/process_recurring_charges.py`

### generate_package_invoices
Generates package-based invoices for engagements.

**Usage:**
```bash
python manage.py generate_package_invoices [--dry-run] [--firm-id FIRM_ID]
```

**Options:**
- `--dry-run`: Show what would be generated without creating invoices.
- `--firm-id`: Generate invoices for a specific firm.

**Evidence:** `src/modules/finance/management/commands/generate_package_invoices.py`

## Firm Management Commands

### provision_firm
Provisions a new firm with baseline configuration.

**Usage:**
```bash
python manage.py provision_firm \
  --name "Acme Consulting" \
  --slug acme-consulting \
  --admin-email admin@acme.com \
  --admin-password secure123 \
  [--admin-first-name FIRST] \
  [--admin-last-name LAST] \
  [--timezone "America/New_York"] \
  [--currency USD] \
  [--tier starter|professional|enterprise] \
  [--max-users 5] \
  [--max-clients 25] \
  [--max-storage-gb 10]
```

**Evidence:** `src/modules/firm/management/commands/provision_firm.py`

## Data Management & Compliance Commands

### execute_retention_policies
Executes data retention policies for active firms.

**Usage:**
```bash
python manage.py execute_retention_policies [--firm-id FIRM_ID] [--data-type TYPE] [--dry-run]
```

**Options:**
- `--firm-id`: Execute policies for a specific firm.
- `--data-type`: Filter by retention data type.
- `--dry-run`: Show what would be processed without changes.

**Evidence:** `src/modules/core/management/commands/execute_retention_policies.py`

### export_user_data
Exports user/client data for GDPR access requests.

**Usage:**
```bash
python manage.py export_user_data --client-id CLIENT_ID [--format json|csv|both] [--output-dir PATH]
python manage.py export_user_data --email user@example.com [--format json|csv|both] [--output-dir PATH]
```

**Options:**
- `--client-id`: Client ID to export (required unless `--email` is provided).
- `--email`: Email to export (required unless `--client-id` is provided).
- `--format`: Export format (`json`, `csv`, `both`).
- `--output-dir`: Output directory (default `./exports`).

**Evidence:** `src/modules/core/management/commands/export_user_data.py`

### execute_erasure_request
Executes an approved erasure/anonymization request.

**Usage:**
```bash
python manage.py execute_erasure_request REQUEST_ID [--dry-run]
```

**Options:**
- `REQUEST_ID`: Erasure request ID (positional argument).
- `--dry-run`: Preview anonymization without executing.

**Note:** Command requires interactive confirmation (`ANONYMIZE`) when not running in dry-run mode.

**Evidence:** `src/modules/core/management/commands/execute_erasure_request.py`

### cleanup_webhook_events
Cleans up old webhook event records based on retention policy.

**Usage:**
```bash
python manage.py cleanup_webhook_events [--retention-days DAYS] [--provider stripe|square|docusign|sms] [--dry-run]
```

**Options:**
- `--retention-days`: Days to retain (default from settings).
- `--provider`: Limit cleanup to a specific provider.
- `--dry-run`: Show what would be deleted without changes.

**Evidence:** `src/modules/core/management/commands/cleanup_webhook_events.py`

## Document Management Commands

### send_file_request_reminders
Sends scheduled reminders for pending file requests.

**Usage:**
```bash
python manage.py send_file_request_reminders [--dry-run]
```

**Options:**
- `--dry-run`: Show reminders without sending.

**Evidence:** `src/modules/documents/management/commands/send_file_request_reminders.py`

### reconcile_s3
Reconciles document versions with S3 storage.

**Usage:**
```bash
python manage.py reconcile_s3 [--firm-id FIRM_ID]
```

**Options:**
- `--firm-id`: Reconcile documents for a specific firm.

**Evidence:** `src/modules/documents/management/commands/reconcile_s3.py`

## Calendar & Workflow Commands

### execute_pending_workflows
Executes pending calendar workflow actions.

**Usage:**
```bash
python manage.py execute_pending_workflows
```

**Evidence:** `src/modules/calendar/management/commands/execute_pending_workflows.py`

## CRM Commands

### check_stale_deals
Checks for stale deals and creates alerts.

**Usage:**
```bash
python manage.py check_stale_deals [--firm-id FIRM_ID] [--send-notifications] [--days DAYS]
```

**Options:**
- `--firm-id`: Process deals for a specific firm.
- `--send-notifications`: Send notifications for created alerts.
- `--days`: Override stale threshold in days.

**Evidence:** `src/modules/crm/management/commands/check_stale_deals.py`

### send_stale_deal_reminders
Sends reminder emails for stale deals.

**Usage:**
```bash
python manage.py send_stale_deal_reminders [--dry-run] [--firm-id FIRM_ID]
```

**Options:**
- `--dry-run`: Run without sending emails.
- `--firm-id`: Process deals for a specific firm.

**Evidence:** `src/modules/crm/management/commands/send_stale_deal_reminders.py`

## Active Directory Integration Commands

### sync_ad
Synchronizes users from Active Directory.

**Usage:**
```bash
python manage.py sync_ad [--firm-id FIRM_ID] [--full] [--delta] [--dry-run]
```

**Options:**
- `--firm-id`: Sync a specific firm (otherwise sync all).
- `--full`: Perform a full sync.
- `--delta`: Perform a delta sync.
- `--dry-run`: Preview sync without applying changes (not implemented).

**Evidence:** `src/modules/ad_sync/management/commands/sync_ad.py`

## Core / Development Commands

### load_fixtures
Seeds deterministic fixture data for local development.

**Usage:**
```bash
python manage.py load_fixtures
```

**Notes:**
- `FIXTURE_USER_PASSWORD` can override the default fixture user password.

**Evidence:** `src/modules/core/management/commands/load_fixtures.py`

## Scheduling Guidance

Most management commands should be scheduled as cron jobs or Celery periodic tasks in production.

**Daily (suggested):**
- `reconcile_stripe` - 2:00 AM
- `reconcile_s3` - 3:00 AM
- `cleanup_webhook_events` - 4:00 AM
- `send_file_request_reminders` - 9:00 AM
- `check_stale_deals` - 10:00 AM
- `send_stale_deal_reminders` - 10:30 AM

**Weekly (suggested):**
- `execute_retention_policies` - Sunday 1:00 AM

**Hourly (suggested):**
- `process_recurring_charges` - Top of each hour
- `execute_pending_workflows` - Every 15 minutes

**As needed:**
- `provision_firm` - Manual or API-triggered
- `export_user_data` - On user request
- `execute_erasure_request` - On user request
- `generate_package_invoices` - Based on billing cycles
- `load_fixtures` - Local/dev only

## See Also
- [Django Management Commands Documentation](https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/)
- [Operations Guide](../OPERATIONS.md)
- [Environment Variables Reference](environment-variables.md)
