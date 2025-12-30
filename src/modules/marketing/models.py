"""
Marketing Models: EmailTemplate, Tag, Segment, CampaignExecution.

Implements ActiveCampaign/HubSpot-like marketing automation features:
- Email campaign templates
- Tag-based organization
- Dynamic segmentation
- Campaign execution tracking

TIER 0: All marketing entities MUST belong to exactly one Firm for tenant isolation.
"""

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class Tag(models.Model):
    """
    Tag for categorizing and segmenting leads, prospects, clients, and campaigns.

    Tags enable flexible organization and segmentation across the platform.
    Similar to ActiveCampaign and HubSpot tagging systems.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    CATEGORY_CHOICES = [
        ("general", "General"),
        ("industry", "Industry"),
        ("service", "Service Type"),
        ("status", "Status"),
        ("behavior", "Behavior"),
        ("campaign", "Campaign"),
        ("custom", "Custom"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="tags",
        help_text="Firm this tag belongs to",
    )

    # Tag identification
    name = models.CharField(max_length=100, help_text="Tag name")
    slug = models.SlugField(
        max_length=100,
        help_text="URL-friendly tag identifier",
    )
    description = models.TextField(blank=True, help_text="Tag description")

    # Categorization
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="general",
        help_text="Tag category",
    )

    # Color coding (for UI display)
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Hex color code for tag display (e.g., #FF5733)",
    )

    # Usage tracking
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of entities tagged with this tag",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tags",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "marketing_tags"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "category"]),
            models.Index(fields=["firm", "slug"]),
        ]
        unique_together = [["firm", "slug"]]

    def __str__(self):
        return f"{self.name}"

    def increment_usage(self):
        """Increment usage count."""
        self.usage_count += 1
        self.save(update_fields=["usage_count"])

    def decrement_usage(self):
        """Decrement usage count."""
        if self.usage_count > 0:
            self.usage_count -= 1
            self.save(update_fields=["usage_count"])


class Segment(models.Model):
    """
    Dynamic segment for targeted marketing campaigns.

    Segments define criteria for automatically including/excluding contacts
    based on tags, properties, and behaviors.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="segments",
        help_text="Firm this segment belongs to",
    )

    # Segment identification
    name = models.CharField(max_length=255, help_text="Segment name")
    description = models.TextField(blank=True, help_text="Segment description")

    # Segmentation criteria (JSON)
    criteria = models.JSONField(
        default=dict,
        help_text="Segmentation rules (tags, lead_score range, status, etc.)",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Segment status",
    )

    # Dynamic update
    auto_update = models.BooleanField(
        default=True,
        help_text="Automatically update segment membership based on criteria",
    )
    last_refreshed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When segment membership was last calculated",
    )

    # Usage tracking
    member_count = models.IntegerField(
        default=0,
        help_text="Cached count of current members",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_segments",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "marketing_segments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["firm", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.member_count} members)"

    def refresh_membership(self):
        """
        Recalculate segment membership based on criteria.

        This is a placeholder - actual implementation would query
        leads/prospects/clients based on criteria.
        """
        # TODO: Implement actual segmentation logic
        self.last_refreshed_at = timezone.now()
        self.save(update_fields=["last_refreshed_at"])


