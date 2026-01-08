from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class EnrichmentProvider(models.Model):
    """
    Configuration for contact/company data enrichment providers.

    Supports Clearbit, ZoomInfo, LinkedIn, and other enrichment services.
    Stores API credentials and configuration per firm.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    PROVIDER_CHOICES = [
        ("clearbit", "Clearbit"),
        ("zoominfo", "ZoomInfo"),
        ("linkedin", "LinkedIn"),
        ("custom", "Custom Provider"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="enrichment_providers",
        help_text="Firm this enrichment provider belongs to",
    )

    # Provider Configuration
    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        help_text="Enrichment service provider"
    )
    is_enabled = models.BooleanField(default=True, help_text="Whether this provider is active")

    # API Credentials (encrypted in production)
    api_key = models.CharField(max_length=500, blank=True, help_text="API key or OAuth token")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API secret (if required)")
    additional_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional provider-specific configuration"
    )

    # Auto-enrichment Settings
    auto_enrich_on_create = models.BooleanField(
        default=True,
        help_text="Automatically enrich new contacts"
    )
    auto_refresh_enabled = models.BooleanField(
        default=True,
        help_text="Enable scheduled re-enrichment"
    )
    refresh_interval_hours = models.IntegerField(
        default=24,
        help_text="Hours between automatic re-enrichment (default: 24)"
    )

    # Usage Tracking
    total_enrichments = models.IntegerField(default=0, help_text="Total enrichment API calls")
    successful_enrichments = models.IntegerField(default=0, help_text="Successful enrichments")
    failed_enrichments = models.IntegerField(default=0, help_text="Failed enrichments")
    last_used_at = models.DateTimeField(null=True, blank=True, help_text="Last enrichment timestamp")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_enrichment_providers",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "crm_enrichment_provider"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "provider"], name="crm_enrich_prov_firm_prov_idx"),
            models.Index(fields=["firm", "is_enabled"], name="crm_enrich_prov_firm_enabled_idx"),
        ]
        unique_together = [["firm", "provider"]]

    def __str__(self) -> str:
        return f"{self.get_provider_display()} - {self.firm.name}"

    @property
    def success_rate(self) -> float:
        """Calculate enrichment success rate."""
        if self.total_enrichments == 0:
            return 0.0
        return (self.successful_enrichments / self.total_enrichments) * 100


class ContactEnrichment(models.Model):
    """
    Enriched data for contacts from external providers.

    Stores company information, social profiles, and enrichment metadata
    from services like Clearbit, ZoomInfo, and LinkedIn.

    TIER 0: Belongs to exactly one Firm through the contact relationship.
    """

    # Related Contact (supports both CRM contacts and Client contacts)
    account_contact = models.OneToOneField(
        "crm.AccountContact",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="enrichment_data",
        help_text="AccountContact this enrichment belongs to"
    )
    client_contact = models.OneToOneField(
        "clients.Contact",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="enrichment_data",
        help_text="Client Contact this enrichment belongs to"
    )

    # Enrichment Source
    enrichment_provider = models.ForeignKey(
        EnrichmentProvider,
        on_delete=models.CASCADE,
        related_name="enrichments",
        help_text="Provider that enriched this contact"
    )

    # Company Data (from Clearbit/ZoomInfo)
    company_name = models.CharField(max_length=255, blank=True)
    company_domain = models.CharField(max_length=255, blank=True)
    company_industry = models.CharField(max_length=255, blank=True)
    company_size = models.CharField(max_length=100, blank=True)  # e.g., "51-200"
    company_revenue = models.CharField(max_length=100, blank=True)  # e.g., "$10M-$50M"
    company_description = models.TextField(blank=True)
    company_logo_url = models.URLField(max_length=500, blank=True, validators=[validate_safe_url])
    company_location = models.CharField(max_length=255, blank=True)
    company_founded_year = models.IntegerField(null=True, blank=True)

    # Contact Data
    contact_title = models.CharField(max_length=255, blank=True)
    contact_seniority = models.CharField(max_length=100, blank=True)  # e.g., "senior", "executive"
    contact_role = models.CharField(max_length=100, blank=True)  # e.g., "engineering", "sales"

    # Social Profiles
    linkedin_url = models.URLField(max_length=500, blank=True, validators=[validate_safe_url])
    twitter_url = models.URLField(max_length=500, blank=True, validators=[validate_safe_url])
    facebook_url = models.URLField(max_length=500, blank=True, validators=[validate_safe_url])
    github_url = models.URLField(max_length=500, blank=True, validators=[validate_safe_url])

    # Technology Stack (from Clearbit)
    technologies = models.JSONField(
        default=list,
        blank=True,
        help_text="Technologies used by the company (e.g., ['Salesforce', 'AWS'])"
    )

    # Raw Response Data
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full JSON response from enrichment provider"
    )

    # Data Quality
    confidence_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Confidence score of enrichment data (0-100)"
    )
    fields_enriched = models.JSONField(
        default=list,
        blank=True,
        help_text="List of fields successfully enriched"
    )
    fields_missing = models.JSONField(
        default=list,
        blank=True,
        help_text="List of fields not found by provider"
    )

    # Refresh Tracking
    last_enriched_at = models.DateTimeField(auto_now_add=True, help_text="Last enrichment timestamp")
    next_refresh_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Scheduled time for next refresh"
    )
    refresh_count = models.IntegerField(default=0, help_text="Number of times re-enriched")

    # Status
    is_stale = models.BooleanField(
        default=False,
        help_text="Whether data needs refreshing"
    )
    enrichment_error = models.TextField(blank=True, help_text="Last enrichment error message")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()

    class Meta:
        db_table = "crm_contact_enrichment"
        ordering = ["-last_enriched_at"]
        indexes = [
            models.Index(fields=["account_contact"], name="crm_enrich_acct_contact_idx"),
            models.Index(fields=["client_contact"], name="crm_enrich_client_contact_idx"),
            models.Index(fields=["enrichment_provider"], name="crm_enrich_provider_idx"),
            models.Index(fields=["is_stale", "next_refresh_at"], name="crm_enrich_refresh_idx"),
            models.Index(fields=["last_enriched_at"], name="crm_enrich_last_at_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(account_contact__isnull=False, client_contact__isnull=True) |
                    models.Q(account_contact__isnull=True, client_contact__isnull=False)
                ),
                name="crm_enrich_one_contact_type"
            )
        ]

    def __str__(self) -> str:
        contact_name = "Unknown"
        if self.account_contact:
            contact_name = f"{self.account_contact.first_name} {self.account_contact.last_name}"
        elif self.client_contact:
            contact_name = f"{self.client_contact.first_name} {self.client_contact.last_name}"
        return f"{contact_name} - {self.enrichment_provider.get_provider_display()}"

    @property
    def firm(self):
        """Get the firm through the contact relationship."""
        if self.account_contact:
            return self.account_contact.account.firm
        elif self.client_contact:
            return self.client_contact.firm
        return None

    @property
    def contact_email(self) -> str:
        """Get the contact's email."""
        if self.account_contact:
            return self.account_contact.email or ""
        elif self.client_contact:
            return self.client_contact.email or ""
        return ""

    @property
    def data_completeness(self) -> float:
        """Calculate data completeness percentage."""
        total_fields = len(self.fields_enriched) + len(self.fields_missing)
        if total_fields == 0:
            return 0.0
        return (len(self.fields_enriched) / total_fields) * 100

    def needs_refresh(self) -> bool:
        """Check if enrichment data needs refreshing."""
        from django.utils import timezone

        if self.is_stale:
            return True

        if self.next_refresh_at and self.next_refresh_at <= timezone.now():
            return True

        return False

    def mark_for_refresh(self):
        """Mark this enrichment for refresh."""
        self.is_stale = True
        self.save(update_fields=["is_stale", "updated_at"])

    def calculate_next_refresh(self):
        """Calculate next refresh time based on provider settings."""
        from django.utils import timezone
        from datetime import timedelta

        if self.enrichment_provider.auto_refresh_enabled:
            hours = self.enrichment_provider.refresh_interval_hours
            self.next_refresh_at = timezone.now() + timedelta(hours=hours)
        else:
            self.next_refresh_at = None


