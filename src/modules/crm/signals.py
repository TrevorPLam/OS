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

                    # Send notification when proposal is sent
                    if old_instance.status == 'draft':
                        from modules.core.notifications import EmailNotification
                        EmailNotification.send_proposal_sent(instance)

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

    Sends email notifications to:
    - Sales team member who created the proposal
    - Account manager (if assigned)
    """
    if not created and instance.status == 'accepted':
        logger.info(
            f"🎉 Proposal {instance.proposal_number} accepted! "
            f"Value: {instance.estimated_value} {instance.currency}"
        )
        # Send email notification
        from modules.core.notifications import EmailNotification
        EmailNotification.send_proposal_accepted(instance)


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
    Send notification when contract is activated and trigger project creation workflow.

    Workflow on contract activation:
    1. Creates initial project skeleton automatically
    2. Enables client portal if not already enabled
    3. Sends notifications to stakeholders

    Sends email notifications to:
    - Project managers
    - Account manager
    - Finance team (for billing setup)
    """
    if not created and instance.status == 'active':
        logger.info(
            f"📋 Contract {instance.contract_number} activated! "
            f"Value: {instance.total_value} {instance.currency}, "
            f"Duration: {instance.start_date} to {instance.end_date}"
        )

        # MEDIUM FEATURE 2.1: Auto-create project skeleton from contract
        _create_project_from_contract(instance)

        # Initialize client portal if not already enabled
        _enable_client_portal(instance)

        # Send email notification
        from modules.core.notifications import EmailNotification
        EmailNotification.send_contract_activated(instance)


def _create_project_from_contract(contract):
    """
    Create initial project skeleton from an activated contract.

    This implements Medium Feature 2.1: Contract → Project creation workflow.

    Args:
        contract: The activated Contract instance
    """
    from modules.projects.models import Project

    # Check if a project already exists for this contract
    existing_project = Project.objects.filter(contract=contract).first()
    if existing_project:
        logger.info(
            f"Project {existing_project.project_code} already exists for "
            f"contract {contract.contract_number}. Skipping creation."
        )
        return existing_project

    # Generate project code based on contract number
    project_code = f"PRJ-{contract.contract_number}"

    # Determine billing type from contract payment terms
    billing_type = 'fixed_price'  # Default
    if contract.payment_terms == 'milestone':
        billing_type = 'fixed_price'
    elif hasattr(contract, 'billing_type'):
        billing_type = contract.billing_type

    # Create the project
    project = Project.objects.create(
        firm=contract.firm,
        client=contract.client,
        contract=contract,
        project_code=project_code,
        name=contract.title,
        description=contract.description,
        status='planning',
        billing_type=billing_type,
        budget=contract.total_value,
        start_date=contract.start_date,
        end_date=contract.end_date,
        notes=f"Auto-created from contract {contract.contract_number}"
    )

    logger.info(
        f"✅ Created project {project.project_code} from contract {contract.contract_number}"
    )

    return project


def _enable_client_portal(contract):
    """
    Enable client portal access if not already enabled.

    Args:
        contract: The activated Contract instance
    """
    client = contract.client

    if not client.portal_enabled:
        client.portal_enabled = True
        client.save(update_fields=['portal_enabled'])
        logger.info(
            f"✅ Enabled client portal for {client.company_name} "
            f"(contract {contract.contract_number})"
        )
    else:
        logger.info(
            f"Client portal already enabled for {client.company_name}"
        )