class EmailTemplate(models.Model):
    """
    Email template for marketing campaigns.

    Reusable email templates with merge fields and personalization.
    Similar to ActiveCampaign and HubSpot email designers.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    TEMPLATE_TYPE_CHOICES = [
        ("campaign", "Marketing Campaign"),
        ("transactional", "Transactional"),
        ("nurture", "Nurture Sequence"),
        ("announcement", "Announcement"),
        ("newsletter", "Newsletter"),
        ("custom", "Custom"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="email_templates",
        help_text="Firm this template belongs to",
    )

    # Template identification
    name = models.CharField(max_length=255, help_text="Template name (internal)")
    description = models.TextField(blank=True, help_text="Template description")
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        default="campaign",
        help_text="Template type",
    )

    # Email content
    subject_line = models.CharField(
        max_length=500,
        help_text="Email subject (supports merge fields like {{company_name}})",
    )
    preheader_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="Preheader text shown in email preview",
    )
    html_content = models.TextField(
        help_text="HTML email content (supports merge fields)",
    )
    plain_text_content = models.TextField(
        blank=True,
        help_text="Plain text version (auto-generated if blank)",
    )

    # Design metadata (for drag-and-drop builder)
    design_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Design structure for visual editor (blocks, styles, etc.)",
    )

    # Merge fields / Personalization
    available_merge_fields = models.JSONField(
        default=list,
        help_text="List of available merge fields (contact_name, company_name, etc.)",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Template status",
    )

    # Usage tracking
    times_used = models.IntegerField(
        default=0,
        help_text="Number of times this template has been used",
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this template was last used",
    )

    # Performance metrics (from campaigns using this template)
    avg_open_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average open rate percentage",
    )
    avg_click_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average click-through rate percentage",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_email_templates",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "marketing_email_templates"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["firm", "template_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    def mark_used(self):
        """Record template usage."""
        self.times_used += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["times_used", "last_used_at"])


class CampaignExecution(models.Model):
    """
    Campaign execution tracking.

    Records when a campaign is executed, who it was sent to, and performance metrics.
    Links to existing Campaign model in CRM module.

    TIER 0: Belongs to exactly one Firm (via campaign relationship).
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("sending", "Sending"),
        ("sent", "Sent"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]

    # Relationships
    campaign = models.ForeignKey(
        "crm.Campaign",
        on_delete=models.CASCADE,
        related_name="executions",
        help_text="Campaign being executed",
    )
    email_template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_executions",
        help_text="Email template used for this execution",
    )

    # Targeting
    segment = models.ForeignKey(
        Segment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_executions",
        help_text="Target segment for this campaign",
    )
    recipient_count = models.IntegerField(
        default=0,
        help_text="Number of recipients",
    )

    # Execution details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        help_text="Execution status",
    )
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to send this campaign",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When campaign started sending",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When campaign finished sending",
    )

    # Performance metrics
    emails_sent = models.IntegerField(default=0, help_text="Emails successfully sent")
    emails_failed = models.IntegerField(default=0, help_text="Failed sends")
    emails_opened = models.IntegerField(default=0, help_text="Unique opens")
    emails_clicked = models.IntegerField(default=0, help_text="Unique clicks")
    emails_bounced = models.IntegerField(default=0, help_text="Bounces")
    emails_unsubscribed = models.IntegerField(default=0, help_text="Unsubscribes")

    # Calculated rates
    open_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Open rate percentage",
    )
    click_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Click-through rate percentage",
    )
    bounce_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Bounce rate percentage",
    )

    # A/B testing (split testing)
    is_ab_test = models.BooleanField(
        default=False,
        help_text="Is this an A/B test campaign?",
    )
    ab_variant = models.CharField(
        max_length=10,
        blank=True,
        help_text="Variant identifier (A, B, C, etc.)",
    )

    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_campaign_executions",
    )

    class Meta:
        db_table = "marketing_campaign_executions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["campaign", "status"]),
            models.Index(fields=["status", "scheduled_for"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.campaign.name} - {self.get_status_display()}"

    def calculate_rates(self):
        """Calculate performance rates."""
        if self.emails_sent > 0:
            self.open_rate = (self.emails_opened / self.emails_sent) * 100
            self.click_rate = (self.emails_clicked / self.emails_sent) * 100
            self.bounce_rate = (self.emails_bounced / self.emails_sent) * 100
            self.save(update_fields=["open_rate", "click_rate", "bounce_rate"])


class EntityTag(models.Model):
    """
    Many-to-many relationship tracking tags applied to entities.

    Supports tagging of leads, prospects, clients, campaigns, and other entities.
    Provides a unified tagging interface across the platform.

    TIER 0: Belongs to exactly one Firm (via tag relationship).
    """

    ENTITY_TYPE_CHOICES = [
        ("lead", "Lead"),
        ("prospect", "Prospect"),
        ("client", "Client"),
        ("campaign", "Campaign"),
        ("contact", "Contact"),
        ("account", "Account"),
    ]

    # Relationship
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="entity_tags",
        help_text="Tag being applied",
    )

    # Entity (polymorphic)
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_TYPE_CHOICES,
        help_text="Type of entity being tagged",
    )
    entity_id = models.BigIntegerField(
        help_text="ID of the entity being tagged",
    )

    # Metadata
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="applied_tags",
        help_text="User who applied this tag",
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    # Auto-tagging context
    auto_applied = models.BooleanField(
        default=False,
        help_text="Was this tag automatically applied by a rule?",
    )
    auto_rule_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID of automation rule that applied this tag",
    )

    class Meta:
        db_table = "marketing_entity_tags"
        ordering = ["-applied_at"]
        indexes = [
            models.Index(fields=["tag", "entity_type"]),
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["applied_by", "-applied_at"]),
        ]
        # One tag per entity
        unique_together = [["tag", "entity_type", "entity_id"]]

    def __str__(self):
        return f"{self.tag.name} → {self.entity_type}:{self.entity_id}"

    def save(self, *args, **kwargs):
        """Update tag usage count when tag is applied."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.tag.increment_usage()

    def delete(self, *args, **kwargs):
        """Update tag usage count when tag is removed."""
        tag = self.tag
        super().delete(*args, **kwargs)
        tag.decrement_usage()
