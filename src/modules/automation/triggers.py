"""
Automation Trigger Detection System (AUTO-2).

Implements trigger detection and workflow initiation:
- Form submission triggers
- Email action triggers (open, click, reply)
- Site tracking triggers
- Deal change triggers
- Score threshold triggers
- Date-based triggers

Integrates with Django signals and event system.

Meta-commentary:
- **Current Status:** TriggerDetector handles generic trigger evaluation; contact create/update and deal lifecycle signals (create, stage change, won/lost) are wired here.
- **Design Rationale:** Idempotency keys prevent duplicate executions (WHY: avoid double-triggered workflows).
- **Assumption:** Event payloads include `contact_id` or `email` to resolve a firm-scoped contact.
- **Missing:** Additional signal hooks (site tracking events, form submissions, email events, score/date-based triggers) must call TriggerDetector elsewhere.
"""

from typing import Any, Dict, List

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from modules.clients.models import Contact
from modules.crm.models import Deal
from modules.firm.models import Firm

from .models import WorkflowExecution, WorkflowTrigger


class TriggerDetector:
    """
    Central trigger detection and workflow initiation.

    Evaluates active triggers against events and starts workflow executions.
    """

    @staticmethod
    def detect_and_trigger(
        firm: Firm,
        trigger_type: str,
        event_data: Dict[str, Any],
        contact: Contact = None,
    ) -> List[WorkflowExecution]:
        """
        Detect matching triggers and initiate workflows.

        Args:
            firm: Firm context
            trigger_type: Type of trigger event
            event_data: Event context data
            contact: Contact to execute workflow for (optional)

        Returns:
            List of created workflow executions
        """
        # Find active triggers matching this event type
        triggers = WorkflowTrigger.objects.filter(
            firm=firm,
            trigger_type=trigger_type,
            is_active=True,
            workflow__status="active",
        ).select_related("workflow")

        executions = []

        for trigger in triggers:
            # Evaluate trigger conditions
            if trigger.evaluate(event_data):
                # Determine contact if not provided
                if not contact:
                    contact = TriggerDetector._extract_contact(firm, event_data)

                if contact:
                    # Create workflow execution
                    execution = TriggerDetector._create_execution(
                        trigger=trigger,
                        contact=contact,
                        event_data=event_data,
                    )
                    if execution:
                        executions.append(execution)

        return executions

    @staticmethod
    def _extract_contact(firm: Firm, event_data: Dict[str, Any]) -> Contact:
        """
        Extract or create contact from event data.

        Args:
            firm: Firm context
            event_data: Event data containing contact information

        Returns:
            Contact instance or None
        """
        # Try to get contact from event data
        contact_id = event_data.get("contact_id")
        if contact_id:
            try:
                return Contact.objects.get(firm=firm, id=contact_id)
            except Contact.DoesNotExist:
                pass

        # Try to find by email
        email = event_data.get("email")
        if email:
            try:
                return Contact.objects.get(firm=firm, email=email)
            except Contact.DoesNotExist:
                # Could create new contact here if desired
                pass
            except Contact.MultipleObjectsReturned:
                # Multiple contacts with same email - use first
                return Contact.objects.filter(firm=firm, email=email).first()

        return None

    @staticmethod
    def _create_execution(
        trigger: WorkflowTrigger,
        contact: Contact,
        event_data: Dict[str, Any],
    ) -> WorkflowExecution:
        """
        Create workflow execution for triggered workflow.

        Args:
            trigger: Matching trigger
            contact: Contact to execute for
            event_data: Event data

        Returns:
            Created execution or None if already exists
        """
        # Compute idempotency key
        idempotency_key = WorkflowExecution.compute_idempotency_key(
            firm_id=trigger.firm_id,
            workflow_id=trigger.workflow_id,
            contact_id=contact.id,
            trigger_type=trigger.trigger_type,
            discriminator=event_data.get("discriminator", ""),
        )

        # Check if execution already exists
        existing = WorkflowExecution.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return None

        # Create execution
        execution = WorkflowExecution.objects.create(
            firm=trigger.firm,
            workflow=trigger.workflow,
            workflow_version=trigger.workflow.version,
            contact=contact,
            status="running",
            trigger_type=trigger.trigger_type,
            trigger_data=event_data,
            context_data={},
            idempotency_key=idempotency_key,
        )

        # Queue execution in job system
        from modules.automation.executor import WorkflowExecutor
        WorkflowExecutor.queue_execution(execution)

        return execution


# Signal handlers for automatic trigger detection

@receiver(post_save, sender=Contact)
def handle_contact_created(sender, instance, created, **kwargs):
    """Trigger workflows on contact creation."""
    if created:
        TriggerDetector.detect_and_trigger(
            firm=instance.firm,
            trigger_type="contact_created",
            event_data={
                "contact_id": instance.id,
                "email": instance.email,
            },
            contact=instance,
        )


@receiver(post_save, sender=Contact)
def handle_contact_updated(sender, instance, created, **kwargs):
    """Trigger workflows on contact update."""
    if not created:
        TriggerDetector.detect_and_trigger(
            firm=instance.firm,
            trigger_type="contact_updated",
            event_data={
                "contact_id": instance.id,
                "email": instance.email,
            },
            contact=instance,
        )


