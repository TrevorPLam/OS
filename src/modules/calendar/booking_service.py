"""Appointment booking services for calendar scheduling."""

import logging
from datetime import datetime
from typing import List

from django.db import transaction
from django.utils import timezone

from .models import Appointment, AppointmentStatusHistory, AppointmentType

logger = logging.getLogger(__name__)


class BookingService:
    """
    Service for booking appointments.

    Implements docs/03-reference/requirements/DOC-34.md section 3: booking flows with race condition protection.
    """

    @transaction.atomic
    def book_appointment(
        self,
        appointment_type: AppointmentType,
        start_time: datetime,
        end_time: datetime,
        staff_user,
        booked_by,
        account=None,
        contact=None,
        engagement=None,
        intake_responses=None,
        booking_link=None,
    ) -> Appointment:
        """
        Book an appointment with atomic transaction for race condition protection.

        Per docs/03-reference/requirements/DOC-34.md section 4.5: slot selection protected against race conditions.
        Per docs/03-reference/requirements/DOC-34.md section 3: creates appointment in requested or confirmed status.
        """
        # Check for conflicts within transaction (per docs/03-reference/requirements/DOC-34.md section 4.5)
        conflicts = Appointment.objects.select_for_update().filter(
            staff_user=staff_user,
            status__in=["requested", "confirmed"],
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()

        if conflicts:
            raise ValueError("Time slot is no longer available (conflict detected)")

        # Determine initial status (per docs/03-reference/requirements/DOC-34.md section 3.1)
        initial_status = "requested" if appointment_type.requires_approval else "confirmed"

        # Create appointment
        appointment = Appointment.objects.create(
            firm=appointment_type.firm,
            appointment_type=appointment_type,
            booking_link=booking_link,
            staff_user=staff_user,
            account=account,
            contact=contact,
            start_time=start_time,
            end_time=end_time,
            timezone=appointment_type.firm.timezone if hasattr(appointment_type.firm, 'timezone') else 'UTC',
            intake_responses=intake_responses or {},
            status=initial_status,
            booked_by=booked_by,
        )

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status="",
            to_status=initial_status,
            reason="Initial booking",
            changed_by=booked_by,
        )

        return appointment

    @transaction.atomic
    def book_collective_appointment(
        self,
        appointment_type: AppointmentType,
        start_time: datetime,
        end_time: datetime,
        collective_hosts: List[any],
        booked_by,
        account=None,
        contact=None,
        engagement=None,
        intake_responses=None,
        booking_link=None,
    ) -> Appointment:
        """
        Book a collective event appointment with multiple hosts.

        TEAM-1: Implements collective event booking with Venn diagram availability.
        Ensures all required hosts are available and books with all hosts atomically.

        Args:
            appointment_type: AppointmentType with event_category="collective"
            start_time: Start time for appointment
            end_time: End time for appointment
            collective_hosts: List of host users (required + available optional)
            booked_by: User who is booking the appointment
            account: Optional client account
            contact: Optional contact
            engagement: Optional engagement
            intake_responses: Optional intake question responses
            booking_link: Optional booking link used

        Returns:
            Created Appointment instance

        Raises:
            ValueError: If conflicts detected for any host
        """
        if appointment_type.event_category != "collective":
            raise ValueError("book_collective_appointment only works with collective event types")

        if not collective_hosts:
            raise ValueError("Collective events require at least one host")

        # Check for conflicts for ALL hosts within transaction (race condition protection)
        for host in collective_hosts:
            conflicts = Appointment.objects.select_for_update().filter(
                staff_user=host,
                status__in=["requested", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exists()

            # Also check if host is in collective_hosts of other appointments
            collective_conflicts = Appointment.objects.select_for_update().filter(
                collective_hosts=host,
                status__in=["requested", "confirmed"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exists()

            if conflicts or collective_conflicts:
                raise ValueError(
                    f"Time slot is no longer available for host {host.username} (conflict detected)"
                )

        # Determine initial status
        initial_status = "requested" if appointment_type.requires_approval else "confirmed"

        # Use the first required host as the primary staff_user for backward compatibility
        required_hosts = list(appointment_type.required_hosts.all())
        primary_staff_user = required_hosts[0] if required_hosts else collective_hosts[0]

        # Create appointment
        appointment = Appointment.objects.create(
            firm=appointment_type.firm,
            appointment_type=appointment_type,
            booking_link=booking_link,
            staff_user=primary_staff_user,
            account=account,
            contact=contact,
            start_time=start_time,
            end_time=end_time,
            timezone=appointment_type.firm.timezone if hasattr(appointment_type.firm, 'timezone') else 'UTC',
            intake_responses=intake_responses or {},
            status=initial_status,
            booked_by=booked_by,
        )

        # Add all collective hosts
        appointment.collective_hosts.set(collective_hosts)

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status="",
            to_status=initial_status,
            reason=f"Initial collective event booking with {len(collective_hosts)} hosts",
            changed_by=booked_by,
        )

        logger.info(
            f"Booked collective appointment {appointment.appointment_id} "
            f"with {len(collective_hosts)} hosts: {[h.username for h in collective_hosts]}"
        )

        return appointment

    @transaction.atomic
    def cancel_appointment(
        self,
        appointment: Appointment,
        reason: str,
        cancelled_by,
    ) -> Appointment:
        """
        Cancel an appointment.

        Creates status history entry for audit trail.
        """
        old_status = appointment.status
        appointment.status = "cancelled"
        appointment.status_reason = reason
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="cancelled",
            reason=reason,
            changed_by=cancelled_by,
        )

        return appointment

    @transaction.atomic
    def confirm_appointment(
        self,
        appointment: Appointment,
        confirmed_by,
    ) -> Appointment:
        """
        Confirm a requested appointment (approval flow).

        Per docs/03-reference/requirements/DOC-34.md section 3.1: approval-required appointments start as requested.
        """
        if appointment.status != "requested":
            raise ValueError("Only requested appointments can be confirmed")

        old_status = appointment.status
        appointment.status = "confirmed"
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="confirmed",
            reason="Approved by staff",
            changed_by=confirmed_by,
        )

        # Trigger confirmation workflows
        from .workflow_services import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        engine.trigger_workflows(
            appointment=appointment,
            trigger_event="appointment_confirmed",
            actor=confirmed_by,
        )

        return appointment

    @transaction.atomic
    def reject_appointment(
        self,
        appointment: Appointment,
        rejected_by,
        reason: str = "",
    ) -> Appointment:
        """
        Reject a requested appointment (denial flow).

        FLOW-3: Enables rejection workflows with automatic notifications.

        Args:
            appointment: Appointment to reject
            rejected_by: User rejecting the appointment
            reason: Reason for rejection

        Returns:
            Updated Appointment instance
        """
        if appointment.status != "requested":
            raise ValueError("Only requested appointments can be rejected")

        old_status = appointment.status
        appointment.status = "cancelled"
        appointment.status_reason = f"Rejected: {reason}" if reason else "Rejected by host"
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="cancelled",
            reason=f"Rejected by staff" + (f": {reason}" if reason else ""),
            changed_by=rejected_by,
        )

        logger.info(f"Rejected appointment {appointment.appointment_id}")

        # Trigger rejection workflows (notification emails, etc.)
        from .workflow_services import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        engine.trigger_workflows(
            appointment=appointment,
            trigger_event="appointment_cancelled",  # Use cancellation trigger for rejection
            actor=rejected_by,
        )

        # If this was a group event, check if we should promote from waitlist
        if appointment.appointment_type.event_category == "group":
            # Note: In a rejection scenario, we typically don't promote from waitlist
            # since the slot was never actually taken
            pass

        return appointment

    @transaction.atomic
    def mark_no_show(
        self,
        appointment: Appointment,
        marked_by,
        party: str = "client",
        reason: str = "",
    ) -> Appointment:
        """
        Mark an appointment as no-show.

        FLOW-2: Enables no-show follow-up workflows.

        Args:
            appointment: Appointment to mark as no-show
            marked_by: User marking the no-show
            party: Who didn't show up ("client" or "staff")
            reason: Optional reason for no-show

        Returns:
            Updated Appointment instance
        """
        if appointment.status not in ["confirmed", "requested"]:
            raise ValueError("Only confirmed or requested appointments can be marked as no-show")

        old_status = appointment.status
        appointment.status = "no_show"
        appointment.status_reason = reason
        appointment.no_show_at = timezone.now()
        appointment.no_show_party = party
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="no_show",
            reason=f"No-show by {party}" + (f": {reason}" if reason else ""),
            changed_by=marked_by,
        )

        logger.info(
            f"Marked appointment {appointment.appointment_id} as no-show ({party})"
        )

        # Trigger no-show workflows
        from .workflow_services import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        engine.trigger_workflows(
            appointment=appointment,
            trigger_event="appointment_no_show",
            actor=marked_by,
        )

        return appointment

    @transaction.atomic
    def complete_appointment(
        self,
        appointment: Appointment,
        completed_by,
        notes: str = "",
    ) -> Appointment:
        """
        Mark an appointment as completed.

        FLOW-2: Triggers post-meeting follow-up workflows.

        Args:
            appointment: Appointment to complete
            completed_by: User marking as complete
            notes: Optional completion notes

        Returns:
            Updated Appointment instance
        """
        if appointment.status not in ["confirmed"]:
            raise ValueError("Only confirmed appointments can be marked as completed")

        old_status = appointment.status
        appointment.status = "completed"
        if notes:
            appointment.notes = (appointment.notes or "") + "\n\n" + notes
        appointment.save()

        # Create status history entry
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=old_status,
            to_status="completed",
            reason="Marked as completed" + (f": {notes}" if notes else ""),
            changed_by=completed_by,
        )

        logger.info(f"Completed appointment {appointment.appointment_id}")

        # Trigger completion workflows (thank you emails, surveys, etc.)
        from .workflow_services import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        engine.trigger_workflows(
            appointment=appointment,
            trigger_event="appointment_completed",
            actor=completed_by,
        )

        return appointment

    @transaction.atomic
    def substitute_collective_host(
        self,
        appointment: Appointment,
        old_host,
        new_host,
        substituted_by,
        reason: str = "",
    ) -> Appointment:
        """
        Substitute a host in a collective event appointment.

        TEAM-1: Implements host substitution workflow for collective events.
        Validates that the new host is available and atomically updates the appointment.

        Args:
            appointment: Appointment to modify
            old_host: Host to remove
            new_host: Host to add as replacement
            substituted_by: User performing the substitution
            reason: Optional reason for substitution

        Returns:
            Updated Appointment instance

        Raises:
            ValueError: If not a collective event, host not found, or new host has conflict
        """
        if appointment.appointment_type.event_category != "collective":
            raise ValueError("Host substitution only supported for collective events")

        if old_host not in appointment.collective_hosts.all():
            raise ValueError("Old host is not part of this collective event")

        # Validate new host availability
        conflicts = Appointment.objects.filter(
            staff_user=new_host,
            status__in=["requested", "confirmed"],
            start_time__lt=appointment.end_time,
            end_time__gt=appointment.start_time,
        ).exists()

        # Also check if new host is in collective_hosts of other appointments
        collective_conflicts = Appointment.objects.select_for_update().filter(
            collective_hosts=new_host,
            status__in=["requested", "confirmed"],
            start_time__lt=appointment.end_time,
            end_time__gt=appointment.start_time,
        ).exists()

        if conflicts or collective_conflicts:
            raise ValueError(
                f"Cannot substitute: new host {new_host.username} has a conflicting appointment"
            )

        # Remove old host and add new host
        appointment.collective_hosts.remove(old_host)
        appointment.collective_hosts.add(new_host)

        # Update primary staff_user if the old host was primary
        if appointment.staff_user == old_host:
            appointment.staff_user = new_host
            appointment.save()

        # Create audit trail in status history
        substitution_reason = reason or f"Host substitution: {old_host.username} → {new_host.username}"
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status=appointment.status,
            to_status=appointment.status,
            reason=substitution_reason,
            changed_by=substituted_by,
        )

        logger.info(
            f"Substituted host in appointment {appointment.appointment_id}: "
            f"{old_host.username} → {new_host.username}"
        )

        return appointment
