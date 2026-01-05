# General Webhook Platform

## Overview

The General Webhook Platform (Task 3.7) provides a comprehensive system for sending real-time event notifications to external systems via HTTP POST requests. It enables firms to integrate ConsultantPro with third-party applications and build custom integrations.

## Key Features

- **Event Subscriptions**: Subscribe to specific event types or use wildcard patterns
- **HMAC Signature Verification**: Secure webhook payloads with HMAC-SHA256 signatures
- **Automatic Retries**: Exponential backoff retry logic for failed deliveries
- **Delivery Tracking**: Complete audit trail of all webhook deliveries
- **Status Monitoring**: Track success rates, response times, and failure patterns
- **Rate Limiting**: Optional rate limiting per webhook endpoint
- **Pause/Resume**: Temporarily disable webhooks without deleting configuration
- **Test Events**: Send test events to verify webhook configuration

## Models

### WebhookEndpoint

Represents a registered webhook receiver that external systems use to receive event notifications.

**Key Fields:**
- `firm`: Firm this webhook belongs to (TIER 0 compliance)
- `name`: Descriptive name for the webhook
- `url`: Target URL to POST events to (up to 2048 characters)
- `description`: Optional description of what this webhook is for
- `status`: Active, paused, or disabled
- `subscribed_events`: List of event types to receive (supports wildcards)
- `secret`: Auto-generated secret key for HMAC signature verification
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_delay_seconds`: Initial retry delay (default: 60s, exponential backoff)
- `timeout_seconds`: HTTP request timeout (default: 30s)
- `rate_limit_per_minute`: Optional rate limiting (null = no limit)

**Statistics Fields:**
- `total_deliveries`: Total delivery attempts
- `successful_deliveries`: Successful deliveries (HTTP 2xx)
- `failed_deliveries`: Failed deliveries
- `last_delivery_at`: Timestamp of last delivery
- `last_success_at`: Timestamp of last successful delivery
- `last_failure_at`: Timestamp of last failed delivery

**Computed Properties:**
- `success_rate`: Percentage of successful deliveries

**Methods:**
- `generate_signature(payload)`: Generate HMAC-SHA256 signature for payload
- `verify_signature(payload, signature)`: Verify HMAC signature
- `is_subscribed_to(event_type)`: Check if subscribed to event type

**TIER 0 Compliance:**
- Belongs to exactly one Firm
- Uses FirmScopedManager for automatic query scoping
- Portal users cannot access (DenyPortalAccess)

### WebhookDelivery

Tracks individual webhook event deliveries for monitoring and debugging.

**Key Fields:**
- `webhook_endpoint`: Webhook endpoint this delivery is for
- `event_type`: Event type (e.g., 'client.created', 'project.updated')
- `event_id`: Unique identifier for this event
- `payload`: Event payload data (JSONField)
- `status`: Pending, sending, success, failed, or retrying
- `attempts`: Number of delivery attempts made
- `http_status_code`: HTTP response status code
- `response_headers`: HTTP response headers (JSONField)
- `response_body`: HTTP response body
- `error_message`: Error message if delivery failed
- `signature`: HMAC signature sent in request headers

**Timing Fields:**
- `created_at`: When delivery was created
- `first_attempt_at`: Timestamp of first attempt
- `last_attempt_at`: Timestamp of most recent attempt
- `next_retry_at`: Timestamp of next retry (if retrying)
- `completed_at`: When delivery completed (success or final failure)

**Computed Properties:**
- `is_success`: True if HTTP 2xx response
- `duration_seconds`: Time from first attempt to completion

**Methods:**
- `calculate_next_retry_time()`: Calculate next retry time with exponential backoff
- `should_retry()`: Check if delivery should be retried

**TIER 0 Compliance:**
- Inherits firm from webhook_endpoint
- Automatically scoped through webhook endpoint relationship

## Event Types

Event types follow a hierarchical naming convention: `resource.action`

**Common Event Types:**
- `client.created` - New client created
- `client.updated` - Client information updated
- `client.deleted` - Client deleted
- `project.created` - New project created
- `project.updated` - Project updated
- `project.completed` - Project marked as completed
- `invoice.created` - New invoice generated
- `invoice.paid` - Invoice marked as paid
- `task.created` - New task created
- `task.completed` - Task marked as completed
- `document.uploaded` - Document uploaded
- `appointment.scheduled` - Appointment scheduled
- `appointment.cancelled` - Appointment cancelled

**Wildcard Subscriptions:**
- Subscribe to `client.*` to receive all client events
- Subscribe to `project.*` to receive all project events
- Wildcards only supported at the end of event type

## Webhook Delivery Process

### 1. Event Triggered

When an event occurs in the system (e.g., client created), the application:
1. Identifies all active webhook endpoints subscribed to that event type
2. Creates a WebhookDelivery record for each endpoint
3. Queues deliveries for processing via JobQueue (job_type: `webhook_delivery`)

### 2. Delivery Attempt

For each delivery:
1. Generate HMAC-SHA256 signature using endpoint's secret key
2. Send HTTP POST request to endpoint URL with:
   - Headers:
     - `Content-Type: application/json`
     - `X-Webhook-Signature: <signature>`
     - `X-Event-Type: <event_type>`
     - `X-Event-ID: <event_id>`
     - `X-Delivery-ID: <delivery_id>`
   - Body: JSON payload
3. Record response status, headers, and body
4. Update delivery status based on response:
   - HTTP 2xx: Success
   - HTTP 4xx/5xx or timeout: Failed (retry if retries remaining)

### 3. Retry Logic

If delivery fails and retries remain:
1. Calculate next retry time using exponential backoff:
   - Retry 1: `retry_delay_seconds * (2^0)` = 60s
   - Retry 2: `retry_delay_seconds * (2^1)` = 120s
   - Retry 3: `retry_delay_seconds * (2^2)` = 240s
2. Set status to "retrying"
3. Set `next_retry_at` timestamp
4. Queue a retry job in JobQueue with `scheduled_at = next_retry_at`
5. Background worker processes retries when `scheduled_at` is reached

### 4. Final Status

After all retries exhausted or on success:
1. Set `completed_at` timestamp
2. Set final status (success or failed)
3. Update endpoint statistics:
   - Increment `total_deliveries`
   - Increment `successful_deliveries` or `failed_deliveries`
   - Update `last_delivery_at`, `last_success_at`, or `last_failure_at`

## API Endpoints

### WebhookEndpoint Management

**List Endpoints:**
```
GET /api/v1/webhooks/endpoints/
```

Query parameters:
- `status`: Filter by status (active, paused, disabled)
- `search`: Search by name, URL, or description
- `ordering`: Sort by name, created_at, last_delivery_at, total_deliveries

**Create Endpoint:**
```
POST /api/v1/webhooks/endpoints/
{
  "name": "My Integration",
  "url": "https://example.com/webhooks",
  "description": "Integration with external CRM",
  "subscribed_events": ["client.created", "client.updated"],
  "max_retries": 3,
  "retry_delay_seconds": 60,
  "timeout_seconds": 30,
  "rate_limit_per_minute": 60,
  "metadata": {"integration_id": "ext-123"}
}
```

**Get Endpoint:**
```
GET /api/v1/webhooks/endpoints/{id}/
```

**Update Endpoint:**
```
PUT /api/v1/webhooks/endpoints/{id}/
PATCH /api/v1/webhooks/endpoints/{id}/
```

**Delete Endpoint:**
```
DELETE /api/v1/webhooks/endpoints/{id}/
```

**Regenerate Secret:**
```
POST /api/v1/webhooks/endpoints/{id}/regenerate_secret/
```

Generates a new secret key. The old secret is immediately invalidated.

**Pause Endpoint:**
```
POST /api/v1/webhooks/endpoints/{id}/pause/
```

Pauses the webhook. No events will be sent while paused.

**Activate Endpoint:**
```
POST /api/v1/webhooks/endpoints/{id}/activate/
```

Activates a paused webhook.

**Test Endpoint:**
```
POST /api/v1/webhooks/endpoints/{id}/test/
{
  "event_type": "test.event",
  "payload": {"message": "Test event", "timestamp": "2026-01-01T10:00:00Z"}
}
```

Sends a test event to verify webhook configuration.

**Get Statistics:**
```
GET /api/v1/webhooks/endpoints/{id}/statistics/
```

Returns detailed statistics including:
- Success rate
- Total/successful/failed deliveries
- Average response time
- Recent status breakdown
- Last delivery timestamps

### WebhookDelivery Monitoring

**List Deliveries:**
```
GET /api/v1/webhooks/deliveries/
```

Query parameters:
- `webhook_endpoint`: Filter by webhook endpoint ID
- `event_type`: Filter by event type
- `status`: Filter by status
- `http_status_code`: Filter by HTTP status code
- `ordering`: Sort by created_at, completed_at, attempts

**Get Delivery:**
```
GET /api/v1/webhooks/deliveries/{id}/
```

**Retry Failed Delivery:**
```
POST /api/v1/webhooks/deliveries/{id}/retry/
```

Manually retry a failed delivery (if retries remain).

**Get Failed Deliveries:**
```
GET /api/v1/webhooks/deliveries/failed/
```

Query parameters:
- `webhook_endpoint`: Filter by endpoint ID
- `event_type`: Filter by event type

**Get Pending Retries:**
```
GET /api/v1/webhooks/deliveries/pending_retries/
```

Returns deliveries ready for retry (status=retrying, next_retry_at <= now).

## Webhook Signature Verification

Webhooks include an HMAC-SHA256 signature in the `X-Webhook-Signature` header. Recipients should verify this signature to ensure the webhook came from ConsultantPro and hasn't been tampered with.

### Signature Format

The signature is a hex-encoded HMAC-SHA256 hash of the request body using the endpoint's secret key.

### Verification Example (Python)

```python
import hmac
import hashlib

