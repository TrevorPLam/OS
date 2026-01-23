"""Admin configuration for SMS module."""

from django.contrib import admin
from .models import (
    SMSPhoneNumber,
    SMSTemplate,
    SMSMessage,
    SMSCampaign,
    SMSConversation,
    SMSOptOut,
)


@admin.register(SMSPhoneNumber)
class SMSPhoneNumberAdmin(admin.ModelAdmin):
    """Admin for SMSPhoneNumber."""

    list_display = [
        'phone_number',
        'friendly_name',
        'provider',
        'status',
        'is_default',
        'messages_sent',
        'messages_received',
        'firm',
        'created_at',
    ]
    list_filter = ['status', 'provider', 'is_default', 'firm', 'can_send_sms', 'can_receive_sms']
    search_fields = ['phone_number', 'friendly_name', 'provider_sid']
    readonly_fields = ['created_at', 'updated_at', 'last_used_at', 'messages_sent', 'messages_received']

    fieldsets = (
        (None, {
            'fields': ('firm', 'phone_number', 'friendly_name')
        }),
        ('Provider Details', {
            'fields': ('provider', 'provider_sid')
        }),
        ('Capabilities', {
            'fields': ('can_send_sms', 'can_receive_sms', 'can_send_mms')
        }),
        ('Status', {
            'fields': ('status', 'is_default')
        }),
        ('Usage Statistics', {
            'fields': ('messages_sent', 'messages_received', 'last_used_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    """Admin for SMSTemplate."""

    list_display = [
        'name',
        'template_type',
        'character_count',
        'estimated_segments',
        'times_used',
        'is_active',
        'firm',
        'created_by',
        'created_at',
    ]
    list_filter = ['template_type', 'is_active', 'firm', 'created_at']
    search_fields = ['name', 'message']
    readonly_fields = ['character_count', 'estimated_segments', 'times_used', 'last_used_at', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('firm', 'name', 'template_type', 'is_active')
        }),
        ('Message Content', {
            'fields': ('message',),
            'description': 'Use {{variable_name}} for template variables'
        }),
        ('Statistics', {
            'fields': ('character_count', 'estimated_segments', 'times_used', 'last_used_at')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    """Admin for SMSMessage."""

    list_display = [
        'id',
        'direction',
        'from_number_display',
        'to_number',
        'status',
        'message_preview',
        'campaign',
        'conversation',
        'sent_at',
        'firm',
    ]
    list_filter = ['direction', 'status', 'firm', 'created_at', 'sent_at']
    search_fields = ['to_number', 'message_body', 'provider_message_sid']
    readonly_fields = [
        'created_at',
        'updated_at',
        'sent_at',
        'delivered_at',
        'provider_message_sid',
        'provider_status',
        'character_count',
        'segment_count',
    ]
    raw_id_fields = ['from_number', 'campaign', 'conversation', 'contact', 'lead', 'sent_by']

    fieldsets = (
        (None, {
            'fields': ('firm', 'direction', 'from_number', 'to_number')
        }),
        ('Message Content', {
            'fields': ('message_body', 'media_urls')
        }),
        ('Status', {
            'fields': ('status', 'error_code', 'error_message')
        }),
        ('Provider Details', {
            'fields': ('provider_message_sid', 'provider_status'),
            'classes': ('collapse',)
        }),
        ('Cost', {
            'fields': ('price', 'price_currency'),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('campaign', 'conversation', 'contact', 'lead'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('sent_at', 'delivered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('sent_by', 'character_count', 'segment_count'),
            'classes': ('collapse',)
        }),
    )

    def from_number_display(self, obj):
        """Display from number with friendly name."""
        if obj.from_number:
            return str(obj.from_number)
        return '-'
    from_number_display.short_description = 'From'

    def message_preview(self, obj):
        """Show message preview."""
        return obj.message_body[:50] + '...' if len(obj.message_body) > 50 else obj.message_body
    message_preview.short_description = 'Message'


@admin.register(SMSCampaign)
class SMSCampaignAdmin(admin.ModelAdmin):
    """Admin for SMSCampaign."""

    list_display = [
        'name',
        'status',
        'from_number',
        'recipients_total',
        'messages_sent',
        'messages_delivered',
        'delivery_rate_display',
        'scheduled_at',
        'firm',
        'created_by',
    ]
    list_filter = ['status', 'firm', 'created_at', 'scheduled_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'created_at',
        'updated_at',
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
    ]
    raw_id_fields = ['template', 'from_number', 'segment', 'created_by']

    fieldsets = (
        (None, {
            'fields': ('firm', 'name', 'description', 'status')
        }),
        ('Message Configuration', {
            'fields': ('template', 'message_content', 'from_number')
        }),
        ('Recipients', {
            'fields': ('segment', 'recipient_list')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'started_at', 'completed_at')
        }),
        ('Analytics', {
            'fields': (
                'recipients_total',
                'messages_sent',
                'messages_delivered',
                'messages_failed',
                'delivery_rate',
                'replies_received',
                'reply_rate',
                'opt_outs_received',
                'total_cost',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def delivery_rate_display(self, obj):
        """Display delivery rate as percentage."""
        return f"{obj.delivery_rate}%"
    delivery_rate_display.short_description = 'Delivery Rate'

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SMSConversation)
class SMSConversationAdmin(admin.ModelAdmin):
    """Admin for SMSConversation."""

    list_display = [
        'id',
        'our_number',
        'their_number',
        'status',
        'message_count',
        'last_message_at',
        'assigned_to',
        'is_opt_out',
        'firm',
    ]
    list_filter = ['status', 'is_opt_out', 'firm', 'created_at']
    search_fields = ['their_number', 'contact__name', 'lead__company_name']
    readonly_fields = ['created_at', 'updated_at', 'message_count', 'last_message_at', 'last_message_from_us']
    raw_id_fields = ['our_number', 'contact', 'lead', 'assigned_to']

    fieldsets = (
        (None, {
            'fields': ('firm', 'our_number', 'their_number', 'status')
        }),
        ('Relationships', {
            'fields': ('contact', 'lead'),
            'classes': ('collapse',)
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Statistics', {
            'fields': ('message_count', 'last_message_at', 'last_message_from_us', 'is_opt_out'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SMSOptOut)
class SMSOptOutAdmin(admin.ModelAdmin):
    """Admin for SMSOptOut."""

    list_display = [
        'phone_number',
        'opted_out_at',
        'opt_out_message_preview',
        'contact',
        'firm',
    ]
    list_filter = ['firm', 'opted_out_at']
    search_fields = ['phone_number', 'opt_out_message', 'contact__name']
    readonly_fields = ['opted_out_at']
    raw_id_fields = ['conversation', 'contact']

    fieldsets = (
        (None, {
            'fields': ('firm', 'phone_number')
        }),
        ('Opt-out Details', {
            'fields': ('opted_out_at', 'opt_out_message', 'conversation')
        }),
        ('Relationships', {
            'fields': ('contact',),
            'classes': ('collapse',)
        }),
    )

    def opt_out_message_preview(self, obj):
        """Show opt-out message preview."""
        if obj.opt_out_message:
            return obj.opt_out_message[:50] + '...' if len(obj.opt_out_message) > 50 else obj.opt_out_message
        return '-'
    opt_out_message_preview.short_description = 'Opt-out Message'
