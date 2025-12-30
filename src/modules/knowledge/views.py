"""
Knowledge System Views (DOC-35.1).

Implements API endpoints for knowledge management per docs/35.
"""

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.permissions import IsStaffUser
from modules.auth.role_permissions import CanAccessKnowledge, is_admin, is_manager_or_above, get_user_role
from modules.firm.utils import FirmScopedMixin

from .models import KnowledgeItem, KnowledgeVersion, KnowledgeReview, KnowledgeAttachment
from .serializers import (
    KnowledgeItemSerializer,
    KnowledgeItemDetailSerializer,
    KnowledgeVersionSerializer,
    KnowledgeReviewSerializer,
    KnowledgeAttachmentSerializer,
)


class KnowledgeItemViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    Knowledge Item management (docs/35).

    Provides CRUD + workflow actions: publish, deprecate, archive, create_version.
    Access control per docs/35 section 4: role-based + item-level access_level.
    """

    model = KnowledgeItem
    permission_classes = [IsAuthenticated, IsStaffUser, CanAccessKnowledge]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["type", "status", "owner", "category", "access_level"]
    search_fields = ["title", "summary", "content", "tags"]
    ordering_fields = ["title", "created_at", "updated_at", "published_at"]
    ordering = ["-updated_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return KnowledgeItemDetailSerializer
        return KnowledgeItemSerializer

    def get_queryset(self):
        """
        Filter queryset by role-based access (docs/35 section 4).

        - Admin: see all
        - Manager+: see all except admin_only
        - Staff: see all_staff only
        - Owners always see their own items
        """
        queryset = super().get_queryset()
        user = self.request.user
        role = get_user_role(user, self.request)

        # Admin sees all
        if is_admin(user, self.request):
            return queryset

        # Manager+ sees all except admin_only
        if is_manager_or_above(user, self.request):
            queryset = queryset.exclude(access_level=KnowledgeItem.ACCESS_ADMIN_ONLY)
        else:
            # Staff sees all_staff + their own items
            queryset = queryset.filter(
                models.Q(access_level=KnowledgeItem.ACCESS_ALL_STAFF) | models.Q(owner=user)
            )

        return queryset

    def perform_create(self, serializer):
        """Set firm, created_by, owner on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
            owner=self.request.user,  # Creator is default owner
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        """
        Update knowledge item with immutability check (docs/35 section 2.1).

        Published items cannot be edited; must create new version.
        """
        instance = self.get_object()
        if instance.status == KnowledgeItem.STATUS_PUBLISHED:
            return Response(
                {"error": "Cannot edit published item. Use create_version action instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """
        Publish knowledge item (docs/35 section 3).

        Requires Manager+ role or explicit permission per docs/35 section 4.
        Creates version snapshot and makes item visible per access policy.
        """
        item = self.get_object()

        # Permission check: Manager+ or owner
        if not is_manager_or_above(request.user, request) and item.owner != request.user:
            return Response(
                {"error": "Publishing requires Manager+ role or item ownership"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            item.publish(published_by=request.user)
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def deprecate(self, request, pk=None):
        """
        Deprecate knowledge item (docs/35 section 3).

        Requires Manager+ role per docs/35 section 4.
        Reason required per docs/35 section 3.
        """
        item = self.get_object()

        # Permission check: Manager+ only
        if not is_manager_or_above(request.user, request):
            return Response(
                {"error": "Deprecation requires Manager+ role"},
                status=status.HTTP_403_FORBIDDEN,
            )

        reason = request.data.get("reason")
        if not reason:
            return Response(
                {"error": "Deprecation reason is required (docs/35 section 3)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item.deprecate(deprecated_by=request.user, reason=reason)
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """
        Archive knowledge item (docs/35 section 3).

        Requires Admin role per docs/35 section 4.
        """
        item = self.get_object()

        # Permission check: Admin only
        if not is_admin(request.user, request):
            return Response(
                {"error": "Archiving requires Admin role"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            item.archive(archived_by=request.user)
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_version(self, request, pk=None):
        """
        Create new version of published item (docs/35 section 2.1).

        Published versions are immutable, so changes create new version.
        """
        item = self.get_object()

        # Permission check: Owner or Manager+
        if item.owner != request.user and not is_manager_or_above(request.user, request):
            return Response(
                {"error": "Creating version requires item ownership or Manager+ role"},
                status=status.HTTP_403_FORBIDDEN,
            )

        change_notes = request.data.get("change_notes", "")

        try:
            new_item = item.create_new_version(updated_by=request.user, change_notes=change_notes)
            serializer = self.get_serializer(new_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        """List all versions of this knowledge item."""
        item = self.get_object()
        versions = item.versions.all()
        serializer = KnowledgeVersionSerializer(versions, many=True)
        return Response(serializer.data)


class KnowledgeVersionViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    Knowledge Version history (docs/35 section 2.2).

    Read-only access to version snapshots.
    """

    model = KnowledgeVersion
    serializer_class = KnowledgeVersionSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, CanAccessKnowledge]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["knowledge_item"]
    ordering_fields = ["version_number", "created_at"]
    ordering = ["-version_number"]


class KnowledgeReviewViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    Knowledge Review workflow (docs/35 section 3).

    Allows requesting reviews and recording approval/rejection.
    """

    model = KnowledgeReview
    serializer_class = KnowledgeReviewSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, CanAccessKnowledge]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["knowledge_item", "reviewer", "decision"]
    ordering_fields = ["requested_at", "reviewed_at"]
    ordering = ["-requested_at"]

    def perform_create(self, serializer):
        """Request a review."""
        serializer.save(
            firm=self.request.firm,
            requested_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve this review."""
        review = self.get_object()

        # Only assigned reviewer can approve
        if review.reviewer != request.user:
            return Response(
                {"error": "Only the assigned reviewer can approve"},
                status=status.HTTP_403_FORBIDDEN,
            )

        comments = request.data.get("comments", "")
        review.approve(comments=comments)
        serializer = self.get_serializer(review)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject this review."""
        review = self.get_object()

        # Only assigned reviewer can reject
        if review.reviewer != request.user:
            return Response(
                {"error": "Only the assigned reviewer can reject"},
                status=status.HTTP_403_FORBIDDEN,
            )

        comments = request.data.get("comments")
        if not comments:
            return Response(
                {"error": "Comments required when rejecting"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            review.reject(comments=comments)
            serializer = self.get_serializer(review)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class KnowledgeAttachmentViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    Knowledge Attachments (docs/35 section 2.3).

    Links knowledge items to documents, templates, external resources.
    """

    model = KnowledgeAttachment
    serializer_class = KnowledgeAttachmentSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, CanAccessKnowledge]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["knowledge_item", "attachment_type"]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def perform_create(self, serializer):
        """Create attachment."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )
