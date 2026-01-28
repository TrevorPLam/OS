"""SMS module serializers."""

from rest_framework import serializers
from .models import (
    SMSPhoneNumber,
    SMSTemplate,
    SMSMessage,
    SMSCampaign,
    SMSConversation,
    SMSOptOut,
)


class SMSPhoneNumberSerializer(serializers.ModelSerializer):
    """Serializer for SMSPhoneNumber."""

    usage_summary = serializers.SerializerMethodField()

    class Meta:
        model = SMSPhoneNumber
        fields = [
            'id',
            'phone_number',
            'friendly_name',
            'provider',
            'provider_sid',
            'can_send_sms',
            'can_receive_sms',
            'can_send_mms',
            'status',
            'is_default',
            'messages_sent',
            'messages_received',
            'last_used_at',
            'usage_summary',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'provider_sid',
            'messages_sent',
            'messages_received',
            'last_used_at',
            'usage_summary',
            'created_at',
            'updated_at',
        ]

    def get_usage_summary(self, obj):
        """Get usage summary."""
        return {
            'total_sent': obj.messages_sent,
            'total_received': obj.messages_received,
            'total_messages': obj.messages_sent + obj.messages_received,
        }

    def validate_phone_number(self, value):
        """Validate phone number format (E.164)."""
        if not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +14155552671)"
            )
        if not value[1:].isdigit():
            raise serializers.ValidationError(
                "Phone number must contain only digits after the +"
            )
        if len(value) < 8 or len(value) > 16:
            raise serializers.ValidationError(
                "Phone number length must be between 8 and 16 characters"
            )
        return value


class SMSTemplateSerializer(serializers.ModelSerializer):
    """Serializer for SMSTemplate."""

    variables = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = SMSTemplate
        fields = [
            'id',
            'name',
            'template_type',
            'message',
            'character_count',
            'estimated_segments',
            'variables',
            'times_used',
            'last_used_at',
            'is_active',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'character_count',
            'estimated_segments',
            'variables',
            'times_used',
            'last_used_at',
            'created_by_username',
            'created_at',
            'updated_at',
        ]

    def get_variables(self, obj):
        """Extract variables from template."""
        return obj.extract_variables()

    def validate_message(self, value):
        """Validate message length."""
        if len(value) > 1600:
            raise serializers.ValidationError(
                "Message too long. Maximum 1600 characters (10 SMS segments)."
            )
        return value


