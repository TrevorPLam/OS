"""
Client Health Score Module

Implements dynamic client health scoring with multi-factor analysis:
- Engagement: Activity levels, responsiveness
- Payments: Invoice payment patterns, overdue amounts
- Communication: Message frequency, response times
- Project Delivery: On-time completion, satisfaction

TIER 0: All health scores belong to exactly one Firm for tenant isolation.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class ClientHealthScoreConfig(models.Model):
    """
    Configuration for health score calculation per firm.
    
    Allows firms to customize weights for each scoring factor.
    Default weights sum to 100 for a total score of 0-100.
    
    TIER 0: Belongs to exactly one Firm.
    """
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="health_score_configs",
        help_text="Firm this configuration belongs to",
    )
    
    # Factor weights (must sum to 100)
    engagement_weight = models.IntegerField(
        default=25,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight for engagement factor (0-100)",
    )
    payment_weight = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight for payment factor (0-100)",
    )
    communication_weight = models.IntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight for communication factor (0-100)",
    )
    project_delivery_weight = models.IntegerField(
        default=25,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight for project delivery factor (0-100)",
    )
    
    # Alert thresholds
    alert_threshold = models.IntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        help_text="Alert when score drops by this many points",
    )
    at_risk_threshold = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score below this is considered at-risk",
    )
    
    # Calculation settings
    lookback_days = models.IntegerField(
        default=90,
        validators=[MinValueValidator(30), MaxValueValidator(365)],
        help_text="Days to look back for historical data",
    )
    
    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_health_score_configs",
        help_text="User who created this configuration",
    )
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "clients_health_score_config"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="clients_hsc_fir_act_idx"),
        ]
        # Only one active config per firm
        unique_together = [["firm", "is_active"]]
    
    def __str__(self):
        return f"Health Score Config for {self.firm.name}"
    
    def clean(self):
        """Validate that weights sum to 100."""
        from django.core.exceptions import ValidationError
        
        total_weight = (
            self.engagement_weight +
            self.payment_weight +
            self.communication_weight +
            self.project_delivery_weight
        )
        
        if total_weight != 100:
            raise ValidationError(
                f"Factor weights must sum to 100, got {total_weight}"
            )


class ClientHealthScore(models.Model):
    """
    Client Health Score snapshot.
    
    Records the health score for a client at a specific point in time.
    Includes overall score and individual factor scores for analysis.
    
    TIER 0: Belongs to a Firm through Client relationship.
    """
    
    # TIER 0: Firm tenancy (inherited through client)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="client_health_scores",
        help_text="Firm this score belongs to",
    )
    
    # Relationships
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="health_scores",
        help_text="Client this score belongs to",
    )
    
    # Overall score (0-100)
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall health score (0-100)",
    )
    
    # Factor scores (0-100 each, before weighting)
    engagement_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Engagement factor score (0-100)",
    )
    payment_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Payment factor score (0-100)",
    )
    communication_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Communication factor score (0-100)",
    )
    project_delivery_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Project delivery factor score (0-100)",
    )
    
    # Metadata for calculation
    calculation_metadata = models.JSONField(
        default=dict,
        help_text="Detailed calculation breakdown for audit trail",
    )
    
    # Previous score for trend tracking
    previous_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Previous health score for comparison",
    )
    score_change = models.IntegerField(
        default=0,
        help_text="Change from previous score (negative = decline)",
    )
    
    # Alert flags
    is_at_risk = models.BooleanField(
        default=False,
        help_text="True if score is below at-risk threshold",
    )
    triggered_alert = models.BooleanField(
        default=False,
        help_text="True if score drop triggered an alert",
    )
    
    # Audit fields
    calculated_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this score was calculated",
    )
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "clients_health_score"
        ordering = ["-calculated_at"]
        indexes = [
            models.Index(fields=["firm", "client", "-calculated_at"], name="clients_hs_fir_cli_cal_idx"),
            models.Index(fields=["firm", "is_at_risk"], name="clients_hs_fir_risk_idx"),
            models.Index(fields=["firm", "triggered_alert"], name="clients_hs_fir_alert_idx"),
            models.Index(fields=["client", "-calculated_at"], name="clients_hs_cli_cal_idx"),
        ]
    
    def __str__(self):
        return f"Health Score {self.score} for {self.client.company_name} ({self.calculated_at.date()})"


class ClientHealthScoreAlert(models.Model):
    """
    Alert for significant health score changes.
    
    Created when a client's health score drops significantly.
    Allows tracking of alert acknowledgment and resolution.
    
    TIER 0: Belongs to a Firm through Client relationship.
    """
    
    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]
    
    # TIER 0: Firm tenancy (inherited through client)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="client_health_alerts",
        help_text="Firm this alert belongs to",
    )
    
    # Relationships
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="health_alerts",
        help_text="Client this alert is for",
    )
    health_score = models.ForeignKey(
        ClientHealthScore,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="Health score that triggered this alert",
    )
    
    # Alert details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Current status of this alert",
    )
    score_drop = models.IntegerField(
        help_text="How many points the score dropped",
    )
    previous_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score before the drop",
    )
    current_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score after the drop",
    )
    
    # Action tracking
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this alert was acknowledged",
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_health_alerts",
        help_text="User who acknowledged this alert",
    )
    resolution_notes = models.TextField(
        blank=True,
        help_text="Notes about how this alert was resolved",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this alert was resolved",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_health_alerts",
        help_text="User who resolved this alert",
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()
    
    class Meta:
        db_table = "clients_health_score_alert"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status", "-created_at"], name="clients_hsa_fir_sta_cre_idx"),
            models.Index(fields=["client", "status"], name="clients_hsa_cli_sta_idx"),
        ]
    
    def __str__(self):
        return f"Alert: {self.client.company_name} score dropped {self.score_drop} points"
