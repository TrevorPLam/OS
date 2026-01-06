# AGENTS.md — Webhooks Module (Webhook Platform)

Last Updated: 2026-01-06
Applies To: `src/modules/webhooks/`

## Purpose

General webhook platform for external integrations. Allows external systems to subscribe to events.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | WebhookEndpoint, WebhookDelivery (~430 LOC) |
| `queue.py` | Webhook delivery queue |
| `jobs.py` | Delivery job definitions |

## Domain Model

```
WebhookEndpoint (registered receiver)
    └── WebhookDelivery (individual delivery attempt)
```

## Key Models

### WebhookEndpoint

Registered webhook receiver:

```python
class WebhookEndpoint(models.Model):
    firm: FK[Firm]
    
    name: str
    url: str                          # HTTPS required
    description: str
    
    status: str                       # active, paused, disabled
    
    # Event subscriptions
    subscribed_events: JSONField      # ["client.created", "project.updated"]
    
    # Authentication
    secret: str                       # Auto-generated HMAC secret
    
    # Headers
    custom_headers: JSONField         # Additional headers to send
    
    # Tracking
    last_success_at: DateTime
    last_failure_at: DateTime
    consecutive_failures: int
    
    # Auto-disable
    auto_disable_after_failures: int  # Default: 10
```

### WebhookDelivery

Individual delivery attempt:

```python
class WebhookDelivery(models.Model):
    endpoint: FK[WebhookEndpoint]
    
    event_type: str                   # e.g., "client.created"
    event_id: str                     # Unique event identifier
    
    # Payload
    payload: JSONField
    
    # Delivery status
    status: str                       # pending, delivered, failed, cancelled
    
    # Attempts
    attempt_count: int
    max_attempts: int                 # Default: 5
    
    # Response tracking
    response_status_code: int
    response_body: str                # Truncated
    response_time_ms: int
    
    # Timing
    scheduled_at: DateTime
    delivered_at: DateTime
```

## Event Types

Standard event format: `{entity}.{action}`

| Event | Description |
|-------|-------------|
| `client.created` | New client created |
| `client.updated` | Client modified |
| `project.created` | New project |
| `project.status_changed` | Project status update |
| `invoice.sent` | Invoice sent to client |
| `invoice.paid` | Invoice payment received |
| `appointment.booked` | Calendar booking |
| `appointment.cancelled` | Booking cancelled |
| `deal.stage_changed` | Deal moved in pipeline |
| `deal.won` | Deal marked won |
| `deal.lost` | Deal marked lost |

## Payload Format

```json
{
  "event_id": "evt_abc123",
  "event_type": "client.created",
  "timestamp": "2026-01-06T10:30:00Z",
  "firm_id": 123,
  "data": {
    "id": 456,
    "name": "Acme Corp",
    "created_at": "2026-01-06T10:30:00Z"
    // ... entity-specific fields
  }
}
```

## HMAC Signature

All deliveries include signature header:

```
X-Webhook-Signature: sha256=abc123...
```

Verification:

```python
import hmac
import hashlib

def verify_signature(payload_body, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload_body.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Delivery Flow

```
1. Event occurs in system
2. Find subscribed endpoints
3. For each endpoint:
   a. Create WebhookDelivery (status=pending)
   b. Queue delivery job
4. Worker picks up delivery:
   a. Build payload
   b. Sign with HMAC
   c. POST to endpoint URL
5. On success (2xx):
   - status=delivered
   - Reset consecutive_failures
6. On failure:
   - attempt_count++
   - If attempts < max: retry with backoff
   - If attempts >= max: status=failed
   - consecutive_failures++
   - If consecutive_failures >= threshold: disable endpoint
```

## Retry Policy

```python
# Retry delays (exponential backoff)
# Attempt 1: immediate
# Attempt 2: 1 minute
# Attempt 3: 5 minutes
# Attempt 4: 30 minutes
# Attempt 5: 2 hours
```

## Auto-Disable

Endpoints auto-disabled after consecutive failures:

```python
# After 10 consecutive failures
endpoint.status = "disabled"
# Admin notified
# Manual re-enable required
```

## Dependencies

- **Depends on**: `firm/`, `jobs/`
- **Used by**: All modules that emit events
- **Related**: `api/webhooks/` (API layer)

## URLs

Staff endpoints (`/api/v1/webhooks/`):

```
GET/POST   /endpoints/
GET/PUT    /endpoints/{id}/
DELETE     /endpoints/{id}/
POST       /endpoints/{id}/test/      # Send test event
POST       /endpoints/{id}/enable/
POST       /endpoints/{id}/disable/

GET        /endpoints/{id}/deliveries/
GET        /deliveries/{id}/
POST       /deliveries/{id}/retry/
```

## Emitting Events

```python
from modules.webhooks.queue import emit_event

# In your view/signal handler
emit_event(
    firm=firm,
    event_type="client.created",
    data={
        "id": client.id,
        "name": client.name,
        # ... relevant fields
    }
)
```
