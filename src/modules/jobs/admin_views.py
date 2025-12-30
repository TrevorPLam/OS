"""
Job Queue and DLQ Admin Views.

Implements DOC-20.1: Admin-gated DLQ viewing and reprocessing per docs/20 section 4.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from modules.auth.permissions import IsStaffUser, IsManager
from .models import JobQueue, JobDLQ


class JobQueueAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ViewSet for JobQueue monitoring.

    Per DOC-20.1: View job queue status, statistics, and failed jobs.
    """

    queryset = JobQueue.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "category", "priority", "error_class"]
    ordering_fields = ["created_at", "scheduled_at", "priority", "attempt_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm).select_related("firm")

    def list(self, request, *args, **kwargs):
        """List jobs with minimal payload (no sensitive content)."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        jobs_data = [
            {
                "job_id": str(job.job_id),
                "category": job.category,
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "idempotency_key": job.idempotency_key,
                "correlation_id": str(job.correlation_id),
                "attempt_count": job.attempt_count,
                "max_attempts": job.max_attempts,
                "error_class": job.error_class,
                "last_error": job.last_error[:200] if job.last_error else "",  # Truncated
                "created_at": job.created_at.isoformat(),
                "scheduled_at": job.scheduled_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in (page if page is not None else queryset)
        ]

        if page is not None:
            return self.get_paginated_response(jobs_data)

        return Response({"jobs": jobs_data, "total_count": len(jobs_data)})

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        """
        Get job queue statistics.

        Returns counts by status, category, and error class.
        """
        queryset = self.get_queryset()

        stats = {
            "total_jobs": queryset.count(),
            "by_status": {},
            "by_category": {},
            "by_error_class": {},
        }

        # Count by status
        for choice in JobQueue.STATUS_CHOICES:
            status_key = choice[0]
            stats["by_status"][status_key] = queryset.filter(status=status_key).count()

        # Count by category
        for choice in JobQueue.CATEGORY_CHOICES:
            category_key = choice[0]
            stats["by_category"][category_key] = queryset.filter(category=category_key).count()

        # Count by error class
        error_classes = ["transient", "retryable", "non_retryable", "rate_limited"]
        for error_class in error_classes:
            stats["by_error_class"][error_class] = queryset.filter(
                status="failed", error_class=error_class
            ).count()

        return Response(stats, status=status.HTTP_200_OK)


class JobDLQAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ViewSet for DLQ viewing and reprocessing.

    Per DOC-20.1: DLQ items must be viewable and reprocessable (admin-gated) per docs/20 section 4.
    """

    queryset = JobDLQ.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "category", "error_class"]
    ordering_fields = ["created_at", "original_created_at", "attempt_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm).select_related(
            "firm", "original_job", "reprocessed_by", "new_job"
        )

    def list(self, request, *args, **kwargs):
        """List DLQ items with original payload preserved."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        dlq_data = [
            {
                "dlq_id": item.dlq_id,
                "category": item.category,
                "job_type": item.job_type,
                "status": item.status,
                "idempotency_key": item.idempotency_key,
                "correlation_id": str(item.correlation_id),
                "error_class": item.error_class,
                "error_message": item.error_message[:500],  # Truncated for display
                "attempt_count": item.attempt_count,
                "payload_version": item.payload_version,
                "original_created_at": item.original_created_at.isoformat(),
                "created_at": item.created_at.isoformat(),
                "reprocessed_at": item.reprocessed_at.isoformat() if item.reprocessed_at else None,
                "reprocessed_by": item.reprocessed_by.username if item.reprocessed_by else None,
                "new_job_id": str(item.new_job.job_id) if item.new_job else None,
            }
            for item in (page if page is not None else queryset)
        ]

        if page is not None:
            return self.get_paginated_response(dlq_data)

        return Response({"dlq_items": dlq_data, "total_count": len(dlq_data)})

    def retrieve(self, request, pk=None):
        """
        Retrieve single DLQ item with full payload.

        Per docs/20 section 4: preserve original payload for reprocessing.
        """
        item = self.get_object()

        data = {
            "dlq_id": item.dlq_id,
            "category": item.category,
            "job_type": item.job_type,
            "status": item.status,
            "payload_version": item.payload_version,
            "payload": item.payload,  # Full payload for reprocessing
            "idempotency_key": item.idempotency_key,
            "correlation_id": str(item.correlation_id),
            "error_class": item.error_class,
            "error_message": item.error_message,
            "attempt_count": item.attempt_count,
            "original_job_id": str(item.original_job.job_id) if item.original_job else None,
            "original_created_at": item.original_created_at.isoformat(),
            "created_at": item.created_at.isoformat(),
            "reprocessed_at": item.reprocessed_at.isoformat() if item.reprocessed_at else None,
            "reprocessed_by": item.reprocessed_by.username if item.reprocessed_by else None,
            "reprocessing_notes": item.reprocessing_notes,
            "new_job_id": str(item.new_job.job_id) if item.new_job else None,
        }

        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reprocess")
    def reprocess(self, request, pk=None):
        """
        Reprocess a DLQ item (admin-gated).

        Per DOC-20.1: Reprocessing must be auditable and preserve original payload per docs/20 section 4.
        """
        item = self.get_object()

        # Check if already reprocessed
        if item.status in ["reprocessing", "resolved"]:
            return Response(
                {
                    "error": f"DLQ item already {item.status}",
                    "reprocessed_at": item.reprocessed_at.isoformat() if item.reprocessed_at else None,
                    "new_job_id": str(item.new_job.job_id) if item.new_job else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get reprocessing notes from request
        notes = request.data.get("notes", "")

        # Reprocess (creates audit events per docs/20 section 4)
        try:
            new_job = item.reprocess(user=request.user, notes=notes)

            return Response(
                {
                    "message": "DLQ item reprocessed successfully",
                    "dlq_id": item.dlq_id,
                    "new_job_id": str(new_job.job_id),
                    "new_idempotency_key": new_job.idempotency_key,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Reprocessing failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="discard")
    def discard(self, request, pk=None):
        """
        Mark a DLQ item as discarded (admin-gated).

        For items that should not be reprocessed.
        """
        item = self.get_object()

        if item.status == "discarded":
            return Response(
                {"error": "DLQ item already discarded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notes = request.data.get("notes", "")

        # Create audit event
        from modules.firm.audit import AuditEvent

        AuditEvent.objects.create(
            firm=item.firm,
            event_category="admin",
            event_type="job_dlq_discarded",
            actor_user=request.user,
            resource_type="JobDLQ",
            resource_id=str(item.dlq_id),
            metadata={
                "dlq_id": item.dlq_id,
                "category": item.category,
                "job_type": item.job_type,
                "notes": notes,
            },
        )

        item.status = "discarded"
        item.reprocessing_notes = notes
        item.save()

        return Response(
            {"message": "DLQ item discarded", "dlq_id": item.dlq_id},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        """Get DLQ statistics."""
        queryset = self.get_queryset()

        stats = {
            "total_dlq_items": queryset.count(),
            "by_status": {},
            "by_category": {},
            "by_error_class": {},
        }

        # Count by status
        for choice in JobDLQ.STATUS_CHOICES:
            status_key = choice[0]
            stats["by_status"][status_key] = queryset.filter(status=status_key).count()

        # Count by category
        for choice in JobQueue.CATEGORY_CHOICES:
            category_key = choice[0]
            stats["by_category"][category_key] = queryset.filter(category=category_key).count()

        # Count by error class
        error_classes = ["transient", "retryable", "non_retryable", "rate_limited"]
        for error_class in error_classes:
            stats["by_error_class"][error_class] = queryset.filter(error_class=error_class).count()

        return Response(stats, status=status.HTTP_200_OK)