@receiver(post_save, sender=Deal)
def handle_deal_created(sender, instance, created, **kwargs):
    """Trigger workflows on deal creation."""
    if created:
        # Get associated contact
        contact = instance.contact if hasattr(instance, 'contact') else None

        TriggerDetector.detect_and_trigger(
            firm=instance.firm,
            trigger_type="deal_created",
            event_data={
                "deal_id": instance.id,
                "contact_id": contact.id if contact else None,
            },
            contact=contact,
        )


@receiver(pre_save, sender=Deal)
def handle_deal_stage_changed(sender, instance, **kwargs):
    """Trigger workflows on deal stage change."""
    if instance.pk:
        try:
            old_instance = Deal.objects.get(pk=instance.pk)
            if old_instance.stage_id != instance.stage_id:
                # Stage changed
                contact = instance.contact if hasattr(instance, 'contact') else None

                # Trigger on stage change
                TriggerDetector.detect_and_trigger(
                    firm=instance.firm,
                    trigger_type="deal_stage_changed",
                    event_data={
                        "deal_id": instance.id,
                        "old_stage_id": old_instance.stage_id,
                        "new_stage_id": instance.stage_id,
                        "contact_id": contact.id if contact else None,
                    },
                    contact=contact,
                )

                # Check if deal was won
                if instance.status == "won":
                    TriggerDetector.detect_and_trigger(
                        firm=instance.firm,
                        trigger_type="deal_won",
                        event_data={
                            "deal_id": instance.id,
                            "contact_id": contact.id if contact else None,
                        },
                        contact=contact,
                    )

                # Check if deal was lost
                if instance.status == "lost":
                    TriggerDetector.detect_and_trigger(
                        firm=instance.firm,
                        trigger_type="deal_lost",
                        event_data={
                            "deal_id": instance.id,
                            "contact_id": contact.id if contact else None,
                        },
                        contact=contact,
                    )
        except Deal.DoesNotExist:
            pass


# Helper functions for external trigger detection

def trigger_form_submitted(firm: Firm, form_id: int, submission_data: Dict[str, Any]):
    """
    Trigger workflows for form submission.

    Args:
        firm: Firm context
        form_id: Form ID that was submitted
        submission_data: Form submission data including contact info
    """
    return TriggerDetector.detect_and_trigger(
        firm=firm,
        trigger_type="form_submitted",
        event_data={
            "form_id": form_id,
            "submission_data": submission_data,
            **submission_data,
        },
    )


def trigger_email_opened(firm: Firm, contact: Contact, email_id: int):
    """
    Trigger workflows for email open.

    Args:
        firm: Firm context
        contact: Contact who opened email
        email_id: Email ID that was opened
    """
    return TriggerDetector.detect_and_trigger(
        firm=firm,
        trigger_type="email_opened",
        event_data={
            "contact_id": contact.id,
            "email_id": email_id,
        },
        contact=contact,
    )


def trigger_email_clicked(firm: Firm, contact: Contact, email_id: int, link_url: str):
    """
    Trigger workflows for email link click.

    Args:
        firm: Firm context
        contact: Contact who clicked
        email_id: Email ID
        link_url: URL that was clicked
    """
    return TriggerDetector.detect_and_trigger(
        firm=firm,
        trigger_type="email_clicked",
        event_data={
            "contact_id": contact.id,
            "email_id": email_id,
            "link_url": link_url,
        },
        contact=contact,
    )


def trigger_score_threshold(firm: Firm, contact: Contact, score: int, threshold: int):
    """
    Trigger workflows for score threshold reached.

    Args:
        firm: Firm context
        contact: Contact whose score changed
        score: Current score
        threshold: Threshold that was reached
    """
    return TriggerDetector.detect_and_trigger(
        firm=firm,
        trigger_type="score_threshold_reached",
        event_data={
            "contact_id": contact.id,
            "score": score,
            "threshold": threshold,
        },
        contact=contact,
    )


def trigger_page_visited(firm: Firm, contact: Contact, page_url: str, visit_data: Dict[str, Any]):
    """
    Trigger workflows for page visit.

    Args:
        firm: Firm context
        contact: Contact who visited page
        page_url: URL that was visited
        visit_data: Additional visit data (referrer, etc.)
    """
    return TriggerDetector.detect_and_trigger(
        firm=firm,
        trigger_type="page_visited",
        event_data={
            "contact_id": contact.id,
            "page_url": page_url,
            **visit_data,
        },
        contact=contact,
    )


def trigger_manual(firm: Firm, workflow_id: int, contact: Contact, context: Dict[str, Any] = None):
    """
    Manually trigger a workflow for a contact.

    Args:
        firm: Firm context
        workflow_id: Workflow to trigger
        contact: Contact to execute for
        context: Additional context data

    Returns:
        Created execution
    """
    from .models import Workflow

    try:
        workflow = Workflow.objects.get(firm=firm, id=workflow_id)
    except Workflow.DoesNotExist:
        return None

    # Create trigger if not exists
    trigger, _ = WorkflowTrigger.objects.get_or_create(
        firm=firm,
        workflow=workflow,
        trigger_type="manual",
        defaults={
            "is_active": True,
            "configuration": {},
            "filter_conditions": {},
        },
    )

    return TriggerDetector._create_execution(
        trigger=trigger,
        contact=contact,
        event_data=context or {},
    )
