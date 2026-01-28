"""
Marketing campaign queue helpers.

Queues campaign execution send jobs and prepares per-recipient status records.
"""

from __future__ import annotations

from typing import Iterable, List

from modules.clients.models import Contact
from modules.jobs.models import JobQueue
from modules.marketing.models import CampaignExecution, CampaignRecipientStatus


def _resolve_contacts(execution: CampaignExecution) -> List[Contact]:
    firm = execution.campaign.firm
    queryset = Contact.objects.filter(
        client__firm=firm,
        status=Contact.STATUS_ACTIVE,
        opt_out_marketing=False,
    )

    if execution.segment and execution.segment.criteria:
        contact_ids = execution.segment.criteria.get("contact_ids")
        if contact_ids:
            queryset = queryset.filter(id__in=contact_ids)

    return list(queryset)


def _ensure_recipient_records(
    execution: CampaignExecution,
    contacts: Iterable[Contact],
) -> List[int]:
    records = [
        CampaignRecipientStatus(
            execution=execution,
            contact=contact,
            email=contact.email,
            status="pending",
        )
        for contact in contacts
        if contact.email
    ]

    if records:
        CampaignRecipientStatus.objects.bulk_create(records, ignore_conflicts=True)

    return [record.contact_id for record in records if record.contact_id]


def queue_campaign_execution(
    execution: CampaignExecution,
    correlation_id: str,
) -> JobQueue:
    contacts = _resolve_contacts(execution)
    recipient_ids = _ensure_recipient_records(execution, contacts)

    idempotency_key = f"email_campaign_{execution.id}_{execution.started_at.isoformat()}"
    payload = {
        "tenant_id": execution.campaign.firm_id,
        "correlation_id": str(correlation_id),
        "idempotency_key": idempotency_key,
        "execution_id": execution.id,
        "campaign_id": execution.campaign_id,
        "template_id": execution.email_template_id,
        "recipient_ids": recipient_ids,
    }

    return JobQueue.objects.create(
        firm=execution.campaign.firm,
        category="notifications",
        job_type="email_campaign_send",
        payload_version="1.0",
        payload=payload,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id,
        priority=1,
    )
