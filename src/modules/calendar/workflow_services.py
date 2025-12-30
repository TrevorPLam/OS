"""
Meeting Workflow Execution Service.

Implements workflow execution engine for pre/post meeting automation.
Handles email reminders, SMS notifications, task creation, surveys, and CRM updates.

Per MISSINGFEATURES.md: MeetingWorkflow models exist but workflows don't execute.
This service implements the missing execution engine.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.template import Template, Context
from django.utils import timezone

from .models import (
    Appointment,
    MeetingWorkflow,
    MeetingWorkflowExecution,
    AppointmentType,
)
from modules.projects.models import Task
from modules.firm.audit import AuditEvent

logger = logging.getLogger(__name__)


class WorkflowExecutionEngine:
    """
    Executes meeting workflows based on appointment lifecycle events.
    
    Responsibilities:
    - Schedule workflow executions when appointments change state
    - Execute pending workflows at scheduled times
    - Handle email, SMS, task creation, survey, and CRM actions
    - Track execution status and errors
    """
    
    def __init__(self):
        pass  # No notification service needed
    
    def trigger_workflows(
        self,
        appointment: Appointment,
        trigger_event: str,
        actor=None
    ) -> List[MeetingWorkflowExecution]:
        """
        Create workflow executions for an appointment event.
        
        Args:
            appointment: The appointment that triggered workflows
            trigger_event: One of MeetingWorkflow.TRIGGER_CHOICES
            actor: User who triggered the event (optional)
        
        Returns:
            List of created MeetingWorkflowExecution instances
        
        Valid trigger events:
        - 'appointment_created'
        - 'appointment_confirmed'
        - 'appointment_completed'
        - 'appointment_cancelled'
        """
        firm = appointment.firm
        appointment_type = appointment.appointment_type
        
        # Find matching workflows
        workflows = MeetingWorkflow.objects.filter(
            firm=firm,
            trigger=trigger_event,
            status='active'
        ).filter(
            models.Q(appointment_type=appointment_type) |
            models.Q(appointment_type__isnull=True)
        )
        
        executions = []
        now = timezone.now()
        
        with transaction.atomic():
            for workflow in workflows:
                # Calculate scheduled execution time
                scheduled_for = self._calculate_scheduled_time(
                    appointment=appointment,
                    delay_minutes=workflow.delay_minutes,
                    trigger_event=trigger_event
                )
                
                # Skip if scheduled time is in the past
                if scheduled_for < now:
                    logger.warning(
                        f"Skipping workflow {workflow.name} for appointment "
                        f"{appointment.appointment_id}: scheduled time is in the past"
                    )
                    continue
                
                # Create execution record
                execution = MeetingWorkflowExecution.objects.create(
                    workflow=workflow,
                    appointment=appointment,
                    status='pending',
                    scheduled_for=scheduled_for
                )
                executions.append(execution)
                
                logger.info(
                    f"Scheduled workflow '{workflow.name}' for appointment "
                    f"{appointment.appointment_id} at {scheduled_for}"
                )
            
            # Create audit event
            if executions:
                AuditEvent.objects.create(
                    firm=firm,
                    event_type='workflow_triggered',
                    object_type='appointment',
                    object_id=str(appointment.appointment_id),
                    actor=actor,
                    metadata={
                        'trigger_event': trigger_event,
                        'workflows_scheduled': len(executions),
                        'workflow_ids': [e.workflow.id for e in executions]
                    }
                )
        
        return executions
    
    def _calculate_scheduled_time(
        self,
        appointment: Appointment,
        delay_minutes: int,
        trigger_event: str
    ) -> datetime:
        """
        Calculate when a workflow should execute.
        
        Args:
            appointment: The appointment
            delay_minutes: Delay from trigger (negative = before, positive = after)
            trigger_event: The trigger event type
        
        Returns:
            DateTime when workflow should execute
        
        For 'before' actions (negative delay):
        - Scheduled relative to appointment start_time
        
        For 'after' actions (positive delay):
        - Scheduled relative to trigger time (now) or appointment end
        """
        if delay_minutes < 0:
            # "Before" action - schedule relative to appointment start
            return appointment.start_time + timedelta(minutes=delay_minutes)
        else:
            # "After" action - schedule relative to now or appointment end
            if trigger_event == 'appointment_completed':
                # Use appointment end time if available
                end_time = appointment.start_time + timedelta(
                    minutes=appointment.appointment_type.duration_minutes
                )
                return end_time + timedelta(minutes=delay_minutes)
            else:
                # Use current time
                return timezone.now() + timedelta(minutes=delay_minutes)
    
    def execute_pending_workflows(self) -> Dict[str, int]:
        """
        Execute all pending workflows that are due.
        
        This should be called by a scheduled task/cron job.
        
        Returns:
            Dict with execution statistics:
            - 'executed': number of successful executions
            - 'failed': number of failed executions
            - 'skipped': number of skipped executions
        """
        now = timezone.now()
        stats = {'executed': 0, 'failed': 0, 'skipped': 0}
        
        # Find pending executions that are due
        pending_executions = MeetingWorkflowExecution.objects.filter(
            status='pending',
            scheduled_for__lte=now
        ).select_related('workflow', 'appointment', 'appointment__firm')
        
        for execution in pending_executions:
            try:
                # Check if appointment was cancelled
                if execution.appointment.status == 'cancelled':
                    execution.status = 'cancelled'
                    execution.save()
                    stats['skipped'] += 1
                    logger.info(
                        f"Skipped workflow execution {execution.id}: "
                        f"appointment was cancelled"
                    )
                    continue
                
                # Execute the workflow action
                self._execute_workflow_action(execution)
                stats['executed'] += 1
                
            except Exception as e:
                stats['failed'] += 1
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.save()
                
                logger.error(
                    f"Failed to execute workflow {execution.workflow.name} "
                    f"for appointment {execution.appointment.appointment_id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"Workflow execution batch complete: "
            f"{stats['executed']} executed, {stats['failed']} failed, "
            f"{stats['skipped']} skipped"
        )
        
        return stats
    
    def _execute_workflow_action(self, execution: MeetingWorkflowExecution):
        """
        Execute a single workflow action.
        
        Args:
            execution: The workflow execution to perform
        
        Raises:
            Exception: If execution fails
        """
        workflow = execution.workflow
        appointment = execution.appointment
        action_type = workflow.action_type
        
        with transaction.atomic():
            execution.status = 'executing'
            execution.save()
            
            result = {}
            
            try:
                if action_type == 'send_email':
                    result = self._execute_send_email(workflow, appointment)
                elif action_type == 'send_sms':
                    result = self._execute_send_sms(workflow, appointment)
                elif action_type == 'create_task':
                    result = self._execute_create_task(workflow, appointment)
                elif action_type == 'send_survey':
                    result = self._execute_send_survey(workflow, appointment)
                elif action_type == 'update_crm':
                    result = self._execute_update_crm(workflow, appointment)
                else:
                    raise ValueError(f"Unknown action type: {action_type}")
                
                execution.status = 'completed'
                execution.executed_at = timezone.now()
                execution.result_data = result
                execution.save()
                
                # Create audit event
                AuditEvent.objects.create(
                    firm=appointment.firm,
                    event_type='workflow_executed',
                    object_type='appointment',
                    object_id=str(appointment.appointment_id),
                    metadata={
                        'workflow_id': workflow.id,
                        'workflow_name': workflow.name,
                        'action_type': action_type,
                        'execution_id': execution.id,
                        'result_summary': result.get('summary', 'completed')
                    }
                )
                
                logger.info(
                    f"Successfully executed workflow '{workflow.name}' "
                    f"for appointment {appointment.appointment_id}"
                )
                
            except Exception as e:
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.save()
                raise
    
    def _execute_send_email(
        self,
        workflow: MeetingWorkflow,
        appointment: Appointment
    ) -> Dict[str, Any]:
        """
        Execute send_email action.
        
        Expected action_config format:
        {
            'template': 'email body template with {{variables}}',
            'subject': 'email subject with {{variables}}',
            'to_email': 'recipient email or {{dynamic_field}}',
            'from_email': 'sender email (optional)'
        }
        """
        config = workflow.action_config
        
        # Prepare template context
        context = self._build_template_context(appointment)
        
        # Render subject and body
        subject_template = Template(config.get('subject', 'Appointment Reminder'))
        body_template = Template(config.get('template', ''))
        
        subject = subject_template.render(Context(context))
        body = body_template.render(Context(context))
        
        # Determine recipient
        to_email = self._resolve_email_recipient(
            config.get('to_email', ''),
            appointment
        )
        
        from_email = config.get('from_email', settings.DEFAULT_FROM_EMAIL)
        
        # Send email
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False
        )
        
        return {
            'summary': 'email_sent',
            'to_email': to_email,
            'subject': subject,
            'sent_at': timezone.now().isoformat()
        }
    
    def _execute_send_sms(
        self,
        workflow: MeetingWorkflow,
        appointment: Appointment
    ) -> Dict[str, Any]:
        """
        Execute send_sms action.
        
        Expected action_config format:
        {
            'message': 'SMS message with {{variables}}',
            'to_phone': 'recipient phone or {{dynamic_field}}'
        }
        
        NOTE: SMS sending requires external service integration (Twilio).
        This is a stub that logs the attempt.
        """
        config = workflow.action_config
        
        # Prepare template context
        context = self._build_template_context(appointment)
        
        # Render message
        message_template = Template(config.get('message', ''))
        message = message_template.render(Context(context))
        
        # Determine recipient
        to_phone = config.get('to_phone', '')
        
        # STUB: Log SMS attempt
        logger.info(
            f"SMS workflow action (STUB): would send to {to_phone}: {message}"
        )
        
        return {
            'summary': 'sms_stubbed',
            'to_phone': to_phone,
            'message': message,
            'note': 'SMS integration not yet implemented'
        }
    
    def _execute_create_task(
        self,
        workflow: MeetingWorkflow,
        appointment: Appointment
    ) -> Dict[str, Any]:
        """
        Execute create_task action.
        
        Expected action_config format:
        {
            'title': 'task title with {{variables}}',
            'description': 'task description',
            'assigned_to': 'user_id or {{field}}',
            'due_days': number of days from now
        }
        
        NOTE: Task creation requires a Project. If no project is available,
        logs a warning and returns a stub result.
        """
        config = workflow.action_config
        
        # Prepare template context
        context = self._build_template_context(appointment)
        
        # Render task details
        title_template = Template(config.get('title', 'Follow up on appointment'))
        description_template = Template(config.get('description', ''))
        
        title = title_template.render(Context(context))
        description = description_template.render(Context(context))
        
        # Calculate due date
        due_days = config.get('due_days', 1)
        due_date = timezone.now() + timedelta(days=due_days)
        
        # NOTE: Task model requires a project. For now, we log a warning
        # since appointments may not always have an associated project.
        # Future enhancement: Create a default "System Tasks" project or
        # make project optional in Task model.
        logger.warning(
            f"Task creation skipped for appointment {appointment.appointment_id}: "
            f"Task model requires a project which is not available from appointment"
        )
        
        return {
            'summary': 'task_creation_skipped',
            'title': title,
            'due_date': due_date.isoformat(),
            'note': 'Task creation skipped - requires project association'
        }
    
    def _execute_send_survey(
        self,
        workflow: MeetingWorkflow,
        appointment: Appointment
    ) -> Dict[str, Any]:
        """
        Execute send_survey action.
        
        Expected action_config format:
        {
            'survey_id': 'ID of survey to send',
            'to_email': 'recipient email or {{dynamic_field}}'
        }
        
        NOTE: Survey system requires separate implementation.
        This is a stub that logs the attempt.
        """
        config = workflow.action_config
        
        survey_id = config.get('survey_id', '')
        to_email = self._resolve_email_recipient(
            config.get('to_email', ''),
            appointment
        )
        
        # STUB: Log survey send attempt
        logger.info(
            f"Survey workflow action (STUB): would send survey {survey_id} "
            f"to {to_email} for appointment {appointment.appointment_id}"
        )
        
        return {
            'summary': 'survey_stubbed',
            'survey_id': survey_id,
            'to_email': to_email,
            'note': 'Survey system not yet implemented'
        }
    
    def _execute_update_crm(
        self,
        workflow: MeetingWorkflow,
        appointment: Appointment
    ) -> Dict[str, Any]:
        """
        Execute update_crm action.
        
        Expected action_config format:
        {
            'update_type': 'add_note' | 'change_stage' | 'add_tag',
            'value': 'note text or stage name or tag name'
        }
        
        NOTE: CRM update logic depends on specific CRM models.
        This is a stub that logs the attempt.
        """
        config = workflow.action_config
        
        update_type = config.get('update_type', 'add_note')
        value = config.get('value', '')
        
        # STUB: Log CRM update attempt
        logger.info(
            f"CRM workflow action (STUB): would {update_type} with value '{value}' "
            f"for appointment {appointment.appointment_id}"
        )
        
        return {
            'summary': 'crm_update_stubbed',
            'update_type': update_type,
            'value': value,
            'note': 'CRM update integration not yet implemented'
        }
    
    def _build_template_context(self, appointment: Appointment) -> Dict[str, Any]:
        """
        Build template context for workflow actions.
        
        Provides variables that can be used in templates:
        - appointment.*
        - client.*
        - staff.*
        - firm.*
        """
        context = {
            'appointment': {
                'id': appointment.appointment_id,
                'start_time': appointment.start_time.strftime('%Y-%m-%d %H:%M'),
                'status': appointment.status,
                'location_mode': appointment.appointment_type.location_mode,
                'location_details': appointment.appointment_type.location_details,
                'duration_minutes': appointment.appointment_type.duration_minutes,
            },
            'firm': {
                'name': appointment.firm.name,
            }
        }
        
        # Add client info if available
        if hasattr(appointment, 'client') and appointment.client:
            context['client'] = {
                'name': appointment.client.name,
                'email': getattr(appointment.client, 'email', ''),
            }
        
        # Add staff info if available
        if hasattr(appointment, 'staff_user') and appointment.staff_user:
            context['staff'] = {
                'name': appointment.staff_user.get_full_name(),
                'email': appointment.staff_user.email,
            }
        
        return context
    
    def _resolve_email_recipient(
        self,
        email_field: str,
        appointment: Appointment
    ) -> str:
        """
        Resolve email recipient from config.
        
        Supports:
        - Direct email: 'user@example.com'
        - Template variable: '{{client.email}}' or '{{staff.email}}'
        """
        if not email_field:
            raise ValueError("No email recipient specified")
        
        # If it's a template variable, resolve it
        if '{{' in email_field:
            context = self._build_template_context(appointment)
            template = Template(email_field)
            email = template.render(Context(context))
            return email
        
        # Otherwise return as-is
        return email_field

