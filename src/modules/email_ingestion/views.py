"""
Email Ingestion Views.

Provides API endpoints for email triage, mapping, and review workflows.
Implements docs/15 section 5 (correction workflow) and section 6 (permissions).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from modules.auth.permissions import IsStaffUser
from modules.crm.models import Account, Engagement
from modules.projects.models import WorkItem
from .models import EmailConnection, EmailArtifact, IngestionAttempt
from .serializers import (
    EmailConnectionSerializer,
    EmailArtifactListSerializer,
    EmailArtifactDetailSerializer,
    ConfirmMappingSerializer,
    MarkIgnoredSerializer,
    IngestionAttemptSerializer,
)


class EmailConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailConnection management.

    Per docs/15 section 6: Only staff can view and manage email connections.
    """

    queryset = EmailConnection.objects.all()
    serializer_class = EmailConnectionSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["provider", "is_active"]
    search_fields = ["name", "email_address"]
    ordering_fields = ["created_at", "name", "last_sync_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm)

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(firm=self.request.firm, created_by=self.request.user)


class EmailArtifactViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for EmailArtifact triage and review.

    Per docs/15 section 6: Only staff can view and triage emails.
    Portal identities cannot see raw ingested emails.

    Provides actions for:
    - Listing emails in triage queue
    - Viewing email details
    - Confirming mappings (correction workflow per docs/15 section 5)
    - Marking emails as ignored (correction workflow per docs/15 section 5)
    """

    queryset = EmailArtifact.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "provider", "connection"]
    search_fields = ["subject", "from_address", "to_addresses"]
    ordering_fields = ["sent_at", "created_at", "mapping_confidence"]
    ordering = ["-sent_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm).select_related(
            "connection",
            "suggested_account",
            "suggested_engagement",
            "confirmed_account",
            "confirmed_engagement",
        )

    def get_serializer_class(self):
        """Use detail serializer for retrieve, list serializer otherwise."""
        if self.action == "retrieve":
            return EmailArtifactDetailSerializer
        return EmailArtifactListSerializer

    @action(detail=True, methods=["post"], url_path="confirm-mapping")
    def confirm_mapping(self, request, pk=None):
        """
        Confirm mapping for an email artifact (per docs/15 section 5).

        Creates an audit event and updates confirmed mapping fields.
        """
        email = self.get_object()
        serializer = ConfirmMappingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Fetch objects
        account = None
        engagement = None
        work_item = None

        if serializer.validated_data.get("account_id"):
            try:
                account = Account.objects.get(
                    firm=request.firm, pk=serializer.validated_data["account_id"]
                )
            except Account.DoesNotExist:
                return Response(
                    {"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND
                )

        if serializer.validated_data.get("engagement_id"):
            try:
                engagement = Engagement.objects.get(
                    firm=request.firm, pk=serializer.validated_data["engagement_id"]
                )
            except Engagement.DoesNotExist:
                return Response(
                    {"error": "Engagement not found"}, status=status.HTTP_404_NOT_FOUND
                )

        if serializer.validated_data.get("work_item_id"):
            try:
                work_item = WorkItem.objects.get(
                    firm=request.firm, pk=serializer.validated_data["work_item_id"]
                )
            except WorkItem.DoesNotExist:
                return Response(
                    {"error": "WorkItem not found"}, status=status.HTTP_404_NOT_FOUND
                )

        # Confirm mapping (creates audit event per docs/15 section 5)
        email.confirm_mapping(
            account=account, engagement=engagement, work_item=work_item, user=request.user
        )

        return Response(
            {"message": "Mapping confirmed", "email": EmailArtifactDetailSerializer(email).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="mark-ignored")
    def mark_ignored(self, request, pk=None):
        """
        Mark email as ignored with a reason (per docs/15 section 5).

        Creates an audit event.
        """
        email = self.get_object()
        serializer = MarkIgnoredSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mark ignored (creates audit event per docs/15 section 5)
        email.mark_ignored(reason=serializer.validated_data["reason"], user=request.user)

        return Response(
            {"message": "Email marked as ignored", "email": EmailArtifactDetailSerializer(email).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="triage-queue")
    def triage_queue(self, request):
        """
        Get emails that need triage (status = triage or ingested with medium confidence).

        Per docs/15 section 4: triage items must be reviewable and re-mappable.
        """
        triage_emails = self.get_queryset().filter(status__in=["triage", "ingested"]).order_by("-sent_at")
        page = self.paginate_queryset(triage_emails)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(triage_emails, many=True)
        return Response(serializer.data)


class IngestionAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for IngestionAttempt logs.

    Per docs/15 section 2.3: logs every ingestion attempt for debugging and retry-safety.
    Staff-only access per docs/15 section 6.
    """

    queryset = IngestionAttempt.objects.all()
    serializer_class = IngestionAttemptSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["operation", "status", "connection"]
    ordering_fields = ["occurred_at", "duration_ms"]
    ordering = ["-occurred_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm).select_related("connection", "email_artifact")