class SMSTemplateRenderSerializer(serializers.Serializer):
    """Serializer for rendering SMS template with variables."""

    context_data = serializers.JSONField(
        required=True,
        help_text="Variable values for template rendering"
    )

    def validate_context_data(self, value):
        """Validate context data is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("context_data must be a dictionary")
        return value


class SMSMessageSerializer(serializers.ModelSerializer):
    """Serializer for SMSMessage."""

    from_number_display = serializers.CharField(
        source='from_number.phone_number',
        read_only=True,
        allow_null=True
    )
    campaign_name = serializers.CharField(
        source='campaign.name',
        read_only=True,
        allow_null=True
    )
    sent_by_username = serializers.CharField(
        source='sent_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = SMSMessage
        fields = [
            'id',
            'direction',
            'from_number',
            'from_number_display',
            'to_number',
            'message_body',
            'media_urls',
            'status',
            'error_code',
            'error_message',
            'provider_message_sid',
            'provider_status',
            'price',
            'price_currency',
            'campaign',
            'campaign_name',
            'conversation',
            'contact',
            'lead',
            'sent_at',
            'delivered_at',
            'sent_by',
            'sent_by_username',
            'character_count',
            'segment_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'from_number_display',
            'campaign_name',
            'sent_by_username',
            'status',
            'error_code',
            'error_message',
            'provider_message_sid',
            'provider_status',
            'price',
            'price_currency',
            'sent_at',
            'delivered_at',
            'character_count',
            'segment_count',
            'created_at',
            'updated_at',
        ]

    def validate_to_number(self, value):
        """Validate recipient phone number."""
        if not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +14155552671)"
            )
        return value

    def validate_message_body(self, value):
        """Validate message body length."""
        if len(value) > 1600:
            raise serializers.ValidationError(
                "Message too long. Maximum 1600 characters."
            )
        return value


class SendSMSSerializer(serializers.Serializer):
    """Serializer for sending individual SMS."""

    to_number = serializers.CharField(
        required=True,
        help_text="Recipient phone number (E.164 format)"
    )
    message = serializers.CharField(
        required=True,
        max_length=1600,
        help_text="Message text"
    )
    from_number_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="SMS phone number ID (uses default if not specified)"
    )
    contact_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Contact ID to associate message with"
    )
    lead_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Lead ID to associate message with"
    )

    def validate_to_number(self, value):
        """Validate phone number format."""
        if not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +14155552671)"
            )
        return value


class SMSCampaignSerializer(serializers.ModelSerializer):
    """Serializer for SMSCampaign."""

    template_name = serializers.CharField(
        source='template.name',
        read_only=True,
        allow_null=True
    )
    from_number_display = serializers.CharField(
        source='from_number.phone_number',
        read_only=True,
        allow_null=True
    )
    segment_name = serializers.CharField(
        source='segment.name',
        read_only=True,
        allow_null=True
    )
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True,
        allow_null=True
    )
    analytics = serializers.SerializerMethodField()

    class Meta:
        model = SMSCampaign
        fields = [
            'id',
            'name',
            'description',
            'template',
            'template_name',
            'message_content',
            'from_number',
            'from_number_display',
            'segment',
            'segment_name',
            'recipient_list',
            'scheduled_at',
            'started_at',
            'completed_at',
            'status',
            'recipients_total',
            'messages_sent',
            'messages_delivered',
            'messages_failed',
            'replies_received',
            'opt_outs_received',
            'total_cost',
            'delivery_rate',
            'reply_rate',
            'analytics',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'template_name',
            'from_number_display',
            'segment_name',
            'created_by_username',
            'started_at',
            'completed_at',
            'recipients_total',
            'messages_sent',
            'messages_delivered',
            'messages_failed',
            'replies_received',
            'opt_outs_received',
            'total_cost',
            'delivery_rate',
            'reply_rate',
            'analytics',
            'created_at',
            'updated_at',
        ]

    def get_analytics(self, obj):
        """Get campaign analytics."""
        return {
            'delivery_rate': obj.delivery_rate,
            'reply_rate': obj.reply_rate,
            'opt_out_rate': (
                round((obj.opt_outs_received / obj.messages_delivered) * 100, 2)
                if obj.messages_delivered > 0
                else 0
            ),
        }


class SMSConversationSerializer(serializers.ModelSerializer):
    """Serializer for SMSConversation."""

    our_number_display = serializers.CharField(
        source='our_number.phone_number',
        read_only=True
    )
    contact_name = serializers.CharField(
        source='contact.name',
        read_only=True,
        allow_null=True
    )
    lead_name = serializers.CharField(
        source='lead.company_name',
        read_only=True,
        allow_null=True
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        allow_null=True
    )
    last_message_preview = serializers.SerializerMethodField()

    class Meta:
        model = SMSConversation
        fields = [
            'id',
            'our_number',
            'our_number_display',
            'their_number',
            'contact',
            'contact_name',
            'lead',
            'lead_name',
            'assigned_to',
            'assigned_to_username',
            'status',
            'is_opt_out',
            'message_count',
            'last_message_at',
            'last_message_from_us',
            'last_message_preview',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'our_number_display',
            'contact_name',
            'lead_name',
            'assigned_to_username',
            'message_count',
            'last_message_at',
            'last_message_from_us',
            'last_message_preview',
            'created_at',
            'updated_at',
        ]

    def get_last_message_preview(self, obj):
        """Get preview of last message."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            preview = last_message.message_body[:50]
            if len(last_message.message_body) > 50:
                preview += '...'
            return {
                'preview': preview,
                'from_us': last_message.direction == 'outbound',
                'timestamp': last_message.created_at,
            }
        return None


class ConversationReplySerializer(serializers.Serializer):
    """Serializer for replying to SMS conversation."""

    message = serializers.CharField(
        required=True,
        max_length=1600,
        help_text="Reply message text"
    )


class SMSOptOutSerializer(serializers.ModelSerializer):
    """Serializer for SMSOptOut."""

    contact_name = serializers.CharField(
        source='contact.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = SMSOptOut
        fields = [
            'id',
            'phone_number',
            'opted_out_at',
            'opt_out_message',
            'conversation',
            'contact',
            'contact_name',
        ]
        read_only_fields = [
            'id',
            'opted_out_at',
            'contact_name',
        ]

    def validate_phone_number(self, value):
        """Validate phone number format."""
        if not value.startswith('+'):
            raise serializers.ValidationError(
                "Phone number must be in E.164 format (e.g., +14155552671)"
            )
        return value
