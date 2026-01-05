"""
Webhook delivery queue integration.

Queues webhook delivery attempts via JobQueue for async processing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from modules.jobs.models import JobQueue
from modules.webhooks.models import WebhookDelivery


def queue_webhook_delivery(
    delivery: WebhookDelivery,
    correlation_id: str,
    scheduled_at: Optional[datetime] = None,
) -> JobQueue:
    """
    Queue a webhook delivery attempt in the JobQueue.

    Args:
        delivery: WebhookDelivery instance to send
        correlation_id: Correlation ID for observability
        scheduled_at: Optional schedule time (for retries)
    """
    idempotency_key = f"webhook_delivery_{delivery.id}_attempt_{delivery.attempts + 1}"
    payload = {
        "tenant_id": delivery.webhook_endpoint.firm_id,
        "correlation_id": str(correlation_id),
        "idempotency_key": idempotency_key,
        "delivery_id": delivery.id,
        "webhook_endpoint_id": delivery.webhook_endpoint_id,
        "event_type": delivery.event_type,
        "recipient_id": delivery.webhook_endpoint_id,
    }

    return JobQueue.objects.create(
        firm=delivery.webhook_endpoint.firm,
        category="notifications",
        job_type="webhook_delivery",
        payload_version="1.0",
        payload=payload,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        scheduled_at=scheduled_at,
        priority=2,
    )
