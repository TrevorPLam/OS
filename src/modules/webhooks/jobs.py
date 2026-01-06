"""
Webhook delivery background job handlers.
"""

from __future__ import annotations

import json
import logging

import requests
from django.utils import timezone

from modules.firm.utils import firm_db_session
from modules.jobs.models import JobQueue
from modules.webhooks.models import WebhookDelivery

logger = logging.getLogger(__name__)


def _serialize_payload(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _update_endpoint_stats(endpoint, success: bool) -> None:
    endpoint.total_deliveries += 1
    endpoint.last_delivery_at = timezone.now()
    if success:
        endpoint.successful_deliveries += 1
        endpoint.last_success_at = timezone.now()
    else:
        endpoint.failed_deliveries += 1
        endpoint.last_failure_at = timezone.now()
    endpoint.save(
        update_fields=[
            "total_deliveries",
            "successful_deliveries",
            "failed_deliveries",
            "last_delivery_at",
            "last_success_at",
            "last_failure_at",
        ]
    )


def process_webhook_delivery_job(job: JobQueue) -> None:
    """
    Process a queued webhook delivery job.

    This function is designed to be invoked by a worker process.
    """
    with firm_db_session(job.firm_id):
        payload = job.payload or {}
        delivery_id = payload.get("delivery_id")

        if not delivery_id:
            job.mark_failed("non_retryable", "Missing delivery_id in payload", should_retry=False)
            return

        delivery = (
            WebhookDelivery.objects.select_related("webhook_endpoint")
            .filter(id=delivery_id)
            .first()
        )
        if not delivery:
            job.mark_failed("non_retryable", "Webhook delivery not found", should_retry=False)
            return

        endpoint = delivery.webhook_endpoint
        if endpoint.status != "active":
            delivery.status = "failed"
            delivery.error_message = "Webhook endpoint is not active"
            delivery.completed_at = timezone.now()
            delivery.save(update_fields=["status", "error_message", "completed_at"])
            job.mark_failed("non_retryable", delivery.error_message, should_retry=False)
            return

        delivery.status = "sending"
        delivery.attempts += 1
        if not delivery.first_attempt_at:
            delivery.first_attempt_at = timezone.now()
        delivery.last_attempt_at = timezone.now()
        delivery.save(update_fields=["status", "attempts", "first_attempt_at", "last_attempt_at"])

        payload_body = _serialize_payload(delivery.payload)
        signature = endpoint.generate_signature(payload_body)
        delivery.signature = signature
        delivery.save(update_fields=["signature"])

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Event-Type": delivery.event_type,
            "X-Webhook-Event-Id": delivery.event_id,
        }

        try:
            response = requests.post(
                endpoint.url,
                data=payload_body,
                headers=headers,
                timeout=endpoint.timeout_seconds,
            )
            delivery.http_status_code = response.status_code
            delivery.response_headers = dict(response.headers)
            delivery.response_body = response.text[:5000]

            if 200 <= response.status_code < 300:
                delivery.status = "success"
                delivery.completed_at = timezone.now()
                delivery.error_message = ""
                delivery.next_retry_at = None
                delivery.save(
                    update_fields=[
                        "http_status_code",
                        "response_headers",
                        "response_body",
                        "status",
                        "completed_at",
                        "error_message",
                        "next_retry_at",
                    ]
                )
                _update_endpoint_stats(endpoint, success=True)
                job.mark_completed(result={"delivery_id": delivery.id, "status": "success"})
                return

            error_message = f"Webhook responded with status {response.status_code}"
            delivery.error_message = error_message
        except requests.RequestException as exc:
            delivery.http_status_code = None
            delivery.response_headers = {}
            delivery.response_body = ""
            delivery.error_message = str(exc)

        delivery.status = "retrying" if delivery.should_retry() else "failed"
        if delivery.status == "retrying":
            delivery.next_retry_at = delivery.calculate_next_retry_time()
        else:
            delivery.completed_at = timezone.now()
        delivery.save(
            update_fields=[
                "http_status_code",
                "response_headers",
                "response_body",
                "error_message",
                "status",
                "next_retry_at",
                "completed_at",
            ]
        )
        _update_endpoint_stats(endpoint, success=False)

        job.mark_failed(
            "retryable" if delivery.status == "retrying" else "non_retryable",
            delivery.error_message or "Webhook delivery failed",
            should_retry=delivery.status == "retrying",
        )

        if delivery.status == "retrying" and delivery.next_retry_at:
            job.scheduled_at = delivery.next_retry_at
            job.save(update_fields=["scheduled_at"])

        logger.warning(
            "Webhook delivery failed",
            extra={"delivery_id": delivery.id, "status": delivery.status},
        )
