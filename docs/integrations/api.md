# API Integrations

API-based integrations and examples.

## Integration Overview

UBOS provides RESTful APIs for integration with external systems.

## Integration Types

### Accounting Integrations
- **QuickBooks** - Sync invoices, payments
- **Xero** - Sync financial data

### CRM Integrations
- **Salesforce** - Sync client data
- **HubSpot** - Sync contacts and deals

### Communication Integrations
- **Email Providers** - Email integration
- **SMS Providers** - SMS messaging
- **Calendar Systems** - Calendar sync

## Integration Examples

### QuickBooks Integration
```python
# Sync invoice to QuickBooks
from modules.accounting_integrations.quickbooks_service import QuickBooksService

service = QuickBooksService()
service.sync_invoice(invoice_id)
```

### Webhook Integration
```python
# Receive webhook from external system
@webhook_handler('external_system')
def handle_webhook(request):
    data = request.data
    # Process webhook data
```

## Integration Setup

1. **Obtain Credentials** - Get API keys/tokens
2. **Configure Integration** - Set up in admin panel
3. **Test Connection** - Verify connectivity
4. **Enable Sync** - Start data synchronization
5. **Monitor** - Monitor integration health

## Related Documentation

- [Integrations](README.md) - Integration overview
- [API Reference](../reference/api/README.md) - Complete API docs
- [Webhooks](webhooks.md) - Webhook documentation
