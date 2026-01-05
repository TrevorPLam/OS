"""
Marketing Module Views.

Provides API endpoints for marketing automation, tagging, segmentation, and campaigns.
Implements ActiveCampaign/HubSpot-like marketing features.
"""

from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser, IsManager
from modules.firm.utils import FirmScopedMixin

from .models import (
    Tag,
    Segment,
    EmailTemplate,
    EmailDomainAuthentication,
    CampaignExecution,
    EntityTag,
)
from .serializers import (
    TagSerializer,
    SegmentSerializer,
    EmailTemplateSerializer,
    CampaignExecutionSerializer,
    EntityTagSerializer,
    EmailDomainAuthenticationSerializer,
)


class TagViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Tag management.

    Tags enable flexible categorization across leads, prospects, clients, and campaigns.
    All staff can create and apply tags.
    """

    model = Tag
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["category"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "usage_count", "created_at"]
    ordering = ["name"]

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["get"])
    def entities(self, request, pk=None):
        """
        Get all entities tagged with this tag.

        Returns list of entity types and IDs.
        """
        tag = self.get_object()
        entity_tags = EntityTag.objects.filter(tag=tag).select_related("tag", "applied_by")

        serializer = EntityTagSerializer(entity_tags, many=True)
        return Response(
            {
                "tag": TagSerializer(tag).data,
                "entities": serializer.data,
                "total": entity_tags.count(),
            },
            status=status.HTTP_200_OK,
        )


class SegmentViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Segment management.

    Segments define dynamic groups for targeted marketing campaigns.
    Only managers can create/edit segments.
    """

    model = Segment
    serializer_class = SegmentSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "auto_update"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "member_count", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        """
        Refresh segment membership based on current criteria.

        Recalculates which leads/prospects/clients match the segment criteria.
        """
        segment = self.get_object()
        segment.refresh_membership()

        return Response(
            {
                "message": "Segment refreshed",
                "segment": SegmentSerializer(segment).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate segment."""
        segment = self.get_object()
        segment.status = "active"
        segment.save(update_fields=["status"])

        return Response(
            {"message": "Segment activated", "segment": SegmentSerializer(segment).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause segment."""
        segment = self.get_object()
        segment.status = "paused"
        segment.save(update_fields=["status"])

        return Response(
            {"message": "Segment paused", "segment": SegmentSerializer(segment).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive segment."""
        segment = self.get_object()
        segment.status = "archived"
        segment.save(update_fields=["status"])

        return Response(
            {"message": "Segment archived", "segment": SegmentSerializer(segment).data},
            status=status.HTTP_200_OK,
        )


class EmailTemplateViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Email Template management.

    Email templates define reusable campaign content with merge fields.
    All staff can create templates; managers can publish/archive.
    """

    model = EmailTemplate
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["template_type", "status"]
    search_fields = ["name", "description", "subject_line"]
    ordering_fields = ["name", "times_used", "avg_open_rate", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate template for use."""
        template = self.get_object()
        template.status = "active"
        template.save(update_fields=["status"])

        return Response(
            {"message": "Template activated", "template": EmailTemplateSerializer(template).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser, IsManager])
    def archive(self, request, pk=None):
        """Archive template (managers only)."""
        template = self.get_object()
        template.status = "archived"
        template.save(update_fields=["status"])

        return Response(
            {"message": "Template archived", "template": EmailTemplateSerializer(template).data},
            status=status.HTTP_200_OK,
        )


class EmailDomainAuthenticationViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for email domain authentication records (DELIV-1).

    Tracks SPF/DKIM/DMARC verification status per firm domain.
    """

    model = EmailDomainAuthentication
    serializer_class = EmailDomainAuthenticationSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "domain", "spf_verified", "dkim_verified", "dmarc_verified"]
    ordering_fields = ["domain", "status", "created_at", "updated_at"]
    ordering = ["domain"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_verified(self, request, pk=None):
        """Mark all verification checks as passed."""
        record = self.get_object()
        record.spf_verified = True
        record.dkim_verified = True
        record.dmarc_verified = True
        record.last_checked_at = timezone.now()
        record.last_error = ""
        record.update_status()
        record.save(
            update_fields=[
                "spf_verified",
                "dkim_verified",
                "dmarc_verified",
                "last_checked_at",
                "last_error",
                "status",
                "updated_at",
            ]
        )
        return Response(
            {"message": "Domain marked verified", "domain": self.get_serializer(record).data},
            status=status.HTTP_200_OK,
        )
    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        """
        Preview template with sample merge field values.

        Accepts merge field values in request body and returns rendered content.
        """
        template = self.get_object()
        merge_fields = request.data.get("merge_fields", {})

        # Simple merge field replacement (production would use a template engine)
        subject = template.subject_line
        html_content = template.html_content

        for field, value in merge_fields.items():
            placeholder = "{{" + field + "}}"
            subject = subject.replace(placeholder, str(value))
            html_content = html_content.replace(placeholder, str(value))

        return Response(
            {
                "subject": subject,
                "html_content": html_content,
                "preheader_text": template.preheader_text,
            },
            status=status.HTTP_200_OK,
        )


class CampaignExecutionViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Campaign Execution tracking.

    Campaign executions track email sends and performance metrics.
    Only managers can create/manage campaign executions.
    """

    queryset = CampaignExecution.objects.all()
    serializer_class = CampaignExecutionSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["campaign", "status", "email_template", "segment"]
    search_fields = ["campaign__name"]
    ordering_fields = ["scheduled_for", "started_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by campaign firm."""
        queryset = self.queryset.filter(campaign__firm=self.request.firm)
        return queryset.select_related(
            "campaign",
            "email_template",
            "segment",
            "created_by",
        )

    def perform_create(self, serializer):
        """Create campaign execution."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def schedule(self, request, pk=None):
        """
        Schedule campaign execution for future send.

        Requires scheduled_for datetime in request body.
        """
        execution = self.get_object()
        scheduled_for = request.data.get("scheduled_for")

        if not scheduled_for:
            return Response(
                {"error": "scheduled_for is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if execution.status not in ["draft"]:
            return Response(
                {"error": "Only draft campaigns can be scheduled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.utils.dateparse import parse_datetime
        scheduled_datetime = parse_datetime(scheduled_for)
        if not scheduled_datetime:
            return Response(
                {"error": "Invalid datetime format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution.status = "scheduled"
        execution.scheduled_for = scheduled_datetime
        execution.save(update_fields=["status", "scheduled_for"])

        return Response(
            {
                "message": "Campaign scheduled",
                "execution": CampaignExecutionSerializer(execution).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def send_now(self, request, pk=None):
        """
        Send campaign immediately.

        In production, this would trigger email send jobs.
        For now, it marks the campaign as sending.
        """
        execution = self.get_object()

        if execution.status not in ["draft", "scheduled"]:
            return Response(
                {"error": "Campaign has already been sent or is in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.utils import timezone
        execution.status = "sending"
        execution.started_at = timezone.now()
        execution.save(update_fields=["status", "started_at"])

        # Trigger email send jobs
        # In production, this would queue background jobs for each recipient
        # For now, log the send request and mark as queued
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Campaign execution {execution.id} queued for sending",
            extra={
                "campaign_id": execution.campaign.id if execution.campaign else None,
                "template_id": execution.email_template.id if execution.email_template else None,
                "segment_id": execution.segment.id if execution.segment else None,
                "firm_id": execution.campaign.firm.id if execution.campaign else None,
            }
        )
        # Tracked in TODO: T-004 (Integrate Email Send Jobs with Background Task System)
        # Example: queue_email_campaign.delay(execution.id)

        return Response(
            {
                "message": "Campaign is being sent",
                "execution": CampaignExecutionSerializer(execution).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause campaign execution (if currently sending)."""
        execution = self.get_object()

        if execution.status != "sending":
            return Response(
                {"error": "Only sending campaigns can be paused"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution.status = "paused"
        execution.save(update_fields=["status"])

        return Response(
            {
                "message": "Campaign paused",
                "execution": CampaignExecutionSerializer(execution).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel scheduled campaign execution."""
        execution = self.get_object()

        if execution.status not in ["draft", "scheduled"]:
            return Response(
                {"error": "Only draft or scheduled campaigns can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution.status = "cancelled"
        execution.save(update_fields=["status"])

        return Response(
            {
                "message": "Campaign cancelled",
                "execution": CampaignExecutionSerializer(execution).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def update_metrics(self, request, pk=None):
        """
        Update campaign performance metrics.

        In production, this would be called by email service webhooks.
        Accepts metrics in request body and recalculates rates.
        """
        execution = self.get_object()

        # Update metrics from request
        for field in [
            "emails_sent",
            "emails_failed",
            "emails_opened",
            "emails_clicked",
            "emails_bounced",
            "emails_unsubscribed",
        ]:
            if field in request.data:
                setattr(execution, field, request.data[field])

        # Calculate rates
        execution.calculate_rates()

        return Response(
            {
                "message": "Metrics updated",
                "execution": CampaignExecutionSerializer(execution).data,
            },
            status=status.HTTP_200_OK,
        )


class EntityTagViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Entity Tag relationships.

    Manages tag application to leads, prospects, clients, campaigns, etc.
    All staff can apply/remove tags.
    """

    queryset = EntityTag.objects.all()
    serializer_class = EntityTagSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["tag", "entity_type", "entity_id", "auto_applied"]
    ordering_fields = ["applied_at"]
    ordering = ["-applied_at"]

    def get_queryset(self):
        """Filter by tag firm."""
        queryset = self.queryset.filter(tag__firm=self.request.firm)
        return queryset.select_related("tag", "applied_by")

    def perform_create(self, serializer):
        """Apply tag to entity."""
        serializer.save(applied_by=self.request.user)

    @action(detail=False, methods=["post"])
    def bulk_apply(self, request):
        """
        Apply a tag to multiple entities.

        Request body should contain:
        - tag_id: ID of tag to apply
        - entities: List of {entity_type, entity_id} objects
        """
        tag_id = request.data.get("tag_id")
        entities = request.data.get("entities", [])

        if not tag_id:
            return Response(
                {"error": "tag_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not entities:
            return Response(
                {"error": "entities list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tag = Tag.objects.get(id=tag_id, firm=request.firm)
        except Tag.DoesNotExist:
            return Response(
                {"error": "Tag not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        created_count = 0
        for entity in entities:
            entity_type = entity.get("entity_type")
            entity_id = entity.get("entity_id")

            if not entity_type or not entity_id:
                continue

            # Create tag relationship (or skip if already exists)
            _, created = EntityTag.objects.get_or_create(
                tag=tag,
                entity_type=entity_type,
                entity_id=entity_id,
                defaults={"applied_by": request.user},
            )

            if created:
                created_count += 1

        return Response(
            {
                "message": f"Tag applied to {created_count} entities",
                "tag": TagSerializer(tag).data,
                "created_count": created_count,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def bulk_remove(self, request):
        """
        Remove a tag from multiple entities.

        Request body should contain:
        - tag_id: ID of tag to remove
        - entities: List of {entity_type, entity_id} objects
        """
        tag_id = request.data.get("tag_id")
        entities = request.data.get("entities", [])

        if not tag_id:
            return Response(
                {"error": "tag_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not entities:
            return Response(
                {"error": "entities list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tag = Tag.objects.get(id=tag_id, firm=request.firm)
        except Tag.DoesNotExist:
            return Response(
                {"error": "Tag not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_count = 0
        for entity in entities:
            entity_type = entity.get("entity_type")
            entity_id = entity.get("entity_id")

            if not entity_type or not entity_id:
                continue

            deleted, _ = EntityTag.objects.filter(
                tag=tag,
                entity_type=entity_type,
                entity_id=entity_id,
            ).delete()

            deleted_count += deleted

        return Response(
            {
                "message": f"Tag removed from {deleted_count} entities",
                "tag": TagSerializer(tag).data,
                "deleted_count": deleted_count,
            },
            status=status.HTTP_200_OK,
        )
