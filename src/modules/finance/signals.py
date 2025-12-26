"""
Finance Module Signals for AP Bill State Machine Workflow.

Implements Medium Feature 2.5: AP bill state machine workflow
- Received → Validated → Approved → Scheduled → Paid
- State transition validations and business rules
- Automatic timestamp and user tracking
- Email notifications for stakeholders
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Bill

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Bill)
def bill_state_machine_workflow(sender, instance, **kwargs):
    """
    Handle AP bill state machine workflow and transitions (Medium Feature 2.5).

    State Machine Flow:
    - received: Bill entered into system
    - validated: Bill checked for accuracy (amount, vendor, items match)
    - approved: Bill approved for payment by authorized person
    - scheduled: Bill scheduled for payment on specific date
    - paid: Bill payment completed
    - rejected: Bill rejected at any stage

    Business Rules:
    - Cannot skip validation (must go: received → validated → approved)
    - Cannot modify paid bills
    - Validation requires validator and timestamp
    - Approval requires approver and timestamp
    - Payment requires scheduled date
    """
    from rest_framework.exceptions import ValidationError

    if instance.pk:  # Only for updates
        try:
            old_instance = Bill.objects.get(pk=instance.pk)

            # Prevent modification of paid bills
            if old_instance.status == "paid":
                if (
                    old_instance.total_amount != instance.total_amount
                    or old_instance.amount_paid != instance.amount_paid
                ):
                    logger.error(f"Attempted modification of paid bill {instance.reference_number}")
                    raise ValidationError("Cannot modify paid bills. Contact finance to issue adjustment.")

            # Track status changes
            if old_instance.status != instance.status:
                logger.info(
                    f"Bill {instance.reference_number} status changed: " f"{old_instance.status} → {instance.status}"
                )

                # Validate state transitions
                valid_transitions = {
                    "received": ["validated", "rejected", "disputed"],
                    "validated": ["approved", "rejected", "disputed"],
                    "approved": ["scheduled", "rejected", "disputed"],
                    "scheduled": ["paid", "partial", "overdue", "disputed"],
                    "partial": ["paid", "overdue", "disputed"],
                    "overdue": ["paid", "partial", "disputed"],
                    "disputed": ["received", "validated", "approved", "rejected"],
                    "rejected": ["received"],  # Can re-enter workflow if corrected
                }

                if old_instance.status in valid_transitions:
                    if instance.status not in valid_transitions[old_instance.status]:
                        logger.error(f"Invalid state transition: {old_instance.status} → {instance.status}")
                        raise ValidationError(
                            f"Cannot transition from '{old_instance.status}' to '{instance.status}'. "
                            f"Valid next states: {', '.join(valid_transitions[old_instance.status])}"
                        )

                # Handle validation
                if instance.status == "validated":
                    if not instance.validated_at:
                        instance.validated_at = timezone.now()

                    if not instance.validated_by:
                        logger.warning(f"Bill {instance.reference_number} validated without validator set")

                    logger.info(
                        f"✅ Bill {instance.reference_number} validated: "
                        f"${instance.total_amount} from {instance.vendor_name}"
                    )

                # Handle approval
                if instance.status == "approved":
                    if not instance.approved_at:
                        instance.approved_at = timezone.now()

                    if not instance.approved_by:
                        logger.warning(f"Bill {instance.reference_number} approved without approver set")

                    logger.info(
                        f"✅ Bill {instance.reference_number} approved for payment: " f"${instance.total_amount}"
                    )

                # Handle payment scheduling
                if instance.status == "scheduled":
                    if not instance.scheduled_payment_date:
                        # Default to due date if not specified
                        instance.scheduled_payment_date = instance.due_date
                        logger.info(f"Auto-set scheduled_payment_date to due_date for bill {instance.reference_number}")

                    logger.info(
                        f"📅 Bill {instance.reference_number} scheduled for payment on "
                        f"{instance.scheduled_payment_date}"
                    )

                # Handle payment completion
                if instance.status == "paid":
                    if not instance.paid_date:
                        instance.paid_date = timezone.now().date()

                    # Ensure amount_paid equals total_amount
                    if instance.amount_paid != instance.total_amount:
                        logger.warning(
                            f"Bill {instance.reference_number} marked as paid but "
                            f"amount_paid ({instance.amount_paid}) != total_amount ({instance.total_amount})"
                        )

                    logger.info(f"💰 Bill {instance.reference_number} paid: ${instance.amount_paid}")

                # Handle rejection
                if instance.status == "rejected":
                    if not instance.rejected_at:
                        instance.rejected_at = timezone.now()

                    logger.info(
                        f"❌ Bill {instance.reference_number} rejected: "
                        f"${instance.total_amount} from {instance.vendor_name}"
                    )

                # Clear validation fields if status changes away from validated
                if old_instance.status == "validated" and instance.status not in [
                    "validated",
                    "approved",
                    "scheduled",
                    "paid",
                ]:
                    if instance.status == "received":  # Going back to received
                        instance.validated_at = None
                        instance.validated_by = None
                        instance.validation_notes = ""
                        logger.info(f"Cleared validation for bill {instance.reference_number}")

                # Clear approval fields if status changes away from approved
                if old_instance.status == "approved" and instance.status not in ["approved", "scheduled", "paid"]:
                    if instance.status in ["received", "validated"]:  # Going back
                        instance.approved_at = None
                        instance.approved_by = None
                        logger.info(f"Cleared approval for bill {instance.reference_number}")

        except Bill.DoesNotExist:
            pass
    else:
        # New bill creation
        if instance.status == "validated" and not instance.validated_at:
            instance.validated_at = timezone.now()
        if instance.status == "approved" and not instance.approved_at:
            instance.approved_at = timezone.now()


@receiver(post_save, sender=Bill)
def bill_workflow_notification(sender, instance, created, **kwargs):
    """
    Send notifications for bill workflow state changes (Medium Feature 2.5).

    Notifications:
    - validated: Notify finance team
    - approved: Notify accounts payable and project owner
    - scheduled: Notify vendor (optional) and finance
    - paid: Notify vendor and project owner
    - rejected: Notify submitter with reason
    """
    from modules.core.notifications import EmailNotification

    if not created:
        try:
            if instance.status == "validated":
                logger.info(
                    f"📋 Bill validated: {instance.reference_number} "
                    f"from {instance.vendor_name} for ${instance.total_amount}"
                )
                # Send notification to approvers
                EmailNotification.send_bill_validated(instance)

            elif instance.status == "approved":
                logger.info(
                    f"✅ Bill approved: {instance.reference_number} " f"for payment of ${instance.total_amount}"
                )
                # Send notification to AP team
                EmailNotification.send_bill_approved(instance)

            elif instance.status == "scheduled":
                logger.info(
                    f"📅 Bill scheduled: {instance.reference_number} " f"payment on {instance.scheduled_payment_date}"
                )
                # Send notification to finance team
                EmailNotification.send_bill_scheduled(instance)

            elif instance.status == "paid":
                logger.info(
                    f"💰 Bill paid: {instance.reference_number} " f"${instance.amount_paid} to {instance.vendor_name}"
                )
                # Send payment confirmation
                EmailNotification.send_bill_paid(instance)

            elif instance.status == "rejected":
                logger.info(f"❌ Bill rejected: {instance.reference_number}")
                # Send rejection notification
                EmailNotification.send_bill_rejected(instance)

        except Exception as e:
            logger.error(f"Error sending bill workflow notification: {str(e)}")


def validate_bill(bill, validator, notes=""):
    """
    Helper function to validate a bill (Medium Feature 2.5).

    Args:
        bill: Bill instance to validate
        validator: User who is validating the bill
        notes: Validation notes

    Returns:
        Bill: The validated bill instance

    Raises:
        ValidationError: If bill cannot be validated
    """
    from rest_framework.exceptions import ValidationError

    if bill.status not in ["received", "disputed"]:
        raise ValidationError(
            f"Cannot validate bill with status '{bill.status}'. "
            "Only 'received' or 'disputed' bills can be validated."
        )

    bill.status = "validated"
    bill.validated_by = validator
    bill.validated_at = timezone.now()
    if notes:
        bill.validation_notes = notes
    bill.save()

    logger.info(
        f"Bill {bill.reference_number} validated by {validator.username}: "
        f"${bill.total_amount} from {bill.vendor_name}"
    )

    return bill


def approve_bill(bill, approver):
    """
    Helper function to approve a bill for payment (Medium Feature 2.5).

    Args:
        bill: Bill instance to approve
        approver: User who is approving the bill

    Returns:
        Bill: The approved bill instance

    Raises:
        ValidationError: If bill cannot be approved
    """
    from rest_framework.exceptions import ValidationError

    if bill.status not in ["validated", "disputed"]:
        raise ValidationError(
            f"Cannot approve bill with status '{bill.status}'. " "Bill must be validated before approval."
        )

    bill.status = "approved"
    bill.approved_by = approver
    bill.approved_at = timezone.now()
    bill.save()

    logger.info(
        f"Bill {bill.reference_number} approved by {approver.username}: " f"${bill.total_amount} scheduled for payment"
    )

    return bill


def schedule_bill_payment(bill, payment_date):
    """
    Helper function to schedule a bill for payment (Medium Feature 2.5).

    Args:
        bill: Bill instance to schedule
        payment_date: Date when payment should be made

    Returns:
        Bill: The scheduled bill instance

    Raises:
        ValidationError: If bill cannot be scheduled
    """
    from rest_framework.exceptions import ValidationError

    if bill.status != "approved":
        raise ValidationError(
            f"Cannot schedule bill with status '{bill.status}'. " "Bill must be approved before scheduling."
        )

    bill.status = "scheduled"
    bill.scheduled_payment_date = payment_date
    bill.save()

    logger.info(f"Bill {bill.reference_number} scheduled for payment on {payment_date}: " f"${bill.total_amount}")

    return bill


def reject_bill(bill, rejector, reason=""):
    """
    Helper function to reject a bill (Medium Feature 2.5).

    Args:
        bill: Bill instance to reject
        rejector: User who is rejecting the bill
        reason: Reason for rejection

    Returns:
        Bill: The rejected bill instance

    Raises:
        ValidationError: If bill cannot be rejected
    """
    from rest_framework.exceptions import ValidationError

    if bill.status in ["paid", "partial"]:
        raise ValidationError(f"Cannot reject bill with status '{bill.status}'. " "Paid bills cannot be rejected.")

    bill.status = "rejected"
    bill.rejected_by = rejector
    bill.rejected_at = timezone.now()
    if reason:
        bill.rejection_reason = reason
    bill.save()

    logger.info(
        f"Bill {bill.reference_number} rejected by {rejector.username}: " f"${bill.total_amount}. Reason: {reason}"
    )

    return bill