def verify_webhook(secret, payload, signature):
    """
    Verify webhook signature.
    
    Args:
        secret: Webhook endpoint secret key
        payload: Raw request body (string)
        signature: Signature from X-Webhook-Signature header
        
    Returns:
        True if signature is valid
    """
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# In your webhook handler
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.get_data(as_text=True)
    
    if not verify_webhook(WEBHOOK_SECRET, payload, signature):
        return 'Invalid signature', 401
    
    # Process webhook
    data = request.get_json()
    event_type = request.headers.get('X-Event-Type')
    # ... handle event
    
    return 'OK', 200
```

### Verification Example (Node.js)

```javascript
const crypto = require('crypto');

function verifyWebhook(secret, payload, signature) {
    const expectedSignature = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');
    
    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expectedSignature)
    );
}

// In your webhook handler
app.post('/webhook', (req, res) => {
    const signature = req.headers['x-webhook-signature'];
    const payload = JSON.stringify(req.body);
    
    if (!verifyWebhook(WEBHOOK_SECRET, payload, signature)) {
        return res.status(401).send('Invalid signature');
    }
    
    // Process webhook
    const eventType = req.headers['x-event-type'];
    // ... handle event
    
    res.send('OK');
});
```

## Webhook Payload Format

All webhooks send a JSON payload with the following structure:

```json
{
  "event_id": "evt_123abc",
  "event_type": "client.created",
  "timestamp": "2026-01-01T10:00:00Z",
  "firm_id": 123,
  "data": {
    // Event-specific data
  },
  "metadata": {
    // Optional metadata
  }
}
```

### Example: Client Created Event

```json
{
  "event_id": "evt_123abc",
  "event_type": "client.created",
  "timestamp": "2026-01-01T10:00:00Z",
  "firm_id": 123,
  "data": {
    "id": 456,
    "company_name": "Acme Corp",
    "contact_name": "John Doe",
    "email": "john@acme.com",
    "phone": "+1-555-0123",
    "status": "active",
    "created_at": "2026-01-01T10:00:00Z"
  },
  "metadata": {
    "created_by_user_id": 789,
    "ip_address": "192.0.2.1"
  }
}
```

### Example: Project Completed Event

```json
{
  "event_id": "evt_456def",
  "event_type": "project.completed",
  "timestamp": "2026-01-01T15:30:00Z",
  "firm_id": 123,
  "data": {
    "id": 789,
    "project_code": "PROJ-001",
    "name": "Website Redesign",
    "client_id": 456,
    "start_date": "2025-10-01",
    "end_date": "2026-01-01",
    "actual_completion_date": "2026-01-01",
    "status": "completed"
  },
  "metadata": {
    "completed_by_user_id": 790,
    "duration_days": 92
  }
}
```

## Best Practices

### For Webhook Senders (ConsultantPro)

1. **Idempotency**: Include unique `event_id` to help receivers handle duplicate deliveries
2. **Minimal Payload**: Send only essential data, let receivers fetch details via API if needed
3. **Versioning**: Include version information in payload if webhook format changes
4. **Rate Limiting**: Respect rate limits to avoid overwhelming receivers
5. **Monitoring**: Track success rates and investigate patterns in failures

### For Webhook Receivers (External Systems)

1. **Verify Signatures**: Always verify HMAC signature before processing
2. **Respond Quickly**: Return HTTP 2xx within timeout period (default 30s)
3. **Process Asynchronously**: Queue webhook for background processing, don't block response
4. **Idempotency**: Use `event_id` to detect and skip duplicate deliveries
5. **Error Handling**: Return appropriate HTTP status codes:
   - `200 OK`: Successfully received and will process
   - `400 Bad Request`: Invalid payload format
   - `401 Unauthorized`: Invalid signature
   - `500 Internal Server Error`: Processing error (will retry)
6. **Testing**: Use test events to verify integration before going live
7. **Logging**: Log all webhook receipts for debugging and audit trail

## Security Considerations

1. **HTTPS Only**: Webhook URLs must use HTTPS (validated by `validate_safe_url`)
2. **Secret Rotation**: Regenerate secrets periodically or if compromised
3. **Signature Verification**: Always verify signatures on receiver side
4. **Timeout Protection**: Requests timeout after configured seconds (default 30s)
5. **Rate Limiting**: Optional rate limiting prevents abuse
6. **Firm Isolation**: TIER 0 compliance ensures webhooks cannot access other firms' data
7. **Access Control**: Only authenticated firm staff can configure webhooks (portal users denied)

## Monitoring & Troubleshooting

### Check Webhook Status

```bash
GET /api/v1/webhooks/endpoints/{id}/statistics/
```

Look for:
- Low success rate (< 95%): Investigate receiver issues
- High average response time: Receiver may be overloaded
- Recent failures: Check error messages in failed deliveries

### View Failed Deliveries

```bash
GET /api/v1/webhooks/deliveries/failed/?webhook_endpoint={id}
```

Common failure reasons:
- **Connection Timeout**: Receiver not responding within timeout
- **HTTP 4xx**: Receiver rejecting payload (check signature, format)
- **HTTP 5xx**: Receiver error processing webhook
- **DNS Failure**: Invalid or unreachable URL

### Retry Failed Deliveries

Automatic retries with exponential backoff occur for:
- Connection errors
- Timeouts
- HTTP 5xx errors

Manual retry if needed:
```bash
POST /api/v1/webhooks/deliveries/{id}/retry/
```

### Pause Problematic Webhooks

If a webhook is causing issues:
```bash
POST /api/v1/webhooks/endpoints/{id}/pause/
```

Fix the issue, then reactivate:
```bash
POST /api/v1/webhooks/endpoints/{id}/activate/
```

## Database Schema

### WebhookEndpoint Table

```sql
CREATE TABLE webhooks_endpoint (
    id BIGSERIAL PRIMARY KEY,
    firm_id BIGINT NOT NULL REFERENCES firm_firm(id),
    name VARCHAR(255) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    subscribed_events JSONB DEFAULT '[]',
    secret VARCHAR(255) NOT NULL,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    timeout_seconds INTEGER DEFAULT 30,
    rate_limit_per_minute INTEGER NULL,
    total_deliveries INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    last_delivery_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    last_failure_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_by_id BIGINT REFERENCES auth_user(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX webhook_ep_firm_status_idx ON webhooks_endpoint(firm_id, status);
CREATE INDEX webhook_ep_status_idx ON webhooks_endpoint(status);
```

### WebhookDelivery Table

```sql
CREATE TABLE webhooks_delivery (
    id BIGSERIAL PRIMARY KEY,
    webhook_endpoint_id BIGINT NOT NULL REFERENCES webhooks_endpoint(id),
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    http_status_code INTEGER,
    response_headers JSONB DEFAULT '{}',
    response_body TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_attempt_at TIMESTAMP WITH TIME ZONE,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    signature VARCHAR(255)
);

CREATE INDEX webhook_del_ep_status_idx ON webhooks_delivery(webhook_endpoint_id, status);
CREATE INDEX webhook_del_event_idx ON webhooks_delivery(event_type);
CREATE INDEX webhook_del_retry_idx ON webhooks_delivery(status, next_retry_at);
CREATE INDEX webhook_del_created_idx ON webhooks_delivery(created_at);
```

## Background Worker Implementation

The webhook delivery system requires a background worker to process deliveries asynchronously. This prevents blocking the main application when sending webhooks.

### Worker Responsibilities

1. **Process New Deliveries**:
   - Query for deliveries with status "pending"
   - Attempt to send HTTP POST request
   - Update delivery status and statistics

2. **Process Retries**:
   - Query for deliveries with status "retrying" and `next_retry_at <= now`
   - Attempt to send HTTP POST request
   - Update delivery status, attempt count, and retry time

3. **Update Statistics**:
   - Update webhook endpoint statistics after each delivery
   - Track success/failure rates
   - Monitor performance metrics

### Implementation Options

**Option 1: Celery Worker (Recommended)**
```python
from celery import shared_task
from modules.webhooks.models import WebhookDelivery

@shared_task
def process_webhook_delivery(delivery_id):
    """Process a single webhook delivery."""
    delivery = WebhookDelivery.objects.get(id=delivery_id)
    # Send HTTP request, update status, handle retries
    ...
```

**Option 2: Django Management Command**
```bash
python manage.py process_webhooks --daemon
```

**Option 3: Kubernetes CronJob**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: webhook-processor
spec:
  schedule: "*/1 * * * *"  # Every minute
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: processor
            image: consultantpro:latest
            command: ["python", "manage.py", "process_webhooks"]
```

## Admin Interface

The Django admin provides full management capabilities:

### WebhookEndpointAdmin

**List View:**
- Name, URL, status, subscribed events count, success rate, total deliveries
- Filters: status, created_at, last_delivery_at
- Search: name, URL, description

**Detail View:**
- Webhook configuration
- Event subscriptions
- Authentication (secret - collapsed)
- Delivery settings
- Statistics (collapsed)
- Metadata (collapsed)
- Audit info (collapsed)

**Admin Actions:**
- Regenerate secret keys
- Pause webhooks
- Activate webhooks

### WebhookDeliveryAdmin

**List View:**
- Event type, webhook endpoint, status, attempts, HTTP status, timestamps
- Filters: status, event_type, http_status_code, created_at
- Search: event_type, event_id, webhook endpoint name

**Detail View:**
- Webhook endpoint
- Event details
- Delivery status
- Response data
- Timing information
- Authentication (collapsed)

**Admin Actions:**
- Retry failed deliveries

## Future Enhancements

1. **Webhook Templates**: Pre-configured webhook endpoints for common integrations
2. **Event Filtering**: Advanced filtering beyond simple subscriptions (e.g., only clients from specific region)
3. **Batch Deliveries**: Group multiple events into single webhook delivery
4. **Custom Headers**: Allow custom HTTP headers in webhook requests
5. **Circuit Breaker**: Automatically disable consistently failing webhooks
6. **Delivery Replay**: Replay historical events to webhook endpoint
7. **Webhook Marketplace**: Directory of available integrations and their required event subscriptions
8. **GraphQL Webhooks**: Support GraphQL subscriptions in addition to REST webhooks
9. **Webhook UI Dashboard**: Visual dashboard for monitoring webhook health and performance

## Migration

Database migration: `0001_initial.py`

To apply:
```bash
python manage.py migrate webhooks
```

## Related Documentation

- [Gantt Chart & Timeline](./gantt-chart-timeline.md) - Task 3.6
- [Resource Planning & Allocation](./resource-planning.md) - Task 3.2
- [CRM Module](./crm-module.md) - Task 3.1
- [Complex Tasks Implementation Summary](./complex-tasks-implementation-summary.md)
