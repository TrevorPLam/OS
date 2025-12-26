"""Background job handlers with explicit tenant guards."""
from django.utils import timezone

from job_guards import require_firm_for_job, require_client_for_job
from modules.firm.utils import expire_overdue_break_glass_sessions
from modules.firm.export import export_firm_data, resolve_requested_by
from modules.firm.models import FirmOffboardingRecord


def expire_overdue_break_glass_sessions_job(*, firm_id=None):
    """Expire overdue break-glass sessions for a firm with firm guard."""
    firm = require_firm_for_job(firm_id)
    return expire_overdue_break_glass_sessions(firm)


def noop_client_job(*, firm_id=None, client_id=None):
    """Example job illustrating firm+client guard enforcement."""
    firm, client = require_client_for_job(firm_id, client_id)
    return f"validated firm={firm.id} client={client.id}"


def firm_offboarding_export_job(*, firm_id=None, requested_by_id=None, retention_days=None, purge_grace_days=None):
    """Generate firm export payload and record export metadata."""
    firm = require_firm_for_job(firm_id)
    requested_by = resolve_requested_by(requested_by_id)
    payload = export_firm_data(
        firm=firm,
        requested_by=requested_by,
        retention_days=retention_days,
        purge_grace_days=purge_grace_days,
    )

    record = FirmOffboardingRecord.objects.create(
        firm=firm,
        requested_by=requested_by,
        retention_days=payload['retention']['retention_days'],
        purge_grace_days=payload['retention']['purge_grace_days'],
        export_completed_at=payload['generated_at'],
        retention_expires_at=payload['retention']['retention_expires_at'],
        purge_scheduled_at=payload['retention']['purge_scheduled_at'],
        export_manifest=payload['manifest'],
        integrity_report=payload['integrity'],
        export_checksum=payload['checksum'],
        status=(
            FirmOffboardingRecord.STATUS_EXPORTED
            if payload['integrity']['status'] == 'ok'
            else FirmOffboardingRecord.STATUS_FAILED
        ),
    )
    return {"record_id": record.id, "payload": payload}


def firm_offboarding_purge_job(*, firm_id=None, record_id=None):
    """Finalize purge sequencing after retention window expires."""
    firm = require_firm_for_job(firm_id)
    record = FirmOffboardingRecord.objects.filter(firm=firm)
    if record_id:
        record = record.filter(id=record_id)
    record = record.first()

    if not record:
        raise ValueError("No offboarding record available for purge.")

    if record.retention_expires_at and timezone.now() < record.retention_expires_at:
        raise ValueError("Retention window has not expired.")

    record.status = FirmOffboardingRecord.STATUS_PURGED
    record.purge_completed_at = timezone.now()
    record.save()

    firm.status = 'canceled'
    firm.save(update_fields=['status'])
    return {"record_id": record.id, "status": record.status}
