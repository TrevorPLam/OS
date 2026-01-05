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
            models.Index(fields=["firm", "category"], name="marketing_fir_cat_idx"),
            models.Index(fields=["firm", "slug"], name="marketing_fir_slu_idx"),
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
            models.Index(fields=["firm", "status"], name="marketing_seg_fir_sta_idx"),
            models.Index(fields=["firm", "-created_at"], name="marketing_fir_cre_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.member_count} members)"

    def refresh_membership(self):
        """
        Recalculate segment membership based on criteria.

        This is a placeholder - actual implementation would query
        leads/prospects/clients based on criteria.
        """
        from modules.clients.models import Client
        from modules.crm.models import Lead, Prospect

        criteria = self.criteria or {}
        entity_types = criteria.get("entity_types") or ["lead", "prospect", "client"]
        tag_slugs = criteria.get("tags") or []

        def apply_tag_filter(queryset, entity_type: str):
            """Filter queryset by tag slugs for the given entity type."""
            if not tag_slugs:
                return queryset

            tagged_ids = (
                EntityTag.objects.filter(
                    entity_type=entity_type,
                    tag__firm=self.firm,
                    tag__slug__in=tag_slugs,
                )
                .values_list("entity_id", flat=True)
                .distinct()
            )
            return queryset.filter(pk__in=tagged_ids)

        def score_range(config: dict):
            """Normalize min/max score filters."""
            if not isinstance(config, dict):
                return None, None
            return config.get("min"), config.get("max")

        total_members = 0

        if "lead" in entity_types:
            lead_qs = Lead.objects.filter(firm=self.firm)

            lead_status = criteria.get("lead_status") or criteria.get("lead_statuses")
            if lead_status:
                lead_qs = lead_qs.filter(status__in=lead_status)

            min_score, max_score = score_range(criteria.get("lead_score", {}))
            if min_score is not None:
                lead_qs = lead_qs.filter(lead_score__gte=min_score)
            if max_score is not None:
                lead_qs = lead_qs.filter(lead_score__lte=max_score)

            lead_qs = apply_tag_filter(lead_qs, "lead")
            total_members += lead_qs.distinct().count()

        if "prospect" in entity_types:
            prospect_qs = Prospect.objects.filter(firm=self.firm)

            stages = criteria.get("prospect_stages") or criteria.get("pipeline_stages")
            if stages:
                prospect_qs = prospect_qs.filter(stage__in=stages)

            prospect_qs = apply_tag_filter(prospect_qs, "prospect")
            total_members += prospect_qs.distinct().count()

        if "client" in entity_types:
            client_qs = Client.objects.filter(firm=self.firm)

            client_status = criteria.get("client_status") or criteria.get("client_statuses")
            if client_status:
                client_qs = client_qs.filter(status__in=client_status)

            client_qs = apply_tag_filter(client_qs, "client")
            total_members += client_qs.distinct().count()

        self.member_count = total_members
        self.last_refreshed_at = timezone.now()
        self.save(update_fields=["member_count", "last_refreshed_at"])


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
            models.Index(fields=["firm", "status"], name="marketing_tml_fir_sta_idx"),
            models.Index(fields=["firm", "template_type"], name="marketing_fir_tem_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    def mark_used(self):
        """Record template usage."""
        self.times_used += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=["times_used", "last_used_at"])


class EmailDomainAuthentication(models.Model):
    """
    Domain authentication records for email deliverability (DELIV-1).

    Tracks SPF, DKIM, and DMARC verification status per firm domain.
    """

    STATUS_PENDING = "pending"
    STATUS_VERIFIED = "verified"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_FAILED, "Failed"),
    ]

    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="email_domains",
        help_text="Firm that owns this sending domain",
    )
    domain = models.CharField(max_length=255, help_text="Sending domain (e.g., example.com)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Overall verification status",
    )

    spf_record = models.CharField(max_length=500, blank=True, help_text="Expected SPF record")
    dkim_record = models.CharField(max_length=500, blank=True, help_text="Expected DKIM record")
    dmarc_record = models.CharField(max_length=500, blank=True, help_text="Expected DMARC record")
    spf_verified = models.BooleanField(default=False)
    dkim_verified = models.BooleanField(default=False)
    dmarc_verified = models.BooleanField(default=False)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_email_domains",
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "marketing_email_domains"
        ordering = ["domain"]
        indexes = [
            models.Index(fields=["firm", "domain"], name="marketing_dom_fir_dom_idx"),
            models.Index(fields=["firm", "status"], name="marketing_dom_fir_sta_idx"),
        ]
        unique_together = [["firm", "domain"]]

    def __str__(self):
        return f"{self.domain} ({self.get_status_display()})"

    def update_status(self):
        """Update overall status based on SPF/DKIM/DMARC checks."""
        if self.spf_verified and self.dkim_verified and self.dmarc_verified:
            self.status = self.STATUS_VERIFIED
        elif self.spf_verified or self.dkim_verified or self.dmarc_verified:
            self.status = self.STATUS_PENDING
        else:
            self.status = self.STATUS_FAILED
        self.save(update_fields=["status", "updated_at"])


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
            models.Index(fields=["campaign", "status"], name="marketing_cam_sta_idx"),
            models.Index(fields=["status", "scheduled_for"], name="marketing_sta_sch_idx"),
            models.Index(fields=["-created_at"], name="marketing_cre_idx"),
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


class CampaignRecipientStatus(models.Model):
    """
    Per-recipient delivery status for campaign executions.

    Tracks whether a contact received, failed, or bounced for a given execution.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("bounced", "Bounced"),
    ]

    execution = models.ForeignKey(
        CampaignExecution,
        on_delete=models.CASCADE,
        related_name="recipient_statuses",
        help_text="Campaign execution this recipient belongs to",
    )
    contact = models.ForeignKey(
        "clients.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaign_recipient_statuses",
        help_text="Contact receiving the campaign",
    )
    email = models.EmailField(help_text="Recipient email address")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Delivery status for this recipient",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "marketing_campaign_recipient_status"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["execution", "status"], name="marketing_rec_sta_exe_idx"),
            models.Index(fields=["email"], name="marketing_rec_sta_email_idx"),
        ]
        unique_together = [["execution", "email"]]

    def __str__(self):
        return f"{self.email} ({self.status})"

    def mark_sent(self):
        from django.utils import timezone

        self.status = "sent"
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "updated_at"])

    def mark_failed(self, reason: str):
        from django.utils import timezone

        self.status = "failed"
        self.failed_at = timezone.now()
        self.error_message = reason
        self.save(update_fields=["status", "failed_at", "error_message", "updated_at"])


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
            models.Index(fields=["tag", "entity_type"], name="marketing_tag_ent_idx"),
            models.Index(fields=["entity_type", "entity_id"], name="marketing_ent_ent_idx"),
            models.Index(fields=["applied_by", "-applied_at"], name="marketing_app_app_idx"),
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
