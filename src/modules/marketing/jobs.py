"""
Marketing background job handlers.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from modules.core.notifications import EmailNotification
from modules.firm.utils import firm_db_session
from modules.jobs.models import JobQueue
from modules.marketing.models import CampaignExecution, CampaignRecipientStatus

logger = logging.getLogger(__name__)


def process_email_campaign_job(job: JobQueue) -> None:
    """
    Process a queued email campaign send job.

    This function is designed to be invoked by a worker process.
    """
    with firm_db_session(job.firm_id):
        payload = job.payload or {}
        execution_id = payload.get("execution_id")

        if not execution_id:
            job.mark_failed("non_retryable", "Missing execution_id in payload", should_retry=False)
            return

        execution = (
            CampaignExecution.objects.select_related("campaign", "email_template")
            .filter(id=execution_id)
            .first()
        )
        if not execution:
            job.mark_failed("non_retryable", "Campaign execution not found", should_retry=False)
            return

        template = execution.email_template
        if not template:
            execution.status = "failed"
            execution.error_message = "Missing email template for campaign execution."
            execution.completed_at = timezone.now()
            execution.save(update_fields=["status", "error_message", "completed_at", "updated_at"])
            job.mark_failed("non_retryable", execution.error_message, should_retry=False)
            return

        recipient_queryset = CampaignRecipientStatus.objects.filter(execution=execution, status="pending")
        recipient_ids = payload.get("recipient_ids")
        if recipient_ids:
            recipient_queryset = recipient_queryset.filter(contact_id__in=recipient_ids)

        sent_count = 0
        failed_count = 0

        for recipient in recipient_queryset.iterator():
            success = EmailNotification.send(
                to=recipient.email,
                subject=template.subject_line,
                html_content=template.html_content,
                text_content=template.plain_text_content or None,
            )
            if success:
                recipient.mark_sent()
                sent_count += 1
            else:
                recipient.mark_failed("Email send failed")
                failed_count += 1

        with transaction.atomic():
            execution.emails_sent += sent_count
            execution.emails_failed += failed_count
            execution.completed_at = timezone.now()
            execution.status = "sent" if execution.emails_sent > 0 else "failed"
            execution.save(
                update_fields=[
                    "emails_sent",
                    "emails_failed",
                    "completed_at",
                    "status",
                    "updated_at",
                ]
            )
            execution.calculate_rates()

        logger.info(
            "Processed email campaign job",
            extra={
                "execution_id": execution.id,
                "sent": sent_count,
                "failed": failed_count,
            },
        )

        job.mark_completed(
            result={
                "execution_id": execution.id,
                "sent": sent_count,
                "failed": failed_count,
            }
        )
