"""
Models for SMS module.

SMS messaging capabilities including:
- Phone number management and validation
- SMS campaigns and bulk messaging
- SMS templates with variables
- Two-way SMS conversations
- Delivery tracking and analytics
- Integration with workflows and automation
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager
import re


# Phone number validator (E.164 format)
phone_validator = RegexValidator(
    regex=r'^\+[1-9]\d{1,14}$',
    message='Phone number must be in E.164 format (e.g., +14155552671)'
)


class SMSPhoneNumber(models.Model):
    """
    SMS-enabled phone number (Twilio phone number).

    Represents a phone number purchased/configured in Twilio
    that can send and receive SMS messages.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending_verification', 'Pending Verification'),
        ('suspended', 'Suspended'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='sms_phone_numbers',
        help_text='Firm this phone number belongs to'
    )

    # Phone Number
    phone_number = models.CharField(
        max_length=20,
        validators=[phone_validator],
        help_text='Phone number in E.164 format (e.g., +14155552671)'
    )
    friendly_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Friendly name for this number (e.g., "Main Support Line")'
    )

    # Provider Details
    provider = models.CharField(
        max_length=20,
        default='twilio',
        help_text='SMS provider (twilio, etc.)'
    )
    provider_sid = models.CharField(
        max_length=100,
        blank=True,
        help_text='Provider-specific identifier (Twilio SID)'
    )

    # Capabilities
    can_send_sms = models.BooleanField(
        default=True,
        help_text='Whether this number can send SMS'
    )
    can_receive_sms = models.BooleanField(
        default=True,
        help_text='Whether this number can receive SMS'
    )
    can_send_mms = models.BooleanField(
        default=False,
        help_text='Whether this number can send MMS (images)'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending_verification',
        help_text='Phone number status'
    )
    is_default = models.BooleanField(
        default=False,
        help_text='Whether this is the default number for the firm'
    )

    # Usage Tracking
    messages_sent = models.IntegerField(
        default=0,
        help_text='Total messages sent from this number'
    )
    messages_received = models.IntegerField(
        default=0,
        help_text='Total messages received by this number'
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this number was last used'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'sms_phone_numbers'
        ordering = ['-is_default', 'phone_number']
        indexes = [
            models.Index(fields=['firm', 'status'], name="sms_phone_fir_sta_idx"),
            models.Index(fields=['firm', 'is_default'], name="sms_phone_fir_is__idx"),
            models.Index(fields=['phone_number'], name="sms_phone_pho_idx"),
        ]
        unique_together = [('firm', 'phone_number')]

    def __str__(self):
        if self.friendly_name:
            return f"{self.friendly_name} ({self.phone_number})"
        return self.phone_number

    def clean(self):
        """Validate phone number."""
        super().clean()

        # Ensure only one default per firm
        if self.is_default:
            existing = SMSPhoneNumber.objects.filter(
                firm=self.firm,
                is_default=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({
                    'is_default': 'Firm already has a default phone number. Unset the existing default first.'
                })


class SMSTemplate(models.Model):
    """
    SMS message template.

    Reusable SMS templates with variable support for campaigns and workflows.
    """

    TEMPLATE_TYPE_CHOICES = [
        ('campaign', 'Campaign'),
        ('notification', 'Notification'),
        ('reminder', 'Reminder'),
        ('confirmation', 'Confirmation'),
        ('alert', 'Alert'),
        ('custom', 'Custom'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='sms_templates',
        help_text='Firm this template belongs to'
    )

    # Template Definition
    name = models.CharField(
        max_length=255,
        help_text='Template name'
    )
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        help_text='Template type'
    )
    message = models.TextField(
        max_length=1600,  # SMS limit is 160 chars, but allow up to 10 segments
        help_text='Message content with variables ({{contact_name}}, {{company_name}}, etc.)'
    )

    # Metadata
    character_count = models.IntegerField(
        default=0,
        help_text='Character count (without variable replacement)'
    )
    estimated_segments = models.IntegerField(
        default=1,
        help_text='Estimated SMS segments (160 chars per segment)'
    )
    times_used = models.IntegerField(
        default=0,
        help_text='Number of times this template has been used'
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this template was last used'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this template is active'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sms_templates',
        help_text='User who created this template'
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'sms_templates'
        ordering = ['name']
        indexes = [
            models.Index(fields=['firm', 'template_type'], name="sms_fir_tem_idx"),
            models.Index(fields=['firm', 'is_active'], name="sms_template_fir_is__idx"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Calculate character count on save."""
        self.character_count = len(self.message)
        self.estimated_segments = max(1, (self.character_count + 159) // 160)
        super().save(*args, **kwargs)

    def extract_variables(self):
        """Extract all variables from template."""
        return re.findall(r'\{\{(\w+)\}\}', self.message)

    def render(self, context_data):
        """
        Render template with actual values.

        Args:
            context_data (dict): Variable values

        Returns:
            str: Rendered message
        """
        rendered = self.message
        for key, value in context_data.items():
            placeholder = '{{' + key + '}}'
            rendered = rendered.replace(placeholder, str(value or ''))
        return rendered


class SMSMessage(models.Model):
    """
    Individual SMS message.

    Tracks sent and received SMS messages with delivery status.
    """

    DIRECTION_CHOICES = [
        ('outbound', 'Outbound (Sent)'),
        ('inbound', 'Inbound (Received)'),
    ]

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('undelivered', 'Undelivered'),
        ('received', 'Received'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='sms_messages',
        help_text='Firm this message belongs to'
    )

    # Phone Numbers
    from_number = models.ForeignKey(
        SMSPhoneNumber,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
        help_text='Phone number message was sent from (our number)'
    )
    to_number = models.CharField(
        max_length=20,
        validators=[phone_validator],
        help_text='Recipient phone number in E.164 format'
    )

    # Message Details
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        help_text='Message direction'
    )
    message_body = models.TextField(
        help_text='Message content'
    )
    media_urls = models.JSONField(
        default=list,
        blank=True,
        help_text='URLs of attached media (MMS)'
    )

    # Status & Delivery
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='queued',
        help_text='Message status'
    )
    error_code = models.CharField(
        max_length=20,
        blank=True,
        help_text='Error code if failed'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if failed'
    )

    # Provider Details
    provider_message_sid = models.CharField(
        max_length=100,
        blank=True,
        help_text='Provider message ID (Twilio SID)'
    )
    provider_status = models.CharField(
        max_length=50,
        blank=True,
        help_text='Provider-specific status'
    )

    # Cost Tracking
    price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Cost per message (in provider currency)'
    )
    price_currency = models.CharField(
        max_length=3,
        default='USD',
        help_text='Currency code (USD, EUR, etc.)'
    )

    # Related Objects
    campaign = models.ForeignKey(
        'SMSCampaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text='Campaign this message belongs to'
    )
    conversation = models.ForeignKey(
        'SMSConversation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        help_text='Conversation this message belongs to'
    )
    contact = models.ForeignKey(
        'clients.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_messages',
        help_text='Contact associated with this message'
    )
    lead = models.ForeignKey(
        'crm.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_messages',
        help_text='Lead associated with this message'
    )

    # Timing
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When message was sent'
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When message was delivered'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Sender
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_sms_messages',
        help_text='User who sent this message (null if automated)'
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'sms_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', '-created_at'], name="sms_message_fir_cre_idx"),
            models.Index(fields=['firm', 'to_number', '-created_at'], name="sms_fir_to__cre_idx"),
            models.Index(fields=['campaign', '-created_at'], name="sms_cam_cre_idx"),
            models.Index(fields=['conversation', '-created_at'], name="sms_con_cre_idx"),
            models.Index(fields=['status'], name="sms_sta_idx"),
            models.Index(fields=['provider_message_sid'], name="sms_pro_idx"),
        ]

    def __str__(self):
        return f"{self.direction.title()} SMS to {self.to_number}: {self.message_body[:50]}"

    @property
    def character_count(self):
        """Get character count of message."""
        return len(self.message_body)

    @property
    def segment_count(self):
        """Calculate number of SMS segments."""
        return max(1, (self.character_count + 159) // 160)


class SMSCampaign(models.Model):
    """
    SMS campaign for bulk messaging.

    Manages bulk SMS sends with scheduling, segmentation, and analytics.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='sms_campaigns',
        help_text='Firm this campaign belongs to'
    )

    # Campaign Definition
    name = models.CharField(
        max_length=255,
        help_text='Campaign name'
    )
    description = models.TextField(
        blank=True,
        help_text='Campaign description'
    )
    template = models.ForeignKey(
        SMSTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        help_text='SMS template used'
    )
    message_content = models.TextField(
        help_text='Message content (copied from template or custom)'
    )

    # Sending Configuration
    from_number = models.ForeignKey(
        SMSPhoneNumber,
        on_delete=models.SET_NULL,
        null=True,
        related_name='campaigns',
        help_text='Phone number to send from'
    )
    segment = models.ForeignKey(
        'marketing.Segment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_campaigns',
        help_text='Segment to send to (or manual list)'
    )
    recipient_list = models.JSONField(
        default=list,
        blank=True,
        help_text='Manual list of phone numbers if not using segment'
    )

    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When to send campaign (null = send immediately)'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When campaign sending started'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When campaign sending completed'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Campaign status'
    )

    # Analytics
    recipients_total = models.IntegerField(
        default=0,
        help_text='Total number of recipients'
    )
    messages_sent = models.IntegerField(
        default=0,
        help_text='Messages successfully sent'
    )
    messages_delivered = models.IntegerField(
        default=0,
        help_text='Messages confirmed delivered'
    )
    messages_failed = models.IntegerField(
        default=0,
        help_text='Messages that failed to send'
    )
    replies_received = models.IntegerField(
        default=0,
        help_text='Replies received'
    )
    opt_outs_received = models.IntegerField(
        default=0,
        help_text='Opt-outs received (STOP, UNSUBSCRIBE, etc.)'
    )

    # Cost
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Total cost of campaign'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sms_campaigns',
        help_text='User who created this campaign'
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'sms_campaigns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'status'], name="sms_campaign_fir_sta_idx"),
            models.Index(fields=['firm', '-created_at'], name="sms_campaign_fir_cre_idx"),
            models.Index(fields=['scheduled_at'], name="sms_sch_idx"),
        ]

    def __str__(self):
        return self.name

    @property
    def delivery_rate(self):
        """Calculate delivery rate."""
        if self.messages_sent == 0:
            return 0
        return round((self.messages_delivered / self.messages_sent) * 100, 2)

    @property
    def reply_rate(self):
        """Calculate reply rate."""
        if self.messages_delivered == 0:
            return 0
        return round((self.replies_received / self.messages_delivered) * 100, 2)


class SMSConversation(models.Model):
    """
    Two-way SMS conversation thread.

    Groups SMS messages by phone number for threaded conversations.
    """

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='sms_conversations',
        help_text='Firm this conversation belongs to'
    )

    # Participants
    our_number = models.ForeignKey(
        SMSPhoneNumber,
        on_delete=models.CASCADE,
        related_name='conversations',
        help_text='Our phone number in this conversation'
    )
    their_number = models.CharField(
        max_length=20,
        validators=[phone_validator],
        help_text='Their phone number'
    )

    # Related Objects
    contact = models.ForeignKey(
        'clients.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_conversations',
        help_text='Associated contact'
    )
    lead = models.ForeignKey(
        'crm.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_conversations',
        help_text='Associated lead'
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sms_conversations',
        help_text='User assigned to this conversation'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Conversation status'
    )
    is_opt_out = models.BooleanField(
        default=False,
        help_text='Whether contact has opted out of SMS'
    )

    # Metadata
    message_count = models.IntegerField(
        default=0,
        help_text='Total message count in conversation'
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When last message was sent/received'
    )
    last_message_from_us = models.BooleanField(
        default=False,
        help_text='Whether last message was from us (vs. from them)'
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'sms_conversations'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['firm', 'status', '-last_message_at'], name="sms_fir_sta_las_idx"),
            models.Index(fields=['firm', 'our_number', 'their_number'], name="sms_fir_our_the_idx"),
            models.Index(fields=['assigned_to', 'status'], name="sms_ass_sta_idx"),
        ]
        unique_together = [('firm', 'our_number', 'their_number')]

    def __str__(self):
        return f"SMS with {self.their_number}"


class SMSOptOut(models.Model):
    """
    SMS opt-out record.

    Tracks phone numbers that have opted out of SMS communication.
    """

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='sms_opt_outs',
        help_text='Firm this opt-out belongs to'
    )

    phone_number = models.CharField(
        max_length=20,
        validators=[phone_validator],
        help_text='Phone number that opted out'
    )

    # Opt-out Details
    opted_out_at = models.DateTimeField(auto_now_add=True)
    opt_out_message = models.TextField(
        blank=True,
        help_text='The message they sent to opt out (STOP, UNSUBSCRIBE, etc.)'
    )
    conversation = models.ForeignKey(
        SMSConversation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opt_outs',
        help_text='Conversation where opt-out occurred'
    )

    # Related Objects
    contact = models.ForeignKey(
        'clients.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_opt_outs',
        help_text='Associated contact'
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'sms_opt_outs'
        ordering = ['-opted_out_at']
        indexes = [
            models.Index(fields=['firm', 'phone_number'], name="sms_fir_pho_idx"),
            models.Index(fields=['phone_number'], name="sms_optout_pho_idx"),
        ]
        unique_together = [('firm', 'phone_number')]

    def __str__(self):
        return f"Opt-out: {self.phone_number}"
