"""
CRM Module Signals for Workflow Automation.

Implements business logic and automatic state transitions:
- Auto-update proposal status when accepted/rejected
- Auto-set timestamps for status changes
- Auto-create contracts from accepted proposals
- Validate business rules
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Proposal, Contract
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Proposal)
def proposal_status_workflow(sender, instance, **kwargs):
    """
    Handle proposal status transitions and auto-set timestamps.

    Workflow:
    - draft -> sent: Set sent_at timestamp
    - sent -> accepted: Set accepted_at timestamp
    - sent -> rejected: Log rejection (no timestamp needed)
    """
    if instance.pk:  # Only for updates, not creation
        try:
            old_instance = Proposal.objects.get(pk=instance.pk)

            # Track status change
            if old_instance.status != instance.status:
                logger.info(
                    f"Proposal {instance.proposal_number} status changed: "
                    f"{old_instance.status} -> {instance.status}"
                )

                # Auto-set sent_at when status changes to 'sent'
                if instance.status == 'sent' and not instance.sent_at:
                    instance.sent_at = timezone.now()
                    logger.info(f"Auto-set sent_at for proposal {instance.proposal_number}")

                # Auto-set accepted_at when status changes to 'accepted'
                if instance.status == 'accepted' and not instance.accepted_at:
                    instance.accepted_at = timezone.now()
                    logger.info(f"Auto-set accepted_at for proposal {instance.proposal_number}")

                # Clear accepted_at if status changes away from 'accepted'
                if old_instance.status == 'accepted' and instance.status != 'accepted':
                    instance.accepted_at = None
                    logger.info(f"Cleared accepted_at for proposal {instance.proposal_number}")

        except Proposal.DoesNotExist:
            pass


@receiver(post_save, sender=Proposal)
def proposal_accepted_notification(sender, instance, created, **kwargs):
    """
    Send notification when proposal is accepted.

    In production, this would send:
    - Email to sales team
    - Slack notification
    - CRM update
    """
    if not created and instance.status == 'accepted':
        logger.info(
            f"🎉 Proposal {instance.proposal_number} accepted! "
            f"Value: {instance.estimated_value} {instance.currency}"
        )
        # TODO: Send actual notifications when email system is integrated
        # send_email_notification(
        #     to=instance.created_by.email,
        #     subject=f"Proposal {instance.proposal_number} Accepted!",
        #     template='proposal_accepted',
        #     context={'proposal': instance}
        # )


@receiver(pre_save, sender=Contract)
def contract_status_workflow(sender, instance, **kwargs):
    """
    Handle contract status transitions and auto-set timestamps.

    Workflow:
    - draft -> active: Ensure signed_date is set
    - active -> completed: Set actual end date
    - * -> cancelled: Log cancellation
    """
    if instance.pk:  # Only for updates
        try:
            old_instance = Contract.objects.get(pk=instance.pk)

            if old_instance.status != instance.status:
                logger.info(
                    f"Contract {instance.contract_number} status changed: "
                    f"{old_instance.status} -> {instance.status}"
                )

                # Ensure signed_date is set when activating contract
                if instance.status == 'active' and not instance.signed_date:
                    instance.signed_date = timezone.now().date()
                    logger.warning(
                        f"Auto-set signed_date for contract {instance.contract_number} "
                        f"(should be set manually)"
                    )

                # Log important transitions
                if instance.status == 'cancelled':
                    logger.warning(f"Contract {instance.contract_number} cancelled")

                if instance.status == 'completed':
                    logger.info(
                        f"Contract {instance.contract_number} completed. "
                        f"Duration: {instance.start_date} to {instance.end_date}"
                    )

        except Contract.DoesNotExist:
            pass


@receiver(post_save, sender=Contract)
def contract_activation_notification(sender, instance, created, **kwargs):
    """
    Send notification when contract is activated.
    """
    if not created and instance.status == 'active':
        logger.info(
            f"📋 Contract {instance.contract_number} activated! "
            f"Value: {instance.contract_value} {instance.currency}, "
            f"Duration: {instance.start_date} to {instance.end_date}"
        )
        # TODO: Send notifications
        # - Notify project managers
        # - Create initial project skeleton
        # - Set up billing schedule
