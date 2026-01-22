"""
Communications API Views.

Implements REST API for Conversation, Message, and Participant models per DOC-33.1 and DOC-25.1.

Per docs/03-reference/requirements/DOC-25.md Staff App IA:
- Conversations appear in primary nav "Communications"
- Messages appear in Client 360 "Messages" tab
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone

from modules.auth.role_permissions import IsStaffUser
from .models import Conversation, Message, Participant, MessageAttachment


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Conversation management.

    Per DOC-25.1: Primary navigation "Communications"
    Per DOC-33.1: Conversation thread management with visibility rules

    Permissions:
    - IsStaffUser required (staff app only)
    - Portal users access via participant-scoped queries only
    """

    queryset = Conversation.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["visibility", "status", "primary_object_type", "primary_object_id"]
    ordering_fields = ["created_at", "last_message_at", "message_count"]
    ordering = ["-last_message_at"]
    search_fields = ["subject"]

    def get_queryset(self):
        """Filter by firm context."""
        queryset = self.queryset.filter(firm=self.request.firm).select_related("firm", "created_by")

        # Filter by linked object if specified
        object_type = self.request.query_params.get("object_type")
        object_id = self.request.query_params.get("object_id")
        if object_type and object_id:
            queryset = queryset.filter(
                primary_object_type=object_type,
                primary_object_id=object_id
            )

        return queryset

    def perform_create(self, serializer):
        """Create conversation with firm context."""
        serializer.save(firm=self.request.firm, created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive_conversation(self, request, pk=None):
        """Archive a conversation (staff only)."""
        conversation = self.get_object()

        if conversation.status == "archived":
            return Response(
                {"error": "Conversation is already archived"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation.status = "archived"
        conversation.save()

        return Response(
            {"message": "Conversation archived", "conversation_id": conversation.id},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="unarchive")
    def unarchive_conversation(self, request, pk=None):
        """Unarchive a conversation (staff only)."""
        conversation = self.get_object()

        if conversation.status == "active":
            return Response(
                {"error": "Conversation is already active"},
                status=status.HTTP_400_BAD_REQUEST
            )

        conversation.status = "active"
        conversation.save()

        return Response(
            {"message": "Conversation unarchived", "conversation_id": conversation.id},
            status=status.HTTP_200_OK
        )


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message management within Conversations.

    Per DOC-25.1: Client 360 "Messages" tab
    Per DOC-33.1: Message CRUD with edit history preservation
    """

    queryset = Message.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["conversation", "message_type", "sender"]
    ordering_fields = ["created_at", "edited_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        """Filter by firm context and conversation."""
        queryset = self.queryset.filter(
            conversation__firm=self.request.firm
        ).select_related("conversation", "sender")

        # Filter by conversation if specified
        conversation_id = self.request.query_params.get("conversation_id")
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        return queryset

    def perform_create(self, serializer):
        """Create message and update conversation metadata."""
        message = serializer.save(sender=self.request.user)

        # Update conversation last_message_at and message_count
        conversation = message.conversation
        conversation.last_message_at = message.created_at
        conversation.message_count = conversation.messages.count()
        conversation.save()

    @action(detail=True, methods=["post"], url_path="edit")
    def edit_message(self, request, pk=None):
        """
        Edit a message (creates MessageRevision for history).

        Per DOC-33.1: Edit history is preserved via MessageRevision
        """
        message = self.get_object()

        # Only sender can edit
        if message.sender != request.user:
            return Response(
                {"error": "Only the sender can edit this message"},
                status=status.HTTP_403_FORBIDDEN
            )

        # System messages cannot be edited
        if message.message_type == "system_event":
            return Response(
                {"error": "System messages cannot be edited"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_body = request.data.get("body")
        if not new_body:
            return Response(
                {"error": "New message body is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create revision before editing
        from .models import MessageRevision
        MessageRevision.objects.create(
            message=message,
            body=message.body,  # Store old body
            edited_at=message.edited_at or message.created_at,
            edited_by=message.sender,
        )

        # Update message
        message.body = new_body
        message.edited_at = timezone.now()
        message.save()

        return Response(
            {"message": "Message edited", "message_id": message.id},
            status=status.HTTP_200_OK
        )


class ParticipantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Participant management in Conversations.

    Per DOC-33.1: Staff and portal user participants
    """

    queryset = Participant.objects.all()
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["conversation", "user", "participant_type"]
    ordering_fields = ["joined_at"]
    ordering = ["joined_at"]

    def get_queryset(self):
        """Filter by firm context and conversation."""
        queryset = self.queryset.filter(
            conversation__firm=self.request.firm
        ).select_related("conversation", "user")

        # Filter by conversation if specified
        conversation_id = self.request.query_params.get("conversation_id")
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        return queryset

    def perform_create(self, serializer):
        """Add participant to conversation."""
        participant = serializer.save()

        # If adding a portal user, ensure conversation is client_visible
        if participant.participant_type == "portal":
            conversation = participant.conversation
            if conversation.visibility == "internal_only":
                # Auto-upgrade to client_visible when portal user is added
                conversation.visibility = "client_visible"
                conversation.save()
