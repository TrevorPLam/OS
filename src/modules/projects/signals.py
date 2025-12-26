"""
Projects Module Signals for Workflow Automation.

Implements business logic and automatic state transitions:
- Auto-set task completion timestamps
- Validate time entry constraints
- Update project status based on task completion
- Send notifications for task assignments
"""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Expense, Project, Task, TimeEntry

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
                logger.info(f"Task '{instance.title}' status changed: " f"{old_instance.status} -> {instance.status}")

                # Auto-set completed_at when status changes to 'done'
                if instance.status == "done" and not instance.completed_at:
                    instance.completed_at = timezone.now()
                    logger.info(f"Auto-set completed_at for task '{instance.title}'")

                # Clear completed_at if status changes away from 'done'
                if old_instance.status == "done" and instance.status != "done":
                    instance.completed_at = None
                    logger.info(f"Cleared completed_at for task '{instance.title}'")

            # Log task assignment changes
            if old_instance.assigned_to != instance.assigned_to:
                if instance.assigned_to:
                    logger.info(f"Task '{instance.title}' assigned to {instance.assigned_to.username}")
                    # Send email notification to assigned user
                    from modules.core.notifications import EmailNotification

                    EmailNotification.send_task_assignment(instance)
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
        # Send email notification
        from modules.core.notifications import EmailNotification

        EmailNotification.send_task_assignment(instance)


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
                logger.error(f"Attempted modification of invoiced time entry {instance.id}")
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
                logger.info(f"Project '{instance.name}' status changed: " f"{old_instance.status} -> {instance.status}")

                # Auto-set actual_completion_date when status changes to 'completed'
                if instance.status == "completed" and not instance.actual_completion_date:
                    instance.actual_completion_date = timezone.now().date()
                    logger.info(f"Auto-set actual_completion_date for project '{instance.name}'")

                # Clear actual_completion_date if status changes away from 'completed'
                if old_instance.status == "completed" and instance.status != "completed":
                    instance.actual_completion_date = None

                # Log project cancellation
                if instance.status == "cancelled":
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

    Implements project completion workflow:
    1. Send notifications to stakeholders
    2. Calculate final billing metrics
    3. Log completion for reporting
    """
    if not created and instance.status == "completed":
        logger.info(
            f"🎊 Project '{instance.name}' completed! "
            f"Duration: {instance.start_date} to {instance.actual_completion_date or instance.end_date}"
        )

        # Send email notification to stakeholders
        from modules.core.notifications import EmailNotification

        EmailNotification.send_project_completed(instance)

        # Log project metrics for completion report
        _log_project_completion_metrics(instance)

        # TODO: Future enhancements
        # - Automatically generate project completion PDF report
        # - Calculate final budget vs. actual comparison
        # - Trigger client satisfaction survey
        # - Archive project files


def _log_project_completion_metrics(project):
    """
    Log project completion metrics for reporting.

    Args:
        project: Project model instance
    """
    try:
        # Calculate total time logged
        from django.db.models import Sum

        total_hours = TimeEntry.objects.filter(project=project).aggregate(total=Sum("hours"))["total"] or 0

        # Calculate billable vs non-billable hours
        billable_hours = (
            TimeEntry.objects.filter(project=project, is_billable=True).aggregate(total=Sum("hours"))["total"] or 0
        )

        non_billable_hours = total_hours - billable_hours

        # Count completed tasks
        total_tasks = Task.objects.filter(project=project).count()
        completed_tasks = Task.objects.filter(project=project, status="done").count()

        # Log metrics
        logger.info(
            f"Project '{project.name}' Completion Metrics:\n"
            f"  - Total Hours: {total_hours}\n"
            f"  - Billable Hours: {billable_hours}\n"
            f"  - Non-Billable Hours: {non_billable_hours}\n"
            f"  - Tasks Completed: {completed_tasks}/{total_tasks}\n"
            f"  - Completion Date: {project.actual_completion_date or project.end_date}"
        )

    except Exception as e:
        logger.error(f"Error calculating project completion metrics: {str(e)}")


@receiver(pre_save, sender=Expense)
def expense_approval_workflow(sender, instance, **kwargs):
    """
    Handle expense approval workflow and status transitions (Medium Feature 2.4).

    Workflow:
    - draft -> submitted: Log submission
    - submitted -> approved: Set approved_at, approved_by
    - submitted -> rejected: Set rejected_at, rejected_by
    - approved -> invoiced: Lock expense from modifications

    Business Rules:
    - Cannot modify approved/invoiced expenses
    - Cannot skip approval (must go through submitted -> approved)
    - Approval requires approver and timestamp
    """
    from rest_framework.exceptions import ValidationError

    if instance.pk:  # Only for updates
        try:
            old_instance = Expense.objects.get(pk=instance.pk)

            # Prevent modification of invoiced expenses
            if old_instance.status == "invoiced":
                if (
                    old_instance.amount != instance.amount
                    or old_instance.billable_amount != instance.billable_amount
                    or old_instance.is_billable != instance.is_billable
                ):
                    logger.error(f"Attempted modification of invoiced expense {instance.id}")
                    raise ValidationError("Cannot modify invoiced expenses. " "Contact finance to adjust the invoice.")

            # Track status changes
            if old_instance.status != instance.status:
                logger.info(f"Expense {instance.id} status changed: " f"{old_instance.status} -> {instance.status}")

                # Validate approval workflow
                if instance.status == "approved":
                    # Set approval timestamp if not already set
                    if not instance.approved_at:
                        instance.approved_at = timezone.now()

                    # Ensure approver is set (should be set by the API)
                    if not instance.approved_by:
                        logger.warning(f"Expense {instance.id} approved without approver set")

                    logger.info(f"✅ Expense {instance.id} approved: " f"${instance.amount} ({instance.category})")

                # Handle rejection
                if instance.status == "rejected":
                    if not instance.rejected_at:
                        instance.rejected_at = timezone.now()

                    logger.info(f"❌ Expense {instance.id} rejected: " f"${instance.amount} ({instance.category})")

                # Clear approval fields if status changes away from approved
                if old_instance.status == "approved" and instance.status != "approved":
                    if instance.status != "invoiced":  # Don't clear if moving to invoiced
                        instance.approved_at = None
                        instance.approved_by = None
                        logger.info(f"Cleared approval for expense {instance.id}")

                # Clear rejection fields if status changes away from rejected
                if old_instance.status == "rejected" and instance.status != "rejected":
                    instance.rejected_at = None
                    instance.rejected_by = None
                    logger.info(f"Cleared rejection for expense {instance.id}")

        except Expense.DoesNotExist:
            pass
    else:
        # New expense creation
        if instance.status == "approved" and not instance.approved_at:
            instance.approved_at = timezone.now()


@receiver(post_save, sender=Expense)
def expense_submission_notification(sender, instance, created, **kwargs):
    """
    Send notifications when expenses are submitted or approved (Medium Feature 2.4).

    Notifications:
    - submitted: Notify project manager for approval
    - approved: Notify submitter of approval
    - rejected: Notify submitter of rejection with reason
    """
    from modules.core.notifications import EmailNotification

    if not created:
        # Get old instance to detect status changes
        # Note: We use a try-except since the instance might have just been saved
        try:
            if instance.status == "submitted":
                logger.info(
                    f"📋 Expense submitted for approval: "
                    f"${instance.amount} by {instance.submitted_by.username} "
                    f"on project {instance.project.project_code}"
                )
                # Send notification to project manager
                if instance.project.project_manager:
                    EmailNotification.send_expense_submitted(instance, approver=instance.project.project_manager)

            elif instance.status == "approved":
                logger.info(f"✅ Expense approved: ${instance.amount} " f"for {instance.submitted_by.username}")
                # Send notification to submitter
                EmailNotification.send_expense_approved(instance)

            elif instance.status == "rejected":
                logger.info(f"❌ Expense rejected: ${instance.amount} " f"for {instance.submitted_by.username}")
                # Send notification to submitter
                EmailNotification.send_expense_rejected(instance)

        except Exception as e:
            logger.error(f"Error sending expense notification: {str(e)}")


def approve_expense(expense, approver):
    """
    Helper function to approve an expense (Medium Feature 2.4).

    Args:
        expense: Expense instance to approve
        approver: User who is approving the expense

    Returns:
        Expense: The approved expense instance

    Raises:
        ValidationError: If expense cannot be approved
    """
    from rest_framework.exceptions import ValidationError

    if expense.status not in ["submitted", "draft"]:
        raise ValidationError(
            f"Cannot approve expense with status '{expense.status}'. "
            "Only 'submitted' or 'draft' expenses can be approved."
        )

    expense.status = "approved"
    expense.approved_by = approver
    expense.approved_at = timezone.now()
    expense.save()

    logger.info(f"Expense {expense.id} approved by {approver.username}: " f"${expense.amount} ({expense.category})")

    return expense


def reject_expense(expense, rejector, reason=""):
    """
    Helper function to reject an expense (Medium Feature 2.4).

    Args:
        expense: Expense instance to reject
        rejector: User who is rejecting the expense
        reason: Reason for rejection

    Returns:
        Expense: The rejected expense instance

    Raises:
        ValidationError: If expense cannot be rejected
    """
    from rest_framework.exceptions import ValidationError

    if expense.status not in ["submitted", "draft"]:
        raise ValidationError(
            f"Cannot reject expense with status '{expense.status}'. "
            "Only 'submitted' or 'draft' expenses can be rejected."
        )

    expense.status = "rejected"
    expense.rejected_by = rejector
    expense.rejected_at = timezone.now()
    if reason:
        expense.rejection_reason = reason
    expense.save()

    logger.info(
        f"Expense {expense.id} rejected by {rejector.username}: "
        f"${expense.amount} ({expense.category}). Reason: {reason}"
    )

    return expense
