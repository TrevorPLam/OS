# Django Management Commands Reference

Complete reference for all Django management commands in ConsultantPro.

---

## Table of Contents

1. [Django Built-in Commands](#django-built-in-commands)
2. [Finance Module Commands](#finance-module-commands)
3. [Common Command Patterns](#common-command-patterns)
4. [Scheduling Commands](#scheduling-commands)

---

## Django Built-in Commands

These are standard Django commands available in all Django projects.

### Database Management

#### `migrate`
Apply database migrations.

```bash
python manage.py migrate
```

**Options:**
- `--fake` - Mark migrations as run without actually running them
- `--fake-initial` - Fake initial migration for existing tables
- `app_label migration_name` - Migrate to a specific migration

**Examples:**
```bash
# Apply all pending migrations
python manage.py migrate

# Migrate specific app
python manage.py migrate modules.finance

# Migrate to specific migration
python manage.py migrate modules.finance 0003

# Fake migration (dangerous - use with caution)
python manage.py migrate modules.finance 0003 --fake
```

---

#### `makemigrations`
Create new database migrations.

```bash
python manage.py makemigrations
```

**Options:**
- `--dry-run` - Show what migrations would be created
- `--empty` - Create an empty migration
- `app_label` - Create migrations for specific app

**Examples:**
```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations modules.finance

# Check what would be created
python manage.py makemigrations --dry-run

# Create empty migration
python manage.py makemigrations modules.finance --empty
```

---

#### `showmigrations`
Show all migrations and their status.

```bash
python manage.py showmigrations
```

**Examples:**
```bash
# Show all migrations
python manage.py showmigrations

# Show migrations for specific app
python manage.py showmigrations modules.finance
```

---

#### `sqlmigrate`
Show SQL for a migration.

```bash
python manage.py sqlmigrate app_label migration_name
```

**Examples:**
```bash
python manage.py sqlmigrate modules.finance 0003
```

---

### User Management

#### `createsuperuser`
Create a superuser account.

```bash
python manage.py createsuperuser
```

**Interactive prompts:**
- Username
- Email
- Password (entered twice)

**Non-interactive:**
```bash
python manage.py createsuperuser \
  --username admin \
  --email admin@example.com \
  --noinput
```

---

#### `changepassword`
Change a user's password.

```bash
python manage.py changepassword username
```

---

### Development Tools

#### `runserver`
Start development server.

```bash
python manage.py runserver [address:port]
```

**Examples:**
```bash
# Default (localhost:8000)
python manage.py runserver

# Custom port
python manage.py runserver 8080

# Bind to all interfaces
python manage.py runserver 0.0.0.0:8000

# Specific IP and port
python manage.py runserver 192.168.1.100:8000
```

**⚠️ Warning:** Do NOT use in production. Use Gunicorn/uWSGI instead.

---

#### `shell`
Open Django/Python shell with project context.

```bash
python manage.py shell
```

**Examples:**
```bash
# Standard shell
python manage.py shell

# IPython shell (if installed)
python manage.py shell -i ipython

# Execute Python code
python manage.py shell -c "from modules.firm.models import Firm; print(Firm.objects.count())"
```

---

#### `dbshell`
Open database shell (psql for PostgreSQL).

```bash
python manage.py dbshell
```

---

### System Management

#### `check`
Check for common problems.

```bash
python manage.py check [--deploy]
```

**Options:**
- `--deploy` - Check deployment-specific settings

**Examples:**
```bash
# Basic checks
python manage.py check

# Deployment checks
python manage.py check --deploy
```

---

#### `collectstatic`
Collect static files for deployment.

```bash
python manage.py collectstatic [--noinput]
```

**Options:**
- `--noinput` - Skip confirmation prompt
- `--clear` - Clear existing files first

**Examples:**
```bash
# Interactive
python manage.py collectstatic

# Non-interactive (CI/CD)
python manage.py collectstatic --noinput
```

---

#### `clearsessions`
Clean up expired sessions.

```bash
python manage.py clearsessions
```

**Usage:** Run periodically in cron (daily or weekly).

---

## Finance Module Commands

Custom commands for financial operations in ConsultantPro.

### `generate_package_invoices`

**Purpose:** Generate package fee invoices for active engagements based on billing schedules.

**Location:** `src/modules/finance/management/commands/generate_package_invoices.py`

**Usage:**
```bash
python manage.py generate_package_invoices [options]
```

**Options:**
- `--dry-run` - Show what would be generated without creating invoices
- `--firm-id ID` - Generate invoices for a specific firm only

**Examples:**
```bash
# Generate invoices for all firms
python manage.py generate_package_invoices

# Dry run to preview
python manage.py generate_package_invoices --dry-run

# Generate for specific firm
python manage.py generate_package_invoices --firm-id 123

# Dry run for specific firm
python manage.py generate_package_invoices --dry-run --firm-id 123
```

**What it does:**
1. Finds all active engagements with package billing (`pricing_mode` = 'package' or 'mixed')
2. Checks billing schedules (monthly, quarterly, annual)
3. Generates invoices for periods that are due
4. Prevents duplicate invoice generation (checks for existing invoices in same period)
5. Only processes firms with active or trial status

**Scheduling:**
```bash
# Cron: Run daily at 2 AM
0 2 * * * cd /path/to/OS && /path/to/.venv/bin/python src/manage.py generate_package_invoices
```

**Output Example:**
```
Processing firm: Acme Consulting (ID: 1)
  ✓ Generated invoice for engagement 45: INV-2025-001 ($5000.00)
  ✓ Generated invoice for engagement 67: INV-2025-002 ($10000.00)
  - Skipped engagement 89: Invoice already exists for this period

Summary:
  Firms processed: 3
  Invoices generated: 15
  Engagements skipped: 8
  Errors: 0
```

**Documentation:** [Package Invoice Deployment Guide](../../docs/tier4/PACKAGE_INVOICE_DEPLOYMENT.md)

---

### `process_recurring_charges`

**Purpose:** Execute autopay for invoices scheduled for recurring billing.

**Location:** `src/modules/finance/management/commands/process_recurring_charges.py`

**Usage:**
```bash
python manage.py process_recurring_charges [options]
```

**Options:**
- `--dry-run` - List invoices that would be charged without executing

**Examples:**
```bash
# Process autopay for all eligible invoices
python manage.py process_recurring_charges

# Dry run to preview
python manage.py process_recurring_charges --dry-run
```

**What it does:**
1. Finds invoices with autopay enabled (`autopay_opt_in=True`)
2. Checks if next charge date has passed (`autopay_next_charge_at`)
3. Processes payment via Stripe using stored payment method
4. Handles retries on failure (3, 7, 14 day schedule)
5. Updates invoice status and payment records

**Eligibility Criteria:**
- Invoice has `autopay_opt_in=True`
- Invoice status is `sent`, `partial`, or `overdue`
- `autopay_next_charge_at` is in the past or null
- Client has valid `payment_method_id` (Stripe)

**Scheduling:**
```bash
# Cron: Run daily at 3 AM (after invoice generation)
0 3 * * * cd /path/to/OS && /path/to/.venv/bin/python src/manage.py process_recurring_charges
```

**Output Example:**
```
Processing autopay charges...
  ✓ Charged invoice INV-2025-001 for $5000.00
  ✓ Charged invoice INV-2025-003 for $2500.00
  ⚠ Failed to charge INV-2025-005: Card declined (will retry in 3 days)

Summary:
  Invoices charged: 2
  Total amount charged: $7500.00
  Failed charges: 1
```

**Retry Logic:**
- First failure: Retry in 3 days
- Second failure: Retry in 7 days
- Third failure: Retry in 14 days
- After 3 failures: Mark as failed, requires manual intervention

**Documentation:** [Autopay Status Guide](../../docs/tier4/AUTOPAY_STATUS.md)

---

## Common Command Patterns

### Dry Run Pattern

Many commands support `--dry-run` for safety:

```bash
# Preview changes without executing
python manage.py command --dry-run

# Execute after preview
python manage.py command
```

**Best Practice:** Always run with `--dry-run` first in production.

---

### Firm-Scoped Operations

For tenant-specific operations:

```bash
# All firms
python manage.py command

# Specific firm
python manage.py command --firm-id 123
```

---

### Logging Output

Capture command output for auditing:

```bash
# Log to file
python manage.py command >> /var/log/consultantpro/command.log 2>&1

# Log with timestamp
python manage.py command 2>&1 | ts >> /var/log/consultantpro/command.log
```

---

## Scheduling Commands

### Cron Setup (Linux/macOS)

Edit crontab:
```bash
crontab -e
```

**Example crontab:**
```bash
# Environment variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
DJANGO_SETTINGS_MODULE=config.settings

# Load environment from .env
# Note: Source .env file in each command or use python-dotenv

# Generate package invoices daily at 2 AM
0 2 * * * cd /path/to/OS && /path/to/.venv/bin/python src/manage.py generate_package_invoices >> /var/log/consultantpro/invoices.log 2>&1

# Process recurring charges daily at 3 AM
0 3 * * * cd /path/to/OS && /path/to/.venv/bin/python src/manage.py process_recurring_charges >> /var/log/consultantpro/autopay.log 2>&1

# Clean up expired sessions weekly (Sunday at 4 AM)
0 4 * * 0 cd /path/to/OS && /path/to/.venv/bin/python src/manage.py clearsessions >> /var/log/consultantpro/sessions.log 2>&1
```

**Cron time format:**
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-6, Sunday = 0)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

---

### Systemd Timers (Alternative to Cron)

**Create service file:** `/etc/systemd/system/generate-invoices.service`
```ini
[Unit]
Description=Generate Package Invoices
After=network.target postgresql.service

[Service]
Type=oneshot
User=consultantpro
WorkingDirectory=/path/to/OS
Environment="DJANGO_SETTINGS_MODULE=config.settings"
EnvironmentFile=/path/to/OS/.env
ExecStart=/path/to/.venv/bin/python src/manage.py generate_package_invoices
StandardOutput=journal
StandardError=journal
```

**Create timer file:** `/etc/systemd/system/generate-invoices.timer`
```ini
[Unit]
Description=Generate Package Invoices Daily
Requires=generate-invoices.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable timer:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable generate-invoices.timer
sudo systemctl start generate-invoices.timer

# Check status
sudo systemctl status generate-invoices.timer
sudo systemctl list-timers
```

---

### Docker Compose (Scheduled Container)

**Add to docker-compose.yml:**
```yaml
  scheduler:
    build: .
    command: >
      sh -c "
        while true; do
          python manage.py generate_package_invoices
          python manage.py process_recurring_charges
          sleep 86400
        done
      "
    environment:
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - POSTGRES_HOST=db
    depends_on:
      - db
    restart: unless-stopped
```

**Better approach:** Use a cron container or Celery Beat.

---

## Monitoring & Alerting

### Command Monitoring

**Check last run:**
```bash
# View cron logs
grep "generate_package_invoices" /var/log/cron

# View application logs
tail -f /var/log/consultantpro/invoices.log
```

**Alert on failures:**
```bash
# In cron job, send email on error
0 2 * * * /path/to/script.sh || echo "Invoice generation failed" | mail -s "Alert" admin@example.com
```

---

### Health Checks

Create a simple health check script:

**`/path/to/OS/scripts/check_billing_health.sh`:**
```bash
#!/bin/bash

# Check if last invoice generation was successful
LAST_RUN=$(grep -c "Successfully generated" /var/log/consultantpro/invoices.log | tail -1)

if [ $LAST_RUN -eq 0 ]; then
    echo "WARNING: No invoices generated in last run"
    exit 1
fi

echo "Billing health check passed"
exit 0
```

---

## Troubleshooting

### "No module named 'config'"

**Solution:** Ensure you're in the `src/` directory or set `PYTHONPATH`:
```bash
cd /path/to/OS/src
python manage.py command

# OR

export PYTHONPATH=/path/to/OS/src
python /path/to/OS/src/manage.py command
```

---

### "Database connection refused"

**Solution:** Check environment variables and database service:
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB

# Verify environment variables
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES)"
```

---

### "Permission denied" in cron

**Solution:** Ensure correct user and paths:
```bash
# Run as correct user
0 2 * * * su - consultantpro -c "cd /path/to/OS && /path/to/.venv/bin/python src/manage.py command"

# OR use full paths and environment
0 2 * * * cd /path/to/OS && /path/to/.venv/bin/python src/manage.py command
```

---

### Commands not appearing

**Solution:** Ensure management command structure is correct:
```
modules/
  finance/
    management/
      __init__.py          # Must exist!
      commands/
        __init__.py        # Must exist!
        command_name.py    # Your command
```

---

## Best Practices

1. **Always use --dry-run first** in production
2. **Log all command output** for auditing
3. **Monitor command execution** with health checks
4. **Use absolute paths** in cron jobs
5. **Set environment variables** properly
6. **Test commands manually** before scheduling
7. **Document custom commands** with docstrings
8. **Handle errors gracefully** with proper logging
9. **Use transactions** for data modifications
10. **Schedule during off-peak hours** (2-4 AM typical)

---

## Related Documentation

- [Environment Variables Reference](environment-variables.md) - Configuration
- [Production Deployment Guide](../02-how-to/production-deployment.md) - Deployment
- [Tier 4 Documentation](../../docs/tier4/) - Billing & monetization guides
- [Package Invoice Deployment](../../docs/tier4/PACKAGE_INVOICE_DEPLOYMENT.md) - Invoice automation
- [Autopay Status](../../docs/tier4/AUTOPAY_STATUS.md) - Recurring payments

---

**Last Updated:** December 26, 2025
