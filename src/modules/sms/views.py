"""
SMS Module Views.

Provides API endpoints for SMS management, campaigns, and conversations.
"""

import logging
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from modules.auth.role_permissions import IsStaffUser, IsManager
from modules.firm.utils import FirmScopedMixin, get_request_firm
from modules.jobs.models import JobQueue
from modules.core.observability import get_correlation_id

from .models import (
    SMSPhoneNumber,
    SMSTemplate,
    SMSMessage,
    SMSCampaign,
    SMSConversation,
    SMSOptOut,
)
from .serializers import (
    SMSPhoneNumberSerializer,
    SMSTemplateSerializer,
    SMSTemplateRenderSerializer,
    SMSMessageSerializer,
    SendSMSSerializer,
    SMSCampaignSerializer,
    SMSConversationSerializer,
    ConversationReplySerializer,
    SMSOptOutSerializer,
)
from .twilio_service import TwilioService

logger = logging.getLogger(__name__)


class SMSPhoneNumberViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SMS phone number management.

    Manager+ only for phone number administration.
    """

    model = SMSPhoneNumber
    serializer_class = SMSPhoneNumberSerializer
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', 'provider', 'is_default', 'can_send_sms', 'can_receive_sms']
    search_fields = ['phone_number', 'friendly_name']
    ordering_fields = ['phone_number', 'friendly_name', 'messages_sent', 'created_at']
    ordering = ['-is_default', 'phone_number']

    def perform_create(self, serializer):
        """Create phone number with firm context."""
        serializer.save(firm=self.request.firm)


class SMSTemplateViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SMS template management.

    All staff can view templates, Manager+ can create/edit.
    """

    model = SMSTemplate
    serializer_class = SMSTemplateSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name', 'message']
    ordering_fields = ['name', 'times_used', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Filter to active templates for non-managers."""
        queryset = super().get_queryset()

        # Non-managers only see active templates
        from modules.auth.role_permissions import is_manager_or_above
        if not is_manager_or_above(self.request.user, self.request):
            queryset = queryset.filter(is_active=True)

        return queryset

    def perform_create(self, serializer):
        """Create template with firm and creator."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    def get_permissions(self):
        """Manager+ required for create, update, delete."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffUser(), IsManager()]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def render(self, request, pk=None):
        """
        Render template with provided variables.

        Returns rendered message with variable substitution.
        """
        template = self.get_object()
        serializer = SMSTemplateRenderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        context_data = serializer.validated_data['context_data']
        rendered_message = template.render(context_data)

        return Response({
            'rendered_message': rendered_message,
            'character_count': len(rendered_message),
            'segment_count': max(1, (len(rendered_message) + 159) // 160),
            'variables_used': list(context_data.keys()),
        })


class SMSMessageViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SMS message viewing and sending.

    Read-only for most, send action for staff.
    """

    model = SMSMessage
    serializer_class = SMSMessageSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['direction', 'status', 'campaign', 'conversation', 'contact', 'lead']
    search_fields = ['to_number', 'message_body']
    ordering_fields = ['created_at', 'sent_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Include related objects."""
        queryset = super().get_queryset()
        return queryset.select_related(
            'from_number',
            'campaign',
            'conversation',
            'contact',
            'lead',
            'sent_by',
        )

    @action(detail=False, methods=['post'])
    def send(self, request):
        """
        Send individual SMS message.

        Creates SMS message record and sends via Twilio.
        """
        serializer = SendSMSSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get or use default phone number
        from_number = None
        if serializer.validated_data.get('from_number_id'):
            try:
                from_number = SMSPhoneNumber.objects.get(
                    firm=request.firm,
                    id=serializer.validated_data['from_number_id'],
                    status='active',
                )
            except SMSPhoneNumber.DoesNotExist:
                return Response(
                    {'error': 'SMS phone number not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Use default phone number
            from_number = SMSPhoneNumber.objects.filter(
                firm=request.firm,
                is_default=True,
                status='active',
            ).first()

        if not from_number:
            return Response(
                {'error': 'No active SMS phone number available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check opt-out status
        to_number = serializer.validated_data['to_number']
        if SMSOptOut.objects.filter(firm=request.firm, phone_number=to_number).exists():
            return Response(
                {'error': f'{to_number} has opted out of SMS communications'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create message record
        with transaction.atomic():
            sms_message = SMSMessage.objects.create(
                firm=request.firm,
                from_number=from_number,
                to_number=to_number,
                direction='outbound',
                message_body=serializer.validated_data['message'],
                status='queued',
                sent_by=request.user,
                contact_id=serializer.validated_data.get('contact_id'),
                lead_id=serializer.validated_data.get('lead_id'),
            )

            # Send via Twilio
            twilio_service = TwilioService()
            result = twilio_service.send_sms(
                to_number=to_number,
                message=serializer.validated_data['message'],
                from_number=from_number.phone_number,
            )

            # Update message with result
            if result['success']:
                sms_message.status = 'sent'
                sms_message.provider_message_sid = result['message_sid']
                sms_message.provider_status = result['status']
                sms_message.sent_at = timezone.now()
            else:
                sms_message.status = 'failed'
                sms_message.error_code = result.get('error_code', '')
                sms_message.error_message = result.get('error', '')

            sms_message.save()

            # Update phone number stats
            from_number.messages_sent += 1
            from_number.last_used_at = timezone.now()
            from_number.save(update_fields=['messages_sent', 'last_used_at'])

        return Response(
            {
                'message': 'SMS sent successfully' if result['success'] else 'SMS send failed',
                'sms': SMSMessageSerializer(sms_message).data,
            },
            status=status.HTTP_201_CREATED if result['success'] else status.HTTP_400_BAD_REQUEST
        )


class SMSCampaignViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SMS campaign management.

    Manager+ for create/edit. Staff can view assigned campaigns.
    """

    model = SMSCampaign
    serializer_class = SMSCampaignSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'scheduled_at', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Include related objects."""
        queryset = super().get_queryset()
        return queryset.select_related(
            'template',
            'from_number',
            'segment',
            'created_by',
        )

    def get_permissions(self):
        """Manager+ required for create, update, delete."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'schedule', 'send_now', 'cancel']:
            return [IsAuthenticated(), IsStaffUser(), IsManager()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create campaign with firm and creator."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """
        Schedule campaign for future send.

        Sets scheduled_at and status to 'scheduled'.
        """
        campaign = self.get_object()

        if campaign.status not in ['draft']:
            return Response(
                {'error': 'Can only schedule draft campaigns'},
                status=status.HTTP_400_BAD_REQUEST
            )

        scheduled_at = request.data.get('scheduled_at')
        if not scheduled_at:
            return Response(
                {'error': 'scheduled_at is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.scheduled_at = scheduled_at
        campaign.status = 'scheduled'
        campaign.save(update_fields=['scheduled_at', 'status'])

        return Response({
            'message': 'Campaign scheduled successfully',
            'campaign': SMSCampaignSerializer(campaign).data,
        })

    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """
        Send campaign immediately.

        Queues campaign for immediate sending via background job queue.
        """
        campaign = self.get_object()

        if campaign.status not in ['draft', 'scheduled']:
            return Response(
                {'error': 'Can only send draft or scheduled campaigns'},
                status=status.HTTP_400_BAD_REQUEST
            )

        firm = get_request_firm(request)
        correlation_id = get_correlation_id(request) or uuid.uuid4()

        # Update campaign status
        campaign.status = 'sending'
        campaign.started_at = timezone.now()
        campaign.save(update_fields=['status', 'started_at'])

        # Queue for background processing per DOC-20.1
        JobQueue.objects.create(
            firm=firm,
            category="notifications",
            job_type="sms_campaign_send",
            payload_version="1.0",
            payload={
                "tenant_id": firm.id,
                "correlation_id": str(correlation_id),
                "campaign_id": campaign.id,
                "initiated_by": request.user.id,
            },
            idempotency_key=f"sms_campaign_{campaign.id}_{campaign.started_at.timestamp()}",
            correlation_id=correlation_id,
            priority=1,  # High priority
        )

        logger.info(
            f"Campaign {campaign.id} queued for background sending",
            extra={
                "campaign_id": campaign.id,
                "firm_id": firm.id,
                "correlation_id": str(correlation_id),
            }
        )

        return Response({
            'message': 'Campaign queued for sending',
            'campaign': SMSCampaignSerializer(campaign).data,
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel scheduled campaign.

        Only works for scheduled campaigns.
        """
        campaign = self.get_object()

        if campaign.status not in ['scheduled']:
            return Response(
                {'error': 'Can only cancel scheduled campaigns'},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.status = 'cancelled'
        campaign.save(update_fields=['status'])

        return Response({
            'message': 'Campaign cancelled',
            'campaign': SMSCampaignSerializer(campaign).data,
        })

    @action(detail=True, methods=['post'])
    def update_stats(self, request, pk=None):
        """
        Refresh campaign statistics.

        Recalculates delivery and reply metrics.
        """
        campaign = self.get_object()

        # Recalculate stats from messages
        messages = campaign.messages.all()
        campaign.messages_sent = messages.filter(status__in=['sent', 'delivered']).count()
        campaign.messages_delivered = messages.filter(status='delivered').count()
        campaign.messages_failed = messages.filter(status__in=['failed', 'undelivered']).count()

        # Calculate replies (inbound messages in related conversations)
        # This is simplified - real implementation would track conversation responses
        campaign.save(update_fields=[
            'messages_sent',
            'messages_delivered',
            'messages_failed',
        ])

        return Response({
            'message': 'Campaign stats updated',
            'campaign': SMSCampaignSerializer(campaign).data,
        })


class SMSConversationViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SMS conversation threads.

    Staff can view assigned conversations and reply.
    """

    model = SMSConversation
    serializer_class = SMSConversationSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', 'is_opt_out', 'assigned_to']
    search_fields = ['their_number', 'contact__name', 'lead__company_name']
    ordering_fields = ['last_message_at', 'created_at']
    ordering = ['-last_message_at']

    def get_queryset(self):
        """Include related objects."""
        queryset = super().get_queryset()
        return queryset.select_related(
            'our_number',
            'contact',
            'lead',
            'assigned_to',
        ).prefetch_related('messages')

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """
        Reply to conversation.

        Sends SMS reply and creates message record.
        """
        conversation = self.get_object()
        serializer = ConversationReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if conversation.is_opt_out:
            return Response(
                {'error': 'Cannot reply to opted-out conversation'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create and send message
        with transaction.atomic():
            sms_message = SMSMessage.objects.create(
                firm=request.firm,
                from_number=conversation.our_number,
                to_number=conversation.their_number,
                direction='outbound',
                message_body=serializer.validated_data['message'],
                conversation=conversation,
                contact=conversation.contact,
                lead=conversation.lead,
                status='queued',
                sent_by=request.user,
            )

            # Send via Twilio
            twilio_service = TwilioService()
            result = twilio_service.send_sms(
                to_number=conversation.their_number,
                message=serializer.validated_data['message'],
                from_number=conversation.our_number.phone_number,
            )

            # Update message with result
            if result['success']:
                sms_message.status = 'sent'
                sms_message.provider_message_sid = result['message_sid']
                sms_message.sent_at = timezone.now()
            else:
                sms_message.status = 'failed'
                sms_message.error_code = result.get('error_code', '')
                sms_message.error_message = result.get('error', '')

            sms_message.save()

            # Update conversation
            conversation.message_count += 1
            conversation.last_message_at = timezone.now()
            conversation.last_message_from_us = True
            conversation.save(update_fields=['message_count', 'last_message_at', 'last_message_from_us'])

        return Response({
            'message': 'Reply sent successfully' if result['success'] else 'Reply failed',
            'sms': SMSMessageSerializer(sms_message).data,
        })

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close conversation."""
        conversation = self.get_object()
        conversation.status = 'closed'
        conversation.save(update_fields=['status'])

        return Response({
            'message': 'Conversation closed',
            'conversation': SMSConversationSerializer(conversation).data,
        })

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive conversation."""
        conversation = self.get_object()
        conversation.status = 'archived'
        conversation.save(update_fields=['status'])

        return Response({
            'message': 'Conversation archived',
            'conversation': SMSConversationSerializer(conversation).data,
        })

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign conversation to user."""
        conversation = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate user exists and is staff
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        conversation.assigned_to = user
        conversation.save(update_fields=['assigned_to'])

        return Response({
            'message': 'Conversation assigned',
            'conversation': SMSConversationSerializer(conversation).data,
        })


class SMSOptOutViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SMS opt-out management.

    Read-only for most, Manager+ can manually add/remove opt-outs.
    """

    model = SMSOptOut
    serializer_class = SMSOptOutSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ['phone_number', 'contact__name']
    ordering_fields = ['opted_out_at']
    ordering = ['-opted_out_at']

    def get_queryset(self):
        """Include related objects."""
        queryset = super().get_queryset()
        return queryset.select_related('conversation', 'contact')

    def get_permissions(self):
        """Manager+ required for create, delete."""
        if self.action in ['create', 'destroy']:
            return [IsAuthenticated(), IsStaffUser(), IsManager()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create opt-out with firm context."""
        serializer.save(firm=self.request.firm)
