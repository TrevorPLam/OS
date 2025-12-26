"""
Billing workflows for package invoicing, autopay, and payment recovery.

Implements Tier 4 architecture from docs/tier4/BILLING_INVARIANTS_AND_ARCHITECTURE.md
and PAYMENT_FAILURE_HANDLING.md.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from modules.clients.models import ClientEngagement
from modules.finance.models import Invoice, PaymentDispute
from modules.finance.services import StripeService
from modules.firm.audit import audit

logger = logging.getLogger(__name__)


def _month_start_for(day: date) -> date:
    return day.replace(day=1)


def _month_end_for(day: date) -> date:
    next_month = (day.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _quarter_start_for(day: date) -> date:
    quarter = (day.month - 1) // 3
    month = quarter * 3 + 1
    return day.replace(month=month, day=1)


def _quarter_end_for(day: date) -> date:
    start = _quarter_start_for(day)
    end_month = start.month + 2
    end_candidate = start.replace(month=end_month)
    return _month_end_for(end_candidate)


def _period_bounds(engagement: ClientEngagement, reference_date: date | None = None):
    reference_date = reference_date or timezone.now().date()
    schedule = (engagement.package_fee_schedule or "monthly").lower()

    if schedule == "quarterly":
        start = _quarter_start_for(reference_date)
        end = _quarter_end_for(reference_date)
    elif schedule in ["annual", "yearly"]:
        start = reference_date.replace(month=1, day=1)
        end = reference_date.replace(month=12, day=31)
    elif schedule in ["one-time", "one_time", "once"]:
        start = engagement.start_date
        end = engagement.end_date
    else:  # default monthly
        start = _month_start_for(reference_date)
        end = _month_end_for(reference_date)

    start = max(start, engagement.start_date)
    end = min(end, engagement.end_date)
    return start, end


def get_package_billing_period(engagement: ClientEngagement, reference_date: date | None = None):
    """Public helper to calculate the billing window for a package engagement."""

    return _period_bounds(engagement, reference_date)


def should_generate_package_invoice(engagement: ClientEngagement, reference_date: date | None = None) -> bool:
    """Determine if a package invoice should be generated for the period."""
    if engagement.status != "current":
        return False

    if engagement.pricing_mode not in ["package", "mixed"]:
        return False

    if not engagement.package_fee:
        return False

    period_start, _ = get_package_billing_period(engagement, reference_date)

    if engagement.end_date < period_start:
        return False

    return not Invoice.objects.filter(engagement=engagement, period_start=period_start, firm=engagement.firm).exists()


def create_package_invoice(
    engagement: ClientEngagement, issue_date: date | None = None, reference_date: date | None = None
) -> Invoice:
    """Create a package-fee invoice for an engagement with duplicate prevention."""
    issue_date = issue_date or timezone.now().date()
    period_start, period_end = get_package_billing_period(engagement, reference_date)

    if engagement.client.firm_id != engagement.firm_id:
        raise ValidationError("Engagement firm must match client firm when generating package invoices.")

    with transaction.atomic():
        invoice, created = Invoice.objects.select_for_update().get_or_create(
            engagement=engagement,
            period_start=period_start,
            defaults={
                "firm": engagement.client.firm,
                "client": engagement.client,
                "status": "sent",
                "subtotal": engagement.package_fee,
                "tax_amount": Decimal("0.00"),
                "total_amount": engagement.package_fee,
                "issue_date": issue_date,
                "due_date": issue_date + timedelta(days=30),
                "line_items": [
                    {
                        "description": f"Package Fee - {engagement.contract.title}",
                        "quantity": 1,
                        "rate": float(engagement.package_fee),
                        "amount": float(engagement.package_fee),
                        "type": "package_fee",
                    }
                ],
                "invoice_number": f"PKG-{engagement.id}-{period_start.isoformat()}",
                "is_auto_generated": True,
                "period_end": period_end,
                "autopay_opt_in": engagement.client.autopay_enabled,
                "autopay_payment_method_id": engagement.client.autopay_payment_method_id,
            },
        )

    if created:
        audit.log_billing_event(
            firm=engagement.firm,
            action="package_invoice_auto_generated",
            actor=None,
            metadata={
                "invoice_id": invoice.id,
                "engagement_id": engagement.id,
                "amount": float(engagement.package_fee),
                "period_start": str(period_start),
                "period_end": str(period_end),
            },
        )

    return invoice


def generate_package_invoices(reference_date: date | None = None, firm=None):
    """Generate package invoices for all active engagements.

    Args:
        reference_date: Optional date used to determine the billing window.
        firm: Optional firm to scope invoice generation (tenant isolation).
    """
    engagements = ClientEngagement.objects.filter(
        status="current", pricing_mode__in=["package", "mixed"], package_fee__isnull=False
    ).select_related("client", "firm")

    if firm:
        engagements = engagements.filter(firm=firm)

    created_invoices = []
    for engagement in engagements:
        if should_generate_package_invoice(engagement, reference_date):
            created_invoices.append(create_package_invoice(engagement, reference_date=reference_date))
    return created_invoices


def execute_autopay_for_invoice(invoice: Invoice):
    """
    Autopay execution that pays invoices on issuance without creating new ones.

    If autopay is enabled for the client and a payment method is present, mark the
    invoice as paid. Failures route through payment failure handling to preserve
    retry metadata.
    """

    if not invoice.client.autopay_enabled:
        return invoice

    if not invoice.client.autopay_payment_method_id:
        return handle_payment_failure(
            invoice,
            failure_reason="Missing autopay payment method",
            failure_code="payment_method_missing",
        )

    invoice.amount_paid = invoice.total_amount
    invoice.status = "paid"
    invoice.paid_date = timezone.now().date()
    invoice.save(update_fields=["amount_paid", "status", "paid_date"])

    audit.log_billing_event(
        firm=invoice.firm,
        action="invoice_autopaid",
        actor=None,
        metadata={
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": float(invoice.total_amount),
        },
    )

    return invoice


def schedule_autopay(invoice: Invoice, reference_time: timezone.datetime | None = None):
    """Mark an invoice for autopay execution based on cadence and due date."""

    if not invoice.client.autopay_enabled:
        invoice.autopay_status = "cancelled"
        invoice.autopay_opt_in = False
        invoice.autopay_next_charge_at = None
        invoice.save(update_fields=["autopay_status", "autopay_opt_in", "autopay_next_charge_at"])
        return invoice

    invoice.autopay_opt_in = True
    invoice.autopay_payment_method_id = invoice.autopay_payment_method_id or invoice.client.autopay_payment_method_id
    invoice.autopay_status = "scheduled"
    reference_time = reference_time or timezone.now()

    if invoice.autopay_cadence == "monthly":
        scheduled_for = invoice.due_date.replace(day=1)
    elif invoice.autopay_cadence == "quarterly":
        scheduled_for = invoice.due_date.replace(month=((invoice.due_date.month - 1) // 3) * 3 + 1, day=1)
    else:
        scheduled_for = invoice.due_date

    invoice.autopay_next_charge_at = timezone.make_aware(
        timezone.datetime.combine(scheduled_for, timezone.datetime.min.time())
    )
    invoice.save(
        update_fields=["autopay_status", "autopay_opt_in", "autopay_payment_method_id", "autopay_next_charge_at"]
    )
    return invoice


def _charge_invoice(invoice: Invoice, payment_service=StripeService):
    """Attempt to charge an invoice using the configured payment method."""

    payment_method_id = invoice.autopay_payment_method_id or invoice.client.autopay_payment_method_id
    if not payment_method_id:
        result = handle_payment_failure(
            invoice,
            failure_reason="Missing autopay payment method",
            failure_code="payment_method_missing",
        )
        invoice.autopay_status = "failed"
        invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
        invoice.save(update_fields=["autopay_status", "autopay_next_charge_at"])
        return result

    invoice.autopay_status = "processing"
    invoice.autopay_last_attempt_at = timezone.now()
    invoice.save(update_fields=["autopay_status", "autopay_last_attempt_at"])

    try:
        intent = payment_service.create_payment_intent(
            amount=invoice.total_amount,
            currency=invoice.currency.lower(),
            customer_id=None,
            metadata={"invoice_id": invoice.id},
            payment_method=payment_method_id,
        )
    except Exception as exc:  # pragma: no cover - safety net
        result = handle_payment_failure(invoice, failure_reason=str(exc), failure_code="processor_error")
        invoice.autopay_status = "failed"
        invoice.autopay_next_charge_at = timezone.now() + timedelta(days=3)
        invoice.save(update_fields=["autopay_status", "autopay_next_charge_at"])
        return result

    invoice.stripe_payment_intent_id = (
        getattr(intent, "id", "") or intent.get("id", "") if hasattr(intent, "get") else ""
    )
    invoice.amount_paid = invoice.total_amount
    invoice.status = "paid"
    invoice.paid_date = timezone.now().date()
    invoice.autopay_status = "succeeded"
    invoice.autopay_next_charge_at = None
    invoice.save(
        update_fields=[
            "stripe_payment_intent_id",
            "amount_paid",
            "status",
            "paid_date",
            "autopay_status",
            "autopay_next_charge_at",
        ]
    )
    return invoice


def process_recurring_invoices(reference_time: timezone.datetime | None = None, payment_service=StripeService):
    """Find invoices marked for autopay and execute charges."""

    now = reference_time or timezone.now()
    due_invoices = Invoice.objects.filter(
        autopay_opt_in=True,
        status__in=["sent", "partial", "overdue"],
    ).select_related("client")

    processed = []
    for invoice in due_invoices:
        if not invoice.client.autopay_enabled:
            invoice.autopay_status = "cancelled"
            invoice.autopay_next_charge_at = None
            invoice.autopay_opt_in = False
            invoice.save(update_fields=["autopay_status", "autopay_next_charge_at", "autopay_opt_in"])
            continue

        if invoice.autopay_next_charge_at and invoice.autopay_next_charge_at > now:
            continue

        try:
            processed.append(_charge_invoice(invoice, payment_service=payment_service))
        except Exception as exc:  # pragma: no cover - guardrail
            handle_payment_failure(invoice, failure_reason=str(exc), failure_code="processor_error")
            invoice.autopay_status = "failed"
            invoice.autopay_next_charge_at = now + timedelta(days=3)
            invoice.save(update_fields=["autopay_status", "autopay_next_charge_at"])

    return processed


def handle_payment_failure(invoice: Invoice, failure_reason: str, failure_code: str | None = None):
    """Record payment failure metadata and schedule retry logic."""
    now = timezone.now()
    invoice.status = "failed"
    invoice.payment_failed_at = now
    invoice.payment_failure_reason = failure_reason
    invoice.payment_failure_code = failure_code or ""
    invoice.payment_retry_count += 1
    invoice.last_payment_retry_at = now
    invoice.save(
        update_fields=[
            "status",
            "payment_failed_at",
            "payment_failure_reason",
            "payment_failure_code",
            "payment_retry_count",
            "last_payment_retry_at",
        ]
    )

    audit.log_billing_event(
        firm=invoice.firm,
        action="payment_failed",
        actor=None,
        metadata={
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": float(invoice.total_amount),
            "failure_reason": failure_reason,
            "failure_code": failure_code,
            "retry_count": invoice.payment_retry_count,
            "stripe_payment_intent_id": invoice.stripe_payment_intent_id,
        },
        severity="WARNING",
    )

    schedule_payment_retry(invoice)
    return invoice


def schedule_payment_retry(invoice: Invoice):
    """Mark retry metadata and hand off to async scheduler (stub)."""
    retry_delays = {
        1: timedelta(days=3),
        2: timedelta(days=7),
        3: timedelta(days=14),
    }

    retry_at = timezone.now() + retry_delays.get(invoice.payment_retry_count, timedelta(days=7))

    audit.log_billing_event(
        firm=invoice.firm,
        action="payment_retry_scheduled",
        metadata={
            "invoice_id": invoice.id,
            "retry_count": invoice.payment_retry_count,
            "retry_at": str(retry_at),
        },
    )

    if invoice.payment_retry_count >= 3:
        invoice.status = "overdue"
        invoice.save(update_fields=["status"])
        audit.log_billing_event(
            firm=invoice.firm,
            action="payment_retry_exhausted",
            metadata={
                "invoice_id": invoice.id,
                "total_retries": invoice.payment_retry_count,
            },
            severity="WARNING",
        )


def handle_dispute_opened(stripe_dispute_data: dict) -> PaymentDispute:
    """Create a dispute record and flag invoice as disputed."""
    invoice = Invoice.objects.get(stripe_invoice_id=stripe_dispute_data["invoice_id"])

    dispute = PaymentDispute.objects.create(
        firm=invoice.firm,
        invoice=invoice,
        status="opened",
        reason=stripe_dispute_data.get("reason", "general"),
        amount=Decimal(str(stripe_dispute_data["amount"])),
        stripe_dispute_id=stripe_dispute_data["id"],
        stripe_charge_id=stripe_dispute_data.get("charge_id", ""),
        opened_at=timezone.now(),
        respond_by=stripe_dispute_data.get("respond_by"),
    )

    invoice.status = "disputed"
    invoice.save(update_fields=["status"])

    audit.log_billing_event(
        firm=invoice.firm,
        action="payment_disputed",
        actor=None,
        metadata={
            "dispute_id": dispute.id,
            "invoice_id": invoice.id,
            "amount": float(dispute.amount),
            "reason": dispute.reason,
            "stripe_dispute_id": dispute.stripe_dispute_id,
        },
        severity="CRITICAL",
    )

    return dispute


def handle_dispute_closed(stripe_dispute_data: dict) -> PaymentDispute:
    """Close dispute and update invoice status accordingly."""
    dispute = PaymentDispute.objects.get(stripe_dispute_id=stripe_dispute_data["id"])

    dispute.status = "closed"
    dispute.resolution = stripe_dispute_data.get("status", "")
    dispute.resolution_reason = stripe_dispute_data.get("reason", "")
    dispute.closed_at = timezone.now()
    dispute.save(update_fields=["status", "resolution", "resolution_reason", "closed_at"])

    if dispute.resolution == "won":
        dispute.invoice.status = "paid"
    else:
        dispute.invoice.status = "charged_back"
        dispute.invoice.amount_paid = max(Decimal("0.00"), dispute.invoice.amount_paid - dispute.amount)

    dispute.invoice.save(update_fields=["status", "amount_paid"])

    audit.log_billing_event(
        firm=dispute.firm,
        action=f"dispute_{dispute.resolution or 'closed'}",
        actor=None,
        metadata={
            "dispute_id": dispute.id,
            "invoice_id": dispute.invoice.id,
            "resolution": dispute.resolution,
            "amount": float(dispute.amount),
        },
        severity="CRITICAL",
    )

    return dispute


def create_milestone_invoice(
    project, milestone_index: int, milestone_data: dict, issue_date: date | None = None
) -> Invoice:
    """
    Create an invoice triggered by a milestone completion (Medium Feature 2.3).

    Args:
        project: The Project instance with the completed milestone
        milestone_index: Index of the milestone in the project.milestones array
        milestone_data: The milestone dictionary containing completion info
        issue_date: Invoice issue date (defaults to today)

    Returns:
        Invoice: The newly created milestone invoice

    Raises:
        ValidationError: If milestone is not completed or invoice already exists
    """

    issue_date = issue_date or timezone.now().date()

    # Validate milestone is completed
    if not milestone_data.get("completed"):
        raise ValidationError(f"Cannot generate invoice for incomplete milestone: {milestone_data.get('name')}")

    # Check for existing milestone invoice (prevent duplicates)
    existing_invoice = Invoice.objects.filter(project=project, milestone_reference=milestone_index).first()

    if existing_invoice:
        raise ValidationError(
            f"Invoice {existing_invoice.invoice_number} already exists for milestone '{milestone_data.get('name')}'"
        )

    # Calculate invoice amount
    milestone_amount = milestone_data.get("invoice_amount")
    if not milestone_amount:
        # If no specific amount, calculate percentage of project budget
        milestone_percentage = milestone_data.get("invoice_percentage", 0)
        if milestone_percentage and project.budget:
            milestone_amount = project.budget * Decimal(str(milestone_percentage / 100))
        else:
            raise ValidationError(
                f"Milestone '{milestone_data.get('name')}' has no invoice_amount or invoice_percentage defined"
            )

    milestone_amount = Decimal(str(milestone_amount))

    # Generate invoice number
    invoice_number = f"M-{project.project_code}-{milestone_index + 1}"

    # Determine payment terms
    payment_terms_days = 30  # Default Net 30
    if project.contract and hasattr(project.contract, "payment_terms"):
        if "net_15" in project.contract.payment_terms.lower():
            payment_terms_days = 15
        elif "net_45" in project.contract.payment_terms.lower():
            payment_terms_days = 45
        elif "net_60" in project.contract.payment_terms.lower():
            payment_terms_days = 60

    due_date = issue_date + timedelta(days=payment_terms_days)

    # Create the invoice
    with transaction.atomic():
        invoice = Invoice.objects.create(
            firm=project.firm,
            client=project.client,
            project=project,
            engagement=getattr(project, "engagement", None),
            invoice_number=invoice_number,
            status="draft",  # Start as draft, can be sent manually or auto-sent
            subtotal=milestone_amount,
            tax_amount=Decimal("0.00"),
            total_amount=milestone_amount,
            currency="USD",
            issue_date=issue_date,
            due_date=due_date,
            payment_terms=f"Net {payment_terms_days}",
            line_items=[
                {
                    "description": f"Milestone: {milestone_data.get('name')}",
                    "detail": milestone_data.get("description", ""),
                    "quantity": 1,
                    "rate": float(milestone_amount),
                    "amount": float(milestone_amount),
                    "type": "milestone",
                }
            ],
            milestone_reference=milestone_index,
            is_auto_generated=True,
        )

    # Log the milestone invoice generation
    audit.log_billing_event(
        firm=project.firm,
        action="milestone_invoice_auto_generated",
        actor=None,
        metadata={
            "invoice_id": invoice.id,
            "project_id": project.id,
            "project_code": project.project_code,
            "milestone_index": milestone_index,
            "milestone_name": milestone_data.get("name"),
            "amount": float(milestone_amount),
        },
    )

    return invoice


def process_milestone_completion(project, milestone_index: int):
    """
    Process a milestone completion and generate invoice if configured.

    This function should be called when a milestone is marked as completed.
    It checks if the milestone has invoice generation enabled and creates
    an invoice accordingly.

    Args:
        project: The Project instance
        milestone_index: Index of the completed milestone

    Returns:
        Invoice or None: The created invoice, or None if no invoice was generated
    """
    if not project.milestones or milestone_index >= len(project.milestones):
        return None

    milestone = project.milestones[milestone_index]

    # Check if milestone should trigger invoice
    if not milestone.get("triggers_invoice", False):
        return None

    # Check if milestone is completed
    if not milestone.get("completed"):
        return None

    try:
        invoice = create_milestone_invoice(project, milestone_index, milestone)
        return invoice
    except ValidationError as e:
        # Log error but don't fail the milestone completion
        logger.warning(f"Failed to generate milestone invoice for {project.project_code}: {str(e)}")
        return None


def should_send_dunning_reminder(invoice, reference_date: date | None = None) -> bool:
    """
    Determine if a dunning reminder should be sent for an overdue invoice (Medium Feature 2.6).

    Args:
        invoice: Invoice instance
        reference_date: Date to check against (defaults to today)

    Returns:
        bool: True if dunning reminder should be sent
    """
    reference_date = reference_date or timezone.now().date()

    # Don't send reminders for paid or cancelled invoices
    if invoice.status in ["paid", "cancelled", "refunded"]:
        return False

    # Don't send if dunning is paused
    if invoice.dunning_paused:
        return False

    # Must be past due date
    if invoice.due_date >= reference_date:
        return False

    # Check dunning level and timing
    days_overdue = (reference_date - invoice.due_date).days

    if invoice.dunning_level == 0:
        # First reminder: 7 days after due date
        return days_overdue >= 7
    elif invoice.dunning_level == 1:
        # Second reminder: 14 days after first (21 days total)
        if not invoice.last_dunning_sent_at:
            return False
        days_since_last = (reference_date - invoice.last_dunning_sent_at.date()).days
        return days_since_last >= 14
    elif invoice.dunning_level == 2:
        # Final reminder: 14 days after second (35 days total)
        if not invoice.last_dunning_sent_at:
            return False
        days_since_last = (reference_date - invoice.last_dunning_sent_at.date()).days
        return days_since_last >= 14
    elif invoice.dunning_level == 3:
        # Collections notice: 30 days after final (65 days total)
        if not invoice.last_dunning_sent_at:
            return False
        days_since_last = (reference_date - invoice.last_dunning_sent_at.date()).days
        return days_since_last >= 30
    else:
        # Already at maximum dunning level
        return False


def send_dunning_reminder(invoice) -> Invoice:
    """
    Send a dunning reminder for an overdue invoice (Medium Feature 2.6).

    Dunning Levels:
    - Level 0 → 1: Friendly reminder (7 days overdue)
    - Level 1 → 2: Firm reminder (21 days overdue)
    - Level 2 → 3: Final notice (35 days overdue)
    - Level 3 → 4: Collections warning (65 days overdue)

    Args:
        invoice: Invoice instance

    Returns:
        Invoice: Updated invoice with new dunning level

    Raises:
        ValidationError: If invoice is not eligible for dunning
    """
    from django.core.exceptions import ValidationError

    if invoice.status in ["paid", "cancelled", "refunded"]:
        raise ValidationError(f"Cannot send dunning reminder for invoice with status '{invoice.status}'")

    if invoice.dunning_paused:
        raise ValidationError(f"Dunning is paused for invoice {invoice.invoice_number}: {invoice.dunning_pause_reason}")

    # Increment dunning level
    invoice.dunning_level += 1
    invoice.last_dunning_sent_at = timezone.now()

    # Update invoice status if needed
    if invoice.status not in ["overdue", "disputed"]:
        invoice.status = "overdue"

    invoice.save()

    # Send appropriate dunning email based on level
    from modules.core.notifications import EmailNotification

    if invoice.dunning_level == 1:
        EmailNotification.send_dunning_reminder_1(invoice)
        logger.info(
            f"📧 Sent friendly dunning reminder for invoice {invoice.invoice_number} "
            f"(${invoice.total_amount}, {(timezone.now().date() - invoice.due_date).days} days overdue)"
        )
    elif invoice.dunning_level == 2:
        EmailNotification.send_dunning_reminder_2(invoice)
        logger.info(
            f"📧 Sent firm dunning reminder for invoice {invoice.invoice_number} "
            f"(${invoice.total_amount}, {(timezone.now().date() - invoice.due_date).days} days overdue)"
        )
    elif invoice.dunning_level == 3:
        EmailNotification.send_dunning_final_notice(invoice)
        logger.warning(
            f"⚠️  Sent final dunning notice for invoice {invoice.invoice_number} "
            f"(${invoice.total_amount}, {(timezone.now().date() - invoice.due_date).days} days overdue)"
        )
    elif invoice.dunning_level >= 4:
        EmailNotification.send_dunning_collections_warning(invoice)
        logger.warning(
            f"🚨 Sent collections warning for invoice {invoice.invoice_number} "
            f"(${invoice.total_amount}, {(timezone.now().date() - invoice.due_date).days} days overdue)"
        )

    # Log dunning action
    audit.log_billing_event(
        firm=invoice.firm,
        action="dunning_reminder_sent",
        actor=None,
        metadata={
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "dunning_level": invoice.dunning_level,
            "days_overdue": (timezone.now().date() - invoice.due_date).days,
            "amount": float(invoice.total_amount),
        },
        severity="WARNING" if invoice.dunning_level >= 3 else "INFO",
    )

    return invoice


def pause_dunning(invoice, reason: str) -> Invoice:
    """
    Pause dunning reminders for an invoice (Medium Feature 2.6).

    Use cases:
    - Payment plan agreed upon
    - Dispute in progress
    - Client communication needed
    - Temporary hardship arrangement

    Args:
        invoice: Invoice instance
        reason: Reason for pausing dunning

    Returns:
        Invoice: Updated invoice with dunning paused
    """
    invoice.dunning_paused = True
    invoice.dunning_pause_reason = reason
    invoice.save()

    logger.info(f"⏸️  Dunning paused for invoice {invoice.invoice_number}: {reason}")

    audit.log_billing_event(
        firm=invoice.firm,
        action="dunning_paused",
        actor=None,
        metadata={
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "reason": reason,
        },
    )

    return invoice


def resume_dunning(invoice) -> Invoice:
    """
    Resume dunning reminders for an invoice (Medium Feature 2.6).

    Args:
        invoice: Invoice instance

    Returns:
        Invoice: Updated invoice with dunning resumed
    """
    invoice.dunning_paused = False
    old_reason = invoice.dunning_pause_reason
    invoice.dunning_pause_reason = ""
    invoice.save()

    logger.info(f"▶️  Dunning resumed for invoice {invoice.invoice_number} (was paused: {old_reason})")

    audit.log_billing_event(
        firm=invoice.firm,
        action="dunning_resumed",
        actor=None,
        metadata={
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "previous_pause_reason": old_reason,
        },
    )

    return invoice


def process_dunning_for_overdue_invoices(reference_date: date | None = None, firm=None):
    """
    Process dunning reminders for all overdue invoices (Medium Feature 2.6).

    This function should be run daily via scheduled task/cron job.

    Args:
        reference_date: Date to check against (defaults to today)
        firm: Optional firm to scope dunning processing (tenant isolation)

    Returns:
        list: List of invoices that had dunning reminders sent
    """
    reference_date = reference_date or timezone.now().date()

    # Find potentially overdue invoices
    overdue_invoices = (
        Invoice.objects.filter(due_date__lt=reference_date, status__in=["sent", "overdue", "partial", "failed"])
        .exclude(dunning_paused=True)
        .select_related("client", "firm")
    )

    if firm:
        overdue_invoices = overdue_invoices.filter(firm=firm)

    processed_invoices = []

    for invoice in overdue_invoices:
        if should_send_dunning_reminder(invoice, reference_date):
            try:
                send_dunning_reminder(invoice)
                processed_invoices.append(invoice)
            except Exception as e:
                logger.error(f"Failed to send dunning reminder for invoice {invoice.invoice_number}: {str(e)}")

    if processed_invoices:
        logger.info(
            f"📧 Processed {len(processed_invoices)} dunning reminders "
            f"({len([i for i in processed_invoices if i.dunning_level == 1])} first, "
            f"{len([i for i in processed_invoices if i.dunning_level == 2])} second, "
            f"{len([i for i in processed_invoices if i.dunning_level == 3])} final, "
            f"{len([i for i in processed_invoices if i.dunning_level >= 4])} collections)"
        )

    return processed_invoices
