import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class ClientHealthScore(models.Model):
    """
    Dynamic Client Health Score (CRM-INT-2).
    
    Tracks real-time health score for clients based on multiple factors:
    - Engagement (communication frequency, response time)
    - Payments (on-time payments, outstanding balance)
    - Communication (email interactions, meeting attendance)
    - Project Delivery (on-time completion, satisfaction)
    
    TIER 0: Belongs to exactly one Firm (via client relationship).
    """
    
    # Client relationship
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name="health_score",
        help_text="Client this health score belongs to"
    )
    
    # Overall Health Score (0-100)
    score = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall health score (0-100, where 100 is excellent)"
    )
    score_trend = models.CharField(
        max_length=20,
        choices=[
            ("improving", "Improving"),
            ("stable", "Stable"),
            ("declining", "Declining"),
        ],
        default="stable",
        help_text="Score trend over recent period"
    )
    
    # Factor Scores (0-100 each)
    engagement_score = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score based on engagement frequency and quality"
    )
    payment_score = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score based on payment history and timeliness"
    )
    communication_score = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score based on communication responsiveness"
    )
    delivery_score = models.IntegerField(
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score based on project delivery quality and satisfaction"
    )
    
    # Configurable Weights (sum should be 1.0)
    engagement_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.25"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))],
        help_text="Weight for engagement factor (0.0-1.0)"
    )
    payment_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.30"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))],
        help_text="Weight for payment factor (0.0-1.0)"
    )
    communication_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.25"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))],
        help_text="Weight for communication factor (0.0-1.0)"
    )
    delivery_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.20"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))],
        help_text="Weight for delivery factor (0.0-1.0)"
    )
    
    # Metrics for score calculation
    days_since_last_activity = models.IntegerField(default=0, help_text="Days since last client activity")
    overdue_invoice_count = models.IntegerField(default=0, help_text="Number of overdue invoices")
    overdue_invoice_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Total overdue invoice amount"
    )
    avg_payment_delay_days = models.IntegerField(default=0, help_text="Average payment delay in days")
    email_response_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        help_text="Email response rate percentage"
    )
    project_completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("100.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        help_text="Project completion rate percentage"
    )
    
    # Alert thresholds
    alert_threshold = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score threshold for at-risk alert"
    )
    is_at_risk = models.BooleanField(
        default=False,
        help_text="Whether client is currently at-risk (score below threshold)"
    )
    alert_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When last at-risk alert was sent"
    )
    
    # Historical tracking
    previous_score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Previous health score (for trend calculation)"
    )
    score_history = models.JSONField(
        default=list,
        blank=True,
        help_text="Historical scores: [{timestamp, score, factors}, ...]"
    )
    
    # Audit Fields
    last_calculated_at = models.DateTimeField(auto_now=True, help_text="When score was last calculated")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "clients_health_score"
        ordering = ["-last_calculated_at"]
        indexes = [
            models.Index(fields=["client"], name="clients_health_cli_idx"),
            models.Index(fields=["score"], name="clients_health_sco_idx"),
            models.Index(fields=["is_at_risk"], name="clients_health_ari_idx"),
            models.Index(fields=["-last_calculated_at"], name="clients_health_lca_idx"),
        ]
    
    def __str__(self):
        return f"{self.client.company_name}: {self.score} ({self.score_trend})"
    
    def calculate_score(self):
        """
        Calculate the overall health score based on factor scores and weights.
        
        Returns:
            int: Calculated health score (0-100)
        """
        score = (
            float(self.engagement_score) * float(self.engagement_weight) +
            float(self.payment_score) * float(self.payment_weight) +
            float(self.communication_score) * float(self.communication_weight) +
            float(self.delivery_score) * float(self.delivery_weight)
        )
        return int(round(score))
    
    def update_trend(self):
        """Update the score trend based on current and previous scores."""
        if self.previous_score is None:
            self.score_trend = "stable"
        else:
            diff = self.score - self.previous_score
            if diff >= 5:
                self.score_trend = "improving"
            elif diff <= -5:
                self.score_trend = "declining"
            else:
                self.score_trend = "stable"
    
    def check_at_risk(self):
        """Check if client is at-risk based on score threshold."""
        self.is_at_risk = self.score < self.alert_threshold
        return self.is_at_risk
    
    def save_to_history(self):
        """Save current score to history."""
        from django.utils import timezone
        
        history_entry = {
            "timestamp": timezone.now().isoformat(),
            "score": self.score,
            "engagement_score": self.engagement_score,
            "payment_score": self.payment_score,
            "communication_score": self.communication_score,
            "delivery_score": self.delivery_score,
        }
        
        if not isinstance(self.score_history, list):
            self.score_history = []
        
        self.score_history.append(history_entry)
        
        # Keep only last 90 days of history
        if len(self.score_history) > 90:
            self.score_history = self.score_history[-90:]
    
    def clean(self):
        """Validate that weights sum to approximately 1.0."""
        from django.core.exceptions import ValidationError
        
        total_weight = (
            self.engagement_weight +
            self.payment_weight +
            self.communication_weight +
            self.delivery_weight
        )
        
        # Allow small floating point differences
        if abs(float(total_weight) - 1.0) > 0.01:
            raise ValidationError({
                "engagement_weight": f"Weights must sum to 1.0 (current sum: {total_weight})"
            })