class EnrichmentQualityMetric(models.Model):
    """
    Tracks data quality metrics for enrichment providers.

    Monitors accuracy, completeness, and freshness of enriched data
    to help evaluate provider performance.

    TIER 0: Belongs to exactly one Firm through the provider relationship.
    """

    # Provider
    enrichment_provider = models.ForeignKey(
        EnrichmentProvider,
        on_delete=models.CASCADE,
        related_name="quality_metrics",
        help_text="Provider being measured"
    )

    # Quality Metrics
    metric_date = models.DateField(help_text="Date of quality measurement")
    total_enrichments = models.IntegerField(default=0, help_text="Total enrichments performed")
    successful_enrichments = models.IntegerField(default=0, help_text="Successful enrichments")
    failed_enrichments = models.IntegerField(default=0, help_text="Failed enrichments")

    # Completeness Metrics
    average_completeness = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Average data completeness percentage"
    )
    average_confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Average confidence score"
    )

    # Field-level Metrics
    field_success_rates = models.JSONField(
        default=dict,
        blank=True,
        help_text="Success rate per field (e.g., {'company_name': 95.5, 'linkedin_url': 60.2})"
    )

    # Response Time Metrics
    average_response_time_ms = models.IntegerField(
        default=0,
        help_text="Average API response time in milliseconds"
    )

    # Error Tracking
    error_types = models.JSONField(
        default=dict,
        blank=True,
        help_text="Count of error types (e.g., {'rate_limit': 5, 'not_found': 10})"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: No direct firm FK but accessed through provider
    objects = models.Manager()

    class Meta:
        db_table = "crm_enrichment_quality_metric"
        ordering = ["-metric_date"]
        indexes = [
            models.Index(fields=["enrichment_provider", "-metric_date"], name="crm_enrich_qual_prov_date_idx"),
        ]
        unique_together = [["enrichment_provider", "metric_date"]]

    def __str__(self) -> str:
        return f"{self.enrichment_provider.get_provider_display()} - {self.metric_date}"

    @property
    def firm(self):
        """Get the firm through the provider relationship."""
        return self.enrichment_provider.firm

    @property
    def success_rate(self) -> float:
        """Calculate enrichment success rate."""
        if self.total_enrichments == 0:
            return 0.0
        return (self.successful_enrichments / self.total_enrichments) * 100
