# Package Invoice Generation - Deployment Guide

## Overview

Package fee invoices are automatically generated for engagements with `pricing_mode='package'` or `'mixed'`. The system prevents duplicate invoices and supports monthly, quarterly, annual, and one-time billing schedules.

## Manual Execution

Generate invoices for all firms:
```bash
python manage.py generate_package_invoices
```

Generate invoices for a specific firm:
```bash
python manage.py generate_package_invoices --firm-id 123
```

Dry run (see what would be generated):
```bash
python manage.py generate_package_invoices --dry-run
```

## Scheduled Execution (Cron)

Until Celery is integrated, use cron to run the command daily:

```cron
# Generate package invoices daily at 2 AM
0 2 * * * cd /home/user/OS && python src/manage.py generate_package_invoices >> /var/log/package_invoices.log 2>&1
```

## Behavior

1. **Period Calculation**: Determines billing period based on `package_fee_schedule`:
   - `Monthly`: First to last day of current month
   - `Quarterly`: First day of quarter to last day of quarter
   - `Annual`: January 1 to December 31
   - `One-time`: Engagement start date to end date

2. **Duplicate Prevention**: Uses `(engagement, period_start)` uniqueness to prevent duplicate invoices

3. **Automatic Features**:
   - Invoice status: `sent`
   - Due date: 30 days from issue
   - Invoice number: `PKG-{engagement_id}-{period_start}`
   - Audit logging: All generated invoices logged to audit system

4. **Autopay Integration**: If client has `autopay_enabled=True`, invoice includes autopay metadata

## Testing

Run tests:
```bash
pytest tests/finance/test_billing.py::test_package_invoice_generation_and_duplicate_prevention
pytest tests/finance/test_billing.py::test_package_invoices_survive_renewal_without_touching_old_invoice
```

## Future Enhancement

When Celery is integrated (Tier 5+), replace cron with:

```python
# In modules/finance/tasks.py
from celery import shared_task
from modules.finance.billing import generate_package_invoices

@shared_task
def generate_package_invoices_task():
    """Daily Celery task to generate package invoices."""
    return generate_package_invoices()
```

Schedule in `celery_beat_schedule`:
```python
'generate-package-invoices': {
    'task': 'modules.finance.tasks.generate_package_invoices_task',
    'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
},
```
