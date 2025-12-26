# Tier 4: Billing & Monetization Documentation

**Status:** ✅ 100% Complete
**Last Updated:** December 26, 2025

---

## Overview

Tier 4 implements a complete billing and monetization system for ConsultantPro, including package invoicing, recurring payments, autopay, payment failure handling, and dispute management.

All features are production-ready with comprehensive test coverage and deployment documentation.

---

## Documentation Index

### 📋 Summary & Architecture

**[TIER_4_COMPLETION_SUMMARY.md](TIER_4_COMPLETION_SUMMARY.md)**
- Complete overview of all 8 tasks
- Architecture principles and design decisions
- Testing summary and deployment checklist
- Monitoring and alerting recommendations
- Future enhancement roadmap

**Start here** for a comprehensive understanding of Tier 4.

---

### 🚀 Deployment Guides

#### [PACKAGE_INVOICE_DEPLOYMENT.md](PACKAGE_INVOICE_DEPLOYMENT.md)
**Task 4.2: Package Fee Invoicing**

Topics covered:
- Manual invoice generation commands
- Cron scheduling configuration
- Billing period calculation logic
- Duplicate prevention mechanism
- Testing procedures
- Future Celery integration plan

**Use this** when deploying package invoice automation.

---

#### [AUTOPAY_STATUS.md](AUTOPAY_STATUS.md)
**Task 4.6: Recurring Payments/Autopay Workflow**

Topics covered:
- Autopay workflow implementation details
- Client and invoice model fields
- Stripe integration with PaymentIntent API
- Webhook configuration
- Retry logic and failure handling
- Management command usage
- Deployment instructions

**Use this** when setting up recurring payment processing.

---

#### [PAYMENT_FAILURE_STATUS.md](PAYMENT_FAILURE_STATUS.md)
**Task 4.7: Payment Failures, Disputes & Chargebacks**

Topics covered:
- Payment failure tracking and metadata
- Retry schedule implementation (3/7/14 days)
- Dispute lifecycle management
- Chargeback handling and amount adjustments
- Stripe webhook integration
- Audit logging for compliance
- Monitoring and alerting strategies

**Use this** when configuring payment failure and dispute workflows.

---

### 📖 Design Documentation

#### [BILLING_INVARIANTS_AND_ARCHITECTURE.md](BILLING_INVARIANTS_AND_ARCHITECTURE.md)
**Original Design Document**

Topics covered:
- Billing invariants and constraints
- Package fee invoicing design
- Hourly billing with approval gates
- Mixed billing architecture
- Credit ledger design
- Renewal billing behavior

**Use this** to understand the original architecture and design decisions.

---

#### [PAYMENT_FAILURE_HANDLING.md](PAYMENT_FAILURE_HANDLING.md)
**Original Failure Handling Specification**

Topics covered:
- Payment failure scenarios
- Retry logic design
- Dispute tracking requirements
- Webhook event handling
- Audit requirements

**Use this** to understand the design rationale for failure handling.

---

## Quick Reference

### Management Commands

```bash
# Package Invoice Generation
python manage.py generate_package_invoices [--dry-run] [--firm-id ID]

# Recurring Payment Processing
python manage.py process_recurring_charges [--dry-run]
```

### Cron Configuration

```cron
# Package invoices (daily at 2 AM)
0 2 * * * cd /path/to/OS && python src/manage.py generate_package_invoices

# Recurring payments (daily at 3 AM)
0 3 * * * cd /path/to/OS && python src/manage.py process_recurring_charges
```

### Environment Variables

```bash
# Required for Stripe integration
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### Stripe Webhook Events

Subscribe to these events at `https://your-domain.com/api/webhooks/stripe/`:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `charge.refunded`
- `charge.dispute.created`
- `charge.dispute.closed`

---

## Implementation Status

