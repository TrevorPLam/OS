"""
Calendar Sync Admin Views.

Provides admin-gated API endpoints for calendar sync management, resync tooling,
and failed attempt replay.

Implements DOC-16.2: admin-gated resync tooling endpoints + replay of failed attempts (audited).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from modules.auth.permissions import IsStaffUser, IsManager
from .models import CalendarConnection, SyncAttemptLog, Appointment
from .sync_services import ResyncService, SyncFailedAttemptReplayService


class CalendarConnectionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ViewSet for Calendar Connection management and resync operations.

    Per DOC-16.2: Admin-gated resync tooling with audit trail.
    """

    queryset = CalendarConnection.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["provider", "status"]
    ordering_fields = ["created_at", "last_sync_at"]
    ordering = ["-last_sync_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm).select_related(
            "owner_staff_user"
        )

    @action(detail=True, methods=["post"], url_path="resync")
    def resync(self, request, pk=None):
        """
        Manually resync a calendar connection (DOC-16.2).

        Triggers full or bounded resync and creates audit trail.
        """
        connection = self.get_object()

        # Parse optional date bounds from request
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        # Convert to datetime if provided
        from datetime import datetime
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)

        # Execute resync
        resync_service = ResyncService()
        try:
            result = resync_service.resync_connection(
                connection=connection,
                start_date=start_date,
                end_date=end_date,
                user=request.user,
            )

            return Response(
                {
                    "message": "Resync initiated successfully",
                    "connection_id": connection.connection_id,
                    "provider": connection.provider,
                    "result": result,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Resync failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="sync-status")
    def sync_status(self, request, pk=None):
        """
        Get sync status and statistics for a connection (DOC-16.2).

        Returns sync cursor, last sync time, and attempt statistics.
        """
        connection = self.get_object()

        replay_service = SyncFailedAttemptReplayService()
        stats = replay_service.get_sync_statistics(connection)

        return Response(
            {
                "connection_id": connection.connection_id,
                "provider": connection.provider,
                "status": connection.status,
                "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                "last_sync_cursor": connection.last_sync_cursor or "Not set",
                "statistics": stats,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="failed-attempts")
    def failed_attempts(self, request, pk=None):
        """
        Get failed sync attempts for a connection (DOC-16.2).

        Returns list of failed attempts with retry eligibility.
        """
        connection = self.get_object()

        include_exhausted = request.query_params.get("include_exhausted", "false").lower() == "true"

        replay_service = SyncFailedAttemptReplayService()
        failed_attempts = replay_service.get_failed_attempts(
            connection_id=connection.pk,
            include_exhausted=include_exhausted,
        )

        # Format response
        attempts_data = [
            {
                "attempt_id": attempt.attempt_id,
                "operation": attempt.operation,
                "direction": attempt.direction,
                "error_class": attempt.error_class,
                "error_summary": attempt.error_summary,
                "retry_count": attempt.retry_count,
                "max_retries_reached": attempt.max_retries_reached,
                "next_retry_at": attempt.next_retry_at.isoformat() if attempt.next_retry_at else None,
                "started_at": attempt.started_at.isoformat(),
                "appointment_id": attempt.appointment_id,
            }
            for attempt in failed_attempts
        ]

        return Response(
            {
                "connection_id": connection.connection_id,
                "failed_attempts": attempts_data,
                "total_count": len(attempts_data),
            },
            status=status.HTTP_200_OK,
        )


class SyncAttemptLogAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ViewSet for SyncAttemptLog viewing and replay.

    Per DOC-16.2: View and reprocess failed attempts (audited).
    """

    queryset = SyncAttemptLog.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "error_class", "operation", "direction", "connection"]
    ordering_fields = ["started_at", "finished_at", "retry_count"]
    ordering = ["-started_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm).select_related(
            "connection", "appointment"
        )

    @action(detail=True, methods=["post"], url_path="replay")
    def replay(self, request, pk=None):
        """
        Manually replay a failed sync attempt (DOC-16.2).

        Reprocesses the failed operation and creates full audit trail.
        """
        attempt = self.get_object()

        # Check if eligible for replay
        if attempt.status == "success":
            return Response(
                {"error": "Cannot replay successful attempt"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attempt.error_class == "non_retryable":
            return Response(
                {
                    "error": "This attempt failed with a non-retryable error and cannot be replayed",
                    "error_summary": attempt.error_summary,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Execute replay
        replay_service = SyncFailedAttemptReplayService()
        result = replay_service.manual_replay(
            attempt=attempt,
            user=request.user,
        )

        if result["success"]:
            return Response(
                {
                    "message": "Replay completed successfully",
                    "attempt_id": attempt.attempt_id,
                    "result": result.get("result"),
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "message": "Replay failed",
                    "attempt_id": attempt.attempt_id,
                    "error": result.get("error"),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="failed")
    def failed(self, request):
        """
        Get all failed attempts across connections (DOC-16.2).

        Supports filtering and pagination.
        """
        queryset = self.get_queryset().filter(status="fail")

        # Apply filters
        include_exhausted = request.query_params.get("include_exhausted", "false").lower() == "true"
        if not include_exhausted:
            queryset = queryset.filter(max_retries_reached=False)

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            attempts_data = [
                {
                    "attempt_id": attempt.attempt_id,
                    "connection_id": attempt.connection_id,
                    "operation": attempt.operation,
                    "direction": attempt.direction,
                    "error_class": attempt.error_class,
                    "error_summary": attempt.error_summary,
                    "retry_count": attempt.retry_count,
                    "max_retries_reached": attempt.max_retries_reached,
                    "next_retry_at": attempt.next_retry_at.isoformat() if attempt.next_retry_at else None,
                    "started_at": attempt.started_at.isoformat(),
                }
                for attempt in page
            ]
            return self.get_paginated_response(attempts_data)

        attempts_data = [
            {
                "attempt_id": attempt.attempt_id,
                "connection_id": attempt.connection_id,
                "operation": attempt.operation,
                "direction": attempt.direction,
                "error_class": attempt.error_class,
                "error_summary": attempt.error_summary,
                "retry_count": attempt.retry_count,
                "max_retries_reached": attempt.max_retries_reached,
                "next_retry_at": attempt.next_retry_at.isoformat() if attempt.next_retry_at else None,
                "started_at": attempt.started_at.isoformat(),
            }
            for attempt in queryset
        ]

        return Response(
            {
                "failed_attempts": attempts_data,
                "total_count": len(attempts_data),
            },
            status=status.HTTP_200_OK,
        )


class AppointmentResyncViewSet(viewsets.GenericViewSet):
    """
    Admin ViewSet for individual appointment resync operations.

    Per DOC-16.2: Resync a single appointment by ID.
    """

    queryset = Appointment.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm)

    @action(detail=True, methods=["post"], url_path="resync")
    def resync(self, request, pk=None):
        """
        Manually resync a single appointment (DOC-16.2).

        Fetches latest state from external calendar and updates internal record.
        """
        appointment = self.get_object()

        if not appointment.calendar_connection:
            return Response(
                {"error": "This appointment is not synced to an external calendar"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not appointment.external_event_id:
            return Response(
                {"error": "This appointment has no external event ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Execute resync
        resync_service = ResyncService()
        try:
            result = resync_service.resync_appointment(
                appointment=appointment,
                user=request.user,
            )

            return Response(
                {
                    "message": "Appointment resynced successfully",
                    "appointment_id": appointment.appointment_id,
                    "external_event_id": appointment.external_event_id,
                    "result": result,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Resync failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
