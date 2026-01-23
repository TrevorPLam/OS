"""
Calendar Signals.

Handles workflow triggering when appointments change state.
Implements automatic workflow execution per MISSINGFEATURES.md requirements.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction

from .models import Appointment, AppointmentStatusHistory
from .workflow_services import WorkflowExecutionEngine

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Appointment)
def trigger_appointment_workflows(sender, instance, created, **kwargs):
    """
    Trigger workflows when appointments are created or status changes.
    
    Workflow triggers:
    - appointment_created: When appointment is first created
    - appointment_confirmed: When status changes to 'confirmed'
    - appointment_completed: When status changes to 'completed'
    - appointment_cancelled: When status changes to 'cancelled'
    """
    appointment = instance
    engine = WorkflowExecutionEngine()
    
    try:
        if created:
            # New appointment created
            engine.trigger_workflows(
                appointment=appointment,
                trigger_event='appointment_created',
                actor=getattr(appointment, '_created_by', None)
            )
            logger.info(
                f"Triggered 'appointment_created' workflows for "
                f"appointment {appointment.appointment_id}"
            )
        else:
            # Check for status changes by looking at the most recent history entry
            status_changes = AppointmentStatusHistory.objects.filter(
                appointment=appointment
            ).order_by('-changed_at')[:1]
            
            if status_changes.exists():
                status_change = status_changes.first()
                new_status = status_change.to_status
                
                # Map status to trigger event
                status_to_trigger = {
                    'confirmed': 'appointment_confirmed',
                    'completed': 'appointment_completed',
                    'cancelled': 'appointment_cancelled',
                }
                
                trigger_event = status_to_trigger.get(new_status)
                if trigger_event:
                    engine.trigger_workflows(
                        appointment=appointment,
                        trigger_event=trigger_event,
                        actor=status_change.changed_by
                    )
                    logger.info(
                        f"Triggered '{trigger_event}' workflows for "
                        f"appointment {appointment.appointment_id}"
                    )
    
    except Exception as e:
        # Log error but don't prevent appointment save
        logger.error(
            f"Failed to trigger workflows for appointment "
            f"{appointment.appointment_id}: {e}",
            exc_info=True
        )


@receiver(pre_save, sender=Appointment)
def track_appointment_status_change(sender, instance, **kwargs):
    """
    Track status changes to create AppointmentStatusHistory records.
    
    This runs before save to capture the old status.
    """
    if instance.pk:  # Only for existing appointments
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Status changed - create history record after save
                instance._status_changed = True
                instance._old_status = old_instance.status
                instance._status_change_actor = getattr(instance, '_updated_by', None)
        except Appointment.DoesNotExist:
            pass


@receiver(post_save, sender=Appointment)
def create_status_history(sender, instance, created, **kwargs):
    """
    Create AppointmentStatusHistory record when status changes.
    
    This runs after save to create the history record.
    """
    if not created and getattr(instance, '_status_changed', False):
        AppointmentStatusHistory.objects.create(
            appointment=instance,
            from_status=instance._old_status,
            to_status=instance.status,
            reason=getattr(instance, '_status_change_reason', ''),
            changed_by=getattr(instance, '_status_change_actor', None)
        )
        
        # Clean up temporary attributes
        delattr(instance, '_status_changed')
        delattr(instance, '_old_status')
        if hasattr(instance, '_status_change_actor'):
            delattr(instance, '_status_change_actor')