| Task | Status | Documentation | Tests |
|------|--------|---------------|-------|
| 4.1: Billing Invariants | ✅ Complete | BILLING_INVARIANTS_AND_ARCHITECTURE.md | ✅ Pass |
| 4.2: Package Invoicing | ✅ Complete | PACKAGE_INVOICE_DEPLOYMENT.md | ✅ Pass |
| 4.3: Hourly Billing | ✅ Complete | BILLING_INVARIANTS_AND_ARCHITECTURE.md | ✅ Pass |
| 4.4: Mixed Billing | ✅ Complete | BILLING_INVARIANTS_AND_ARCHITECTURE.md | ✅ Pass |
| 4.5: Credit Ledger | ✅ Complete | BILLING_INVARIANTS_AND_ARCHITECTURE.md | ✅ Pass |
| 4.6: Autopay Workflow | ✅ Complete | AUTOPAY_STATUS.md | ✅ Pass |
| 4.7: Payment Failures | ✅ Complete | PAYMENT_FAILURE_STATUS.md | ✅ Pass |
| 4.8: Renewal Billing | ✅ Complete | BILLING_INVARIANTS_AND_ARCHITECTURE.md | ✅ Pass |

**Overall Status:** 100% Complete (8/8 tasks)

---

## Testing

### Run All Billing Tests

```bash
# All billing-related tests
pytest tests/finance/

# Specific test suites
pytest tests/finance/test_billing.py
pytest tests/finance/test_recurring_autopay.py
pytest tests/e2e/test_sales_to_cash_flow.py
```

### Test Coverage

```bash
pytest tests/finance/ --cov=src/modules/finance --cov-report=html
```

View coverage report: `htmlcov/index.html`

---

## Key Files

### Backend
- `src/modules/finance/models.py` - Invoice, PaymentDispute, PaymentFailure models
- `src/modules/finance/billing.py` - Core billing logic and workflows
- `src/modules/finance/services.py` - Stripe service integration
- `src/modules/clients/models.py` - Client, ClientEngagement with autopay fields

### API
- `src/api/finance/webhooks.py` - Stripe webhook handlers
- `src/api/finance/views.py` - Invoice API endpoints

### Management Commands
- `src/modules/finance/management/commands/generate_package_invoices.py`
- `src/modules/finance/management/commands/process_recurring_charges.py`

### Tests
- `tests/finance/test_billing.py` - Core billing tests
- `tests/finance/test_recurring_autopay.py` - Autopay workflow tests
- `tests/e2e/test_sales_to_cash_flow.py` - End-to-end integration tests

---

## Support & Troubleshooting

### Common Issues

**Package Invoices Not Generating?**
- Check engagement has `pricing_mode='package'` or `'mixed'`
- Verify `package_fee` is set on engagement
- Confirm engagement dates overlap billing period
- Run with `--dry-run` to see what would be generated

**Autopay Not Charging?**
- Verify client has `autopay_enabled=True`
- Check `autopay_payment_method_id` is set
- Confirm invoice has `autopay_opt_in=True`
- Check `autopay_next_charge_at` is in the past
- Review logs for payment processor errors

**Webhooks Not Working?**
- Verify webhook URL is publicly accessible
- Check `STRIPE_WEBHOOK_SECRET` matches Stripe dashboard
- Review webhook logs in Stripe dashboard
- Ensure events are subscribed correctly

### Debugging

Enable verbose logging:
```python
# In Django settings
LOGGING = {
    'loggers': {
        'modules.finance': {
            'level': 'DEBUG',
        }
    }
}
```

Check audit logs:
```python
from modules.firm.audit import AuditEvent

# Recent billing events
AuditEvent.objects.filter(
    category='billing',
    created_at__gte=timezone.now() - timedelta(days=7)
).order_by('-created_at')
```

---

## Next Steps

With Tier 4 complete, the platform is ready for:

1. **Production Deployment**
   - Configure Stripe webhooks
   - Set up cron jobs for automation
   - Enable monitoring and alerting

2. **Tier 5: Durability, Scale & Exit**
   - Hero workflow integration tests
   - Performance safeguards
   - Firm offboarding and data exit flows

3. **Future Enhancements**
   - Celery integration for async tasks
   - Client-facing payment method setup
   - Automated dispute evidence submission
   - Advanced analytics and reporting

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for:
- Development workflow
- Code quality standards
- Testing requirements
- Documentation practices

---

**Questions or Issues?**

- Review the detailed documentation linked above
- Check the troubleshooting section
- Refer to the design documents for architecture details
- Run tests to verify functionality
