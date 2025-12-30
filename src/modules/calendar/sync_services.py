"""
Calendar Sync Services.

Provides idempotent sync with external calendar providers (Google/Microsoft).
Implements docs/16 CALENDAR_SYNC_SPEC sections 3 (sync behavior) and 4 (retry behavior).
Enhanced with DOC-16.2: retry logic and failed attempt replay.
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from django.db import transaction, models as django_models
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


class SyncRetryStrategy:
    """
    Retry strategy for calendar sync with exponential backoff.

    Implements DOC-16.2: retry logic similar to email ingestion.
    """

    # Retry configuration
    MAX_RETRIES = 5
    BASE_DELAY_SECONDS = 2
    MAX_DELAY_SECONDS = 300  # 5 minutes
    JITTER_FACTOR = 0.1  # 10% jitter

    @classmethod
    def calculate_next_retry(cls, retry_count: int, error_class: str) -> Optional[timedelta]:
        """
        Calculate delay until next retry based on error class and retry count.

        Returns:
            timedelta for next retry, or None if should not retry.
        """
        # Non-retryable errors: never retry
        if error_class == "non_retryable":
            return None

        # Max retries exceeded
        if retry_count >= cls.MAX_RETRIES:
            return None

        # Calculate base delay with exponential backoff
        if error_class == "transient":
            # Transient errors: faster retry (1s, 2s, 4s, 8s, 16s)
            delay = min(2 ** retry_count, cls.MAX_DELAY_SECONDS)
        elif error_class == "rate_limited":
            # Rate limited: slower backoff (60s, 120s, 240s, ...)
            delay = min(60 * (2 ** retry_count), cls.MAX_DELAY_SECONDS)
        else:
            # Retryable: standard backoff (2s, 4s, 8s, 16s, 32s)
            delay = min(cls.BASE_DELAY_SECONDS * (2 ** retry_count), cls.MAX_DELAY_SECONDS)

        # Add jitter to avoid thundering herd
        jitter = delay * cls.JITTER_FACTOR * random.uniform(-1, 1)
        delay_with_jitter = max(1, delay + jitter)

        return timedelta(seconds=delay_with_jitter)

    @classmethod
    def should_retry(cls, retry_count: int, error_class: str) -> bool:
        """Return True if should retry based on error class and count."""
        return cls.calculate_next_retry(retry_count, error_class) is not None


class SyncFailedAttemptReplayService:
    """
    Service for replaying failed calendar sync attempts.

    Implements DOC-16.2: replay of failed attempts with audit trail.
    """

    def __init__(self):
        self.sync_service = CalendarSyncService()
        self.resync_service = ResyncService()
        self.retry_strategy = SyncRetryStrategy()

    def get_failed_attempts(
        self,
        firm_id: Optional[int] = None,
        connection_id: Optional[int] = None,
        include_exhausted: bool = False,
    ) -> List[SyncAttemptLog]:
        """
        Get failed sync attempts eligible for retry or review.

        Args:
            firm_id: Filter by firm
            connection_id: Filter by connection
            include_exhausted: Include attempts that hit max retries

        Returns:
            List of failed SyncAttemptLog records
        """
        queryset = SyncAttemptLog.objects.filter(status="fail").exclude(
            error_class="non_retryable"
        )

        if firm_id:
            queryset = queryset.filter(firm_id=firm_id)

        if connection_id:
            queryset = queryset.filter(connection_id=connection_id)

        if not include_exhausted:
            queryset = queryset.filter(max_retries_reached=False)

        # Filter by next_retry_at (ready to retry)
        now = timezone.now()
        queryset = queryset.filter(
            django_models.Q(next_retry_at__isnull=True) | django_models.Q(next_retry_at__lte=now)
        )

        return list(queryset.select_related("connection", "appointment").order_by("started_at"))

    @transaction.atomic
    def record_retry_attempt(
        self,
        original_attempt: SyncAttemptLog,
        error: Exception,
        user=None,
    ) -> SyncAttemptLog:
        """
        Record a retry attempt for a failed sync.

        Creates a new SyncAttemptLog with incremented retry_count.

        Args:
            original_attempt: The original failed attempt
            error: The error that occurred on retry
            user: User who initiated the retry (for audit)

        Returns:
            New SyncAttemptLog record
        """
        from modules.firm.audit import AuditEvent

        # Classify error (simplified - in production, use ErrorClassifier)
        error_type = type(error).__name__
        if error_type in ["ConnectionError", "Timeout", "TimeoutError"]:
            error_class = "transient"
        elif "rate" in str(error).lower() or "429" in str(error):
            error_class = "rate_limited"
        elif error_type in ["ValidationError", "ValueError", "PermissionDenied"]:
            error_class = "non_retryable"
        else:
            error_class = "transient"

        retry_count = original_attempt.retry_count + 1

        # Calculate next retry time
        next_retry_delay = self.retry_strategy.calculate_next_retry(retry_count, error_class)
        next_retry_at = timezone.now() + next_retry_delay if next_retry_delay else None
        max_retries_reached = not self.retry_strategy.should_retry(retry_count, error_class)

        # Create new attempt record
        new_attempt = SyncAttemptLog.objects.create(
            firm=original_attempt.firm,
            connection=original_attempt.connection,
            appointment=original_attempt.appointment,
            direction=original_attempt.direction,
            operation=original_attempt.operation,
            status="fail",
            error_class=error_class,
            error_summary=f"Retry {retry_count}: {error_type}",
            retry_count=retry_count,
            next_retry_at=next_retry_at,
            max_retries_reached=max_retries_reached,
            correlation_id=original_attempt.correlation_id,
            finished_at=timezone.now(),
        )

        # Audit event for retry
        AuditEvent.objects.create(
            firm=original_attempt.firm,
            event_category="integration",
            event_type="calendar_sync_retry",
            actor_user=user,
            resource_type="SyncAttemptLog",
            resource_id=str(new_attempt.attempt_id),
            severity="warning" if not max_retries_reached else "error",
            metadata={
                "original_attempt_id": original_attempt.attempt_id,
                "retry_count": retry_count,
                "error_class": error_class,
                "max_retries_reached": max_retries_reached,
                "next_retry_at": next_retry_at.isoformat() if next_retry_at else None,
                "connection_id": original_attempt.connection_id,
                "operation": original_attempt.operation,
                "direction": original_attempt.direction,
            },
        )

        return new_attempt

    @transaction.atomic
    def manual_replay(
        self,
        attempt: SyncAttemptLog,
        user,
    ) -> Dict:
        """
        Manually replay a failed sync attempt (admin-gated).

        Implements DOC-16.2: manual replay with full audit trail.

        Args:
            attempt: The failed attempt to replay
            user: Staff user initiating the replay

        Returns:
            dict with replay result
        """
        from modules.firm.audit import AuditEvent

        # Audit the manual replay request
        AuditEvent.objects.create(
            firm=attempt.firm,
            event_category="admin",
            event_type="calendar_sync_manual_replay_requested",
            actor_user=user,
            resource_type="SyncAttemptLog",
            resource_id=str(attempt.attempt_id),
            metadata={
                "attempt_id": attempt.attempt_id,
                "connection_id": attempt.connection_id,
                "operation": attempt.operation,
                "direction": attempt.direction,
                "original_error": attempt.error_summary,
            },
        )

        try:
            # Replay based on operation type
            if attempt.operation == "resync":
                # Replay connection resync
                result = self.resync_service.resync_connection(
                    connection=attempt.connection,
                    user=user,
                )

                # Audit success
                AuditEvent.objects.create(
                    firm=attempt.firm,
                    event_category="admin",
                    event_type="calendar_sync_manual_replay_success",
                    actor_user=user,
                    resource_type="SyncAttemptLog",
                    resource_id=str(attempt.attempt_id),
                    metadata={
                        "attempt_id": attempt.attempt_id,
                        "operation": attempt.operation,
                        "result": result,
                    },
                )

                return {"success": True, "result": result}

            elif attempt.operation == "upsert" and attempt.appointment:
                # Replay appointment resync
                result = self.resync_service.resync_appointment(
                    appointment=attempt.appointment,
                    user=user,
                )

                # Audit success
                AuditEvent.objects.create(
                    firm=attempt.firm,
                    event_category="admin",
                    event_type="calendar_sync_manual_replay_success",
                    actor_user=user,
                    resource_type="SyncAttemptLog",
                    resource_id=str(attempt.attempt_id),
                    metadata={
                        "attempt_id": attempt.attempt_id,
                        "operation": attempt.operation,
                        "appointment_id": attempt.appointment.appointment_id,
                        "result": result,
                    },
                )

                return {"success": True, "result": result}

            else:
                return {
                    "success": False,
                    "error": f"Replay not implemented for operation: {attempt.operation}",
                }

        except Exception as e:
            # Record retry failure
            self.record_retry_attempt(attempt, e, user)

            # Audit failure
            AuditEvent.objects.create(
                firm=attempt.firm,
                event_category="admin",
                event_type="calendar_sync_manual_replay_failed",
                actor_user=user,
                resource_type="SyncAttemptLog",
                resource_id=str(attempt.attempt_id),
                severity="error",
                metadata={
                    "attempt_id": attempt.attempt_id,
                    "operation": attempt.operation,
                    "error": type(e).__name__,
                },
            )

            return {"success": False, "error": str(e)}

    def get_sync_statistics(self, connection: CalendarConnection) -> Dict:
        """
        Get sync statistics for a connection.

        Returns:
            dict with sync metrics
        """
        attempts = SyncAttemptLog.objects.filter(connection=connection)

        total_attempts = attempts.count()
        successes = attempts.filter(status="success").count()
        failures = attempts.filter(status="fail").count()
        max_retries_reached = attempts.filter(max_retries_reached=True).count()
        pending_retry = attempts.filter(
            status="fail",
            max_retries_reached=False,
            next_retry_at__gt=timezone.now(),
        ).count()

        error_breakdown = {}
        for error_class in ["transient", "non_retryable", "rate_limited"]:
            error_breakdown[error_class] = attempts.filter(
                status="fail", error_class=error_class
            ).count()

        # Last successful sync
        last_success = attempts.filter(status="success").order_by("-finished_at").first()

        return {
            "total_attempts": total_attempts,
            "successes": successes,
            "failures": failures,
            "success_rate": f"{(successes / total_attempts * 100):.1f}%" if total_attempts > 0 else "0%",
            "max_retries_reached": max_retries_reached,
            "pending_retry": pending_retry,
            "eligible_for_retry": len(self.get_failed_attempts(connection_id=connection.pk)),
            "error_breakdown": error_breakdown,
            "last_successful_sync": last_success.finished_at.isoformat() if last_success and last_success.finished_at else None,
            "last_sync_cursor": connection.last_sync_cursor or "Not set",
        }
