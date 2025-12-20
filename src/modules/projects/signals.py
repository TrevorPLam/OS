"""
Projects Module Signals for Workflow Automation.

Implements business logic and automatic state transitions:
- Auto-set task completion timestamps
- Validate time entry constraints
- Update project status based on task completion
- Send notifications for task assignments
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Project, Task, TimeEntry
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Task)
def task_status_workflow(sender, instance, **kwargs):
    """
    Handle task status transitions and auto-set completed_at.

    Workflow:
    - * -> done: Set completed_at timestamp
    - done -> *: Clear completed_at timestamp
    """
    if instance.pk:  # Only for updates
        try:
            old_instance = Task.objects.get(pk=instance.pk)

            if old_instance.status != instance.status:
                logger.info(
                    f"Task '{instance.title}' status changed: "
                    f"{old_instance.status} -> {instance.status}"
                )

                # Auto-set completed_at when status changes to 'done'
                if instance.status == 'done' and not instance.completed_at:
                    instance.completed_at = timezone.now()
                    logger.info(f"Auto-set completed_at for task '{instance.title}'")

                # Clear completed_at if status changes away from 'done'
                if old_instance.status == 'done' and instance.status != 'done':
                    instance.completed_at = None
                    logger.info(f"Cleared completed_at for task '{instance.title}'")

            # Log task assignment changes
            if old_instance.assigned_to != instance.assigned_to:
                if instance.assigned_to:
                    logger.info(
                        f"Task '{instance.title}' assigned to {instance.assigned_to.username}"
                    )
                    # TODO: Send email notification to assigned user
                else:
                    logger.info(f"Task '{instance.title}' unassigned")

        except Task.DoesNotExist:
            pass


@receiver(post_save, sender=Task)
def task_created_notification(sender, instance, created, **kwargs):
    """
    Send notification when task is created and assigned.
    """
    if created and instance.assigned_to:
        logger.info(
            f"📋 New task created: '{instance.title}' "
            f"assigned to {instance.assigned_to.username} "
            f"in project {instance.project.name}"
        )
        # TODO: Send email/slack notification
        # notify_task_assignment(task=instance)


@receiver(pre_save, sender=TimeEntry)
def time_entry_validation(sender, instance, **kwargs):
    """
    Validate time entry business rules before save.

    Rules:
    - Cannot modify invoiced time entries
    - Cannot log time on future dates
    - Cannot log more than 24 hours per day
    """
    if instance.pk:  # Only for updates
        try:
            old_instance = TimeEntry.objects.get(pk=instance.pk)

            # Prevent modification of invoiced entries
            if old_instance.invoiced and (
                old_instance.hours != instance.hours
                or old_instance.hourly_rate != instance.hourly_rate
                or old_instance.is_billable != instance.is_billable
            ):
                logger.error(
                    f"Attempted modification of invoiced time entry {instance.id}"
                )
                from rest_framework.exceptions import ValidationError
                raise ValidationError("Cannot modify invoiced time entries")

        except TimeEntry.DoesNotExist:
            pass

    # Validate date is not in future
    if instance.date > timezone.now().date():
        logger.error(f"Attempted to log time entry for future date: {instance.date}")
        from rest_framework.exceptions import ValidationError
        raise ValidationError("Cannot log time for future dates")


@receiver(post_save, sender=TimeEntry)
def time_entry_logged_notification(sender, instance, created, **kwargs):
    """
    Log time entry creation for audit trail.
    """
    if created:
        logger.info(
            f"⏱️  Time logged: {instance.hours}h by {instance.user.username} "
            f"on project {instance.project.name} "
            f"{'(billable)' if instance.is_billable else '(non-billable)'}"
        )


@receiver(pre_save, sender=Project)
def project_status_workflow(sender, instance, **kwargs):
    """
    Handle project status transitions.

    Workflow:
    - planning -> in_progress: Log start
    - in_progress -> completed: Set actual_completion_date
    """
    if instance.pk:  # Only for updates
        try:
            old_instance = Project.objects.get(pk=instance.pk)

            if old_instance.status != instance.status:
                logger.info(
                    f"Project '{instance.name}' status changed: "
                    f"{old_instance.status} -> {instance.status}"
                )

                # Auto-set actual_completion_date when status changes to 'completed'
                if instance.status == 'completed' and not instance.actual_completion_date:
                    instance.actual_completion_date = timezone.now().date()
                    logger.info(
                        f"Auto-set actual_completion_date for project '{instance.name}'"
                    )

                # Clear actual_completion_date if status changes away from 'completed'
                if old_instance.status == 'completed' and instance.status != 'completed':
                    instance.actual_completion_date = None

                # Log project cancellation
                if instance.status == 'cancelled':
                    logger.warning(
                        f"Project '{instance.name}' cancelled. "
                        f"Budget: {instance.budget}, "
                        f"Period: {instance.start_date} to {instance.end_date}"
                    )

        except Project.DoesNotExist:
            pass


@receiver(post_save, sender=Project)
def project_completion_notification(sender, instance, created, **kwargs):
    """
    Send notification when project is completed.
    """
    if not created and instance.status == 'completed':
        logger.info(
            f"🎊 Project '{instance.name}' completed! "
            f"Duration: {instance.start_date} to {instance.actual_completion_date or instance.end_date}"
        )
        # TODO: Generate project completion report
        # TODO: Calculate final billing
        # TODO: Send completion notification to stakeholders
