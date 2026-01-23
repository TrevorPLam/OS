# Webhooks

Webhook configuration, events, and handling.

## Webhook Overview

UBOS supports webhooks for real-time event notifications to external systems.

## Webhook Events

### Client Events
- `client.created` - New client created
- `client.updated` - Client updated
- `client.deleted` - Client deleted

### Project Events
- `project.created` - New project created
- `project.updated` - Project updated
- `project.completed` - Project completed

### Invoice Events
- `invoice.created` - Invoice created
- `invoice.paid` - Invoice paid
- `invoice.overdue` - Invoice overdue

## Webhook Configuration

### Setting Up Webhooks
1. Configure webhook URL in admin panel
2. Set authentication (API key, signature)
3. Select events to subscribe to
4. Test webhook delivery

### Webhook Payload
```json
{
  "event": "client.created",
  "timestamp": "2026-01-23T12:00:00Z",
  "data": {
    "id": 123,
    "name": "Client Name",
    "email": "client@example.com"
  }
}
```

## Security

- Webhook signatures for verification
- HTTPS required
- Rate limiting
- Retry logic

## Related Documentation

- [Integrations](README.md) - Integration overview
- [API Guide](../guides/api/README.md) - API documentation
- [Security](../security/README.md) - Security practices
