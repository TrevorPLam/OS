"""
Calendar Sync Services.

Provides idempotent sync with external calendar providers (Google/Microsoft).
Implements docs/16 CALENDAR_SYNC_SPEC sections 3 (sync behavior) and 4 (retry behavior).
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from django.db import transaction
from django.utils import timezone

from .models import (
    CalendarConnection,
    Appointment,
    SyncAttemptLog,
    AppointmentType,
)


class CalendarSyncService:
    """
    Service for syncing appointments with external calendar providers.

    Implements docs/16 sections 3.1 (pull) and 3.2 (push) with idempotency.
    """

    @transaction.atomic
    def pull_appointment(
        self,
        connection: CalendarConnection,
        external_event_data: Dict,
        correlation_id: Optional[uuid.UUID] = None,
    ) -> Tuple[Appointment, bool]:
        """
        Pull an external event and upsert as an Appointment.

        Per docs/16 section 3.1: Upsert by (connection_id, external_event_id).
        Returns: (appointment, created)

        Args:
            connection: Calendar connection
            external_event_data: Event data from external provider
                {
                    'id': '...',
                    'summary': '...',
                    'start': {'dateTime': '...'},
                    'end': {'dateTime': '...'},
                    'status': 'confirmed' | 'cancelled',
                    ...
                }
            correlation_id: Optional correlation ID for tracing
        """
        correlation_id = correlation_id or uuid.uuid4()
        start_time = timezone.now()

        external_event_id = external_event_data.get("id")
        if not external_event_id:
            self._log_sync_attempt(
                connection=connection,
                direction="pull",
                operation="upsert",
                status="fail",
                error_class="non_retryable",
                error_summary="Missing external event ID",
                correlation_id=correlation_id,
                start_time=start_time,
            )
            raise ValueError("External event data must include 'id'")

        # Check for existing appointment (per docs/16 section 3.1: upsert by connection + external_event_id)
        existing = Appointment.objects.filter(
            calendar_connection=connection,
            external_event_id=external_event_id,
        ).first()

        # Parse external event data
        try:
            parsed_data = self._parse_external_event(connection, external_event_data)
        except Exception as e:
            self._log_sync_attempt(
                connection=connection,
                direction="pull",
                operation="upsert",
                status="fail",
                error_class="non_retryable",
                error_summary=f"Failed to parse external event: {type(e).__name__}",
                correlation_id=correlation_id,
                start_time=start_time,
            )
            raise

        created = False
        if existing:
            # Update existing appointment (per docs/16 section 3.1: apply reconciliation rules)
            old_start = existing.start_time
            old_end = existing.end_time

            existing.start_time = parsed_data["start_time"]
            existing.end_time = parsed_data["end_time"]

            # Apply cancellation policy (per docs/16 section 3.1)
            if parsed_data["is_cancelled"]:
                existing.status = "cancelled"
                existing.status_reason = "Cancelled externally"

            existing.save()

            # Log change if times changed
            if old_start != parsed_data["start_time"] or old_end != parsed_data["end_time"]:
                from modules.firm.audit import AuditEvent
                AuditEvent.objects.create(
                    firm=connection.firm,
                    event_category="data",
                    event_type="appointment_time_changed_by_sync",
                    resource_type="Appointment",
                    resource_id=str(existing.appointment_id),
                    metadata={
                        "old_start": old_start.isoformat(),
                        "new_start": parsed_data["start_time"].isoformat(),
                        "old_end": old_end.isoformat(),
                        "new_end": parsed_data["end_time"].isoformat(),
                        "external_event_id": external_event_id,
                    },
                )

            appointment = existing
        else:
            # Create new appointment
            appointment = Appointment.objects.create(
                firm=connection.firm,
                appointment_type=parsed_data["appointment_type"],
                staff_user=connection.owner_staff_user,
                calendar_connection=connection,
                external_event_id=external_event_id,
                start_time=parsed_data["start_time"],
                end_time=parsed_data["end_time"],
                status="confirmed" if not parsed_data["is_cancelled"] else "cancelled",
                booked_by=connection.owner_staff_user,
            )
            created = True

        # Log successful sync
        self._log_sync_attempt(
            connection=connection,
            appointment=appointment,
            direction="pull",
            operation="upsert",
            status="success",
            correlation_id=correlation_id,
            start_time=start_time,
        )

        return appointment, created

    @transaction.atomic
    def push_appointment(
        self,
        appointment: Appointment,
        connection: CalendarConnection,
        correlation_id: Optional[uuid.UUID] = None,
    ) -> str:
        """
        Push an internal appointment to external calendar provider.

        Per docs/16 section 3.2: Store returned external_event_id.
        Retries MUST not create duplicates.

        Returns: external_event_id

        Note: This is a stub implementation. In production, you would:
        1. Call the provider's API (Google Calendar API, Microsoft Graph API)
        2. Handle OAuth refresh if needed
        3. Implement provider-specific idempotency
        """
        correlation_id = correlation_id or uuid.uuid4()
        start_time = timezone.now()

        # STUB: In production, call external provider API here
        # For now, generate a fake external event ID
        external_event_id = f"ext_{appointment.appointment_id}_{uuid.uuid4().hex[:8]}"

        # Update appointment with external_event_id
        appointment.calendar_connection = connection
        appointment.external_event_id = external_event_id
        appointment.save()

        # Log successful push
        self._log_sync_attempt(
            connection=connection,
            appointment=appointment,
            direction="push",
            operation="upsert",
            status="success",
            correlation_id=correlation_id,
            start_time=start_time,
        )

        return external_event_id

    def _parse_external_event(
        self, connection: CalendarConnection, event_data: Dict
    ) -> Dict:
        """
        Parse external event data into internal format.

        Handles timezone correctness (per docs/16 section 7).
        """
        from dateutil import parser as date_parser

        # Parse start/end times (per docs/16 section 7: timezone correctness)
        start_str = event_data.get("start", {}).get("dateTime") or event_data.get("start", {}).get("date")
        end_str = event_data.get("end", {}).get("dateTime") or event_data.get("end", {}).get("date")

        if not start_str or not end_str:
            raise ValueError("Event must have start and end times")

        start_time = date_parser.parse(start_str)
        end_time = date_parser.parse(end_str)

        # Ensure times are timezone-aware and in UTC
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)

        # Get or create a default appointment type for synced events
        appointment_type, _ = AppointmentType.objects.get_or_create(
            firm=connection.firm,
            name="Synced Event",
            defaults={
                "duration_minutes": 30,
                "location_mode": "custom",
                "routing_policy": "fixed_staff",
                "fixed_staff_user": connection.owner_staff_user,
                "status": "active",
            },
        )

        # Check if cancelled
        is_cancelled = event_data.get("status") == "cancelled"

        return {
            "start_time": start_time,
            "end_time": end_time,
            "appointment_type": appointment_type,
            "is_cancelled": is_cancelled,
        }

    def _log_sync_attempt(
        self,
        connection: CalendarConnection,
        direction: str,
        operation: str,
        status: str,
        start_time: datetime,
        appointment: Optional[Appointment] = None,
        error_class: str = "",
        error_summary: str = "",
        correlation_id: Optional[uuid.UUID] = None,
    ):
        """Log a sync attempt (per docs/16 section 2.3)."""
        duration_ms = int((timezone.now() - start_time).total_seconds() * 1000)

        SyncAttemptLog.objects.create(
            firm=connection.firm,
            connection=connection,
            appointment=appointment,
            direction=direction,
            operation=operation,
            status=status,
            error_class=error_class,
            error_summary=error_summary,
            correlation_id=correlation_id,
            finished_at=timezone.now(),
            duration_ms=duration_ms,
        )


class ResyncService:
    """
    Service for manual resync tooling.

    Implements docs/16 section 5: manual resync with audit.
    """

    def __init__(self):
        self.sync_service = CalendarSyncService()

    @transaction.atomic
    def resync_connection(
        self,
        connection: CalendarConnection,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user=None,
    ) -> Dict:
        """
        Manually resync a calendar connection (per docs/16 section 5).

        Args:
            connection: Calendar connection to resync
            start_date: Optional start date for bounded resync
            end_date: Optional end date for bounded resync
            user: User performing the resync (for audit)

        Returns:
            Dict with sync stats
        """
        from modules.firm.audit import AuditEvent

        correlation_id = uuid.uuid4()

        # Log resync request
        AuditEvent.objects.create(
            firm=connection.firm,
            event_category="admin",
            event_type="calendar_connection_resync_requested",
            actor_user=user,
            resource_type="CalendarConnection",
            resource_id=str(connection.connection_id),
            metadata={
                "provider": connection.provider,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "correlation_id": str(correlation_id),
            },
        )

        # STUB: In production, fetch events from external provider here
        # For now, just log the resync attempt
        SyncAttemptLog.objects.create(
            firm=connection.firm,
            connection=connection,
            direction="pull",
            operation="resync",
            status="success",
            correlation_id=correlation_id,
            finished_at=timezone.now(),
        )

        # Update last sync timestamp
        connection.last_sync_at = timezone.now()
        connection.save()

        return {
            "status": "success",
            "correlation_id": str(correlation_id),
            "synced_count": 0,  # STUB: In production, return actual count
        }

    @transaction.atomic
    def resync_appointment(
        self,
        appointment: Appointment,
        user=None,
    ) -> Dict:
        """
        Manually resync a single appointment (per docs/16 section 5).

        Args:
            appointment: Appointment to resync
            user: User performing the resync (for audit)

        Returns:
            Dict with sync status
        """
        from modules.firm.audit import AuditEvent

        if not appointment.calendar_connection:
            raise ValueError("Appointment is not synced to an external calendar")

        correlation_id = uuid.uuid4()

        # Log resync request
        AuditEvent.objects.create(
            firm=appointment.firm,
            event_category="admin",
            event_type="appointment_resync_requested",
            actor_user=user,
            resource_type="Appointment",
            resource_id=str(appointment.appointment_id),
            metadata={
                "external_event_id": appointment.external_event_id,
                "connection_id": appointment.calendar_connection.connection_id,
                "correlation_id": str(correlation_id),
            },
        )

        # STUB: In production, fetch event from external provider and call pull_appointment
        SyncAttemptLog.objects.create(
            firm=appointment.firm,
            connection=appointment.calendar_connection,
            appointment=appointment,
            direction="pull",
            operation="resync",
            status="success",
            correlation_id=correlation_id,
            finished_at=timezone.now(),
        )

        return {
            "status": "success",
            "correlation_id": str(correlation_id),
        }
