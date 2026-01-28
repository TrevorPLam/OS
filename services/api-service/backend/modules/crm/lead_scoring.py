"""
Lead scoring automation models.

Automated lead scoring based on behavioral triggers, demographics,
and engagement metrics.

Meta-commentary:
- **Current Status:** Rules create ScoreAdjustment records and Lead scores are recalculated from non-decayed points.
- **Design Rationale:** Separate rule definitions from adjustments to preserve an audit trail (WHY: explainable scoring).
- **Assumption:** Behavioral event payloads use `event.*` keys to match trigger conditions.
- **Limitation:** Condition matching supports exact, list, and min/max range comparisons only.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager
from modules.crm.models import Lead
import json


class ScoringRule(models.Model):
    """
    Automated lead scoring rule.

    Defines conditions and point values for automatic lead score calculation.
    Rules can be based on:
    - Demographics (industry, company size, location)
    - Behavioral triggers (email opens, link clicks, form submissions)
    - Engagement metrics (website visits, content downloads)
    - CRM data (budget, timeline, authority)
    """

    RULE_TYPE_CHOICES = [
        ('demographic', 'Demographic'),
        ('behavioral', 'Behavioral'),
        ('engagement', 'Engagement'),
        ('firmographic', 'Firmographic'),
        ('custom', 'Custom'),
    ]

    TRIGGER_CHOICES = [
        # Behavioral
        ('email_opened', 'Email Opened'),
        ('email_clicked', 'Email Link Clicked'),
        ('form_submitted', 'Form Submitted'),
        ('page_visited', 'Page Visited'),
        ('document_downloaded', 'Document Downloaded'),
        ('meeting_booked', 'Meeting Booked'),
        ('meeting_attended', 'Meeting Attended'),
        ('proposal_viewed', 'Proposal Viewed'),

        # Engagement
        ('reply_received', 'Reply to Email Received'),
        ('phone_answered', 'Phone Call Answered'),
        ('referral_made', 'Referral Made'),
        ('social_engagement', 'Social Media Engagement'),

        # Demographic/Firmographic
        ('job_title_match', 'Job Title Matches Criteria'),
        ('company_size_match', 'Company Size in Range'),
        ('industry_match', 'Industry Matches'),
        ('location_match', 'Location Matches'),
        ('budget_range_match', 'Budget in Range'),

        # Custom
        ('custom_field_match', 'Custom Field Matches'),
        ('tag_added', 'Tag Added'),
        ('status_changed', 'Status Changed'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='scoring_rules',
        help_text='Firm this rule belongs to'
    )

    # Rule Definition
    name = models.CharField(
        max_length=255,
        help_text='Descriptive name for this rule'
    )
    description = models.TextField(
        blank=True,
        help_text='Detailed description of what this rule does'
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        help_text='Type of scoring rule'
    )

    # Trigger & Conditions
    trigger = models.CharField(
        max_length=50,
        choices=TRIGGER_CHOICES,
        help_text='Event that triggers this rule'
    )
    conditions = models.JSONField(
        default=dict,
        help_text='Conditions that must be met (JSON object with field: value pairs)'
    )

    # Scoring
    points = models.IntegerField(
        validators=[MinValueValidator(-100), MaxValueValidator(100)],
        help_text='Points to add (positive) or subtract (negative) when rule matches'
    )
    max_applications = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maximum times this rule can be applied to same lead (null = unlimited)'
    )
    decay_days = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Days after which points from this rule decay to 0 (null = no decay)'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this rule is active'
    )
    priority = models.IntegerField(
        default=0,
        help_text='Rule priority for execution order (higher = earlier)'
    )

    # Usage Tracking
    times_applied = models.IntegerField(
        default=0,
        help_text='Total number of times this rule has been applied'
    )
    last_applied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this rule was last applied'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_scoring_rules',
        help_text='User who created this rule'
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'scoring_rules'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['firm', 'is_active']),
            models.Index(fields=['firm', 'rule_type']),
            models.Index(fields=['trigger']),
            models.Index(fields=['-priority']),
        ]

    def __str__(self):
        return f"{self.name} ({self.points:+d} points)"

    def clean(self):
        """Validate scoring rule."""
        super().clean()

        # Validate conditions JSON
        if self.conditions:
            try:
                json.dumps(self.conditions)
            except (TypeError, ValueError):
                raise ValidationError({'conditions': 'Conditions must be valid JSON'})

    def matches_conditions(self, lead, event_data=None):
        """
        Check if lead matches rule conditions.

        Args:
            lead (Lead): Lead to check
            event_data (dict): Optional event data for behavioral triggers

        Returns:
            bool: True if conditions match
        """
        if not self.conditions:
            return True  # No conditions = always match

        for field, expected_value in self.conditions.items():
            if field.startswith('event.') and event_data:
                # Check event data
                event_field = field.replace('event.', '')
                actual_value = event_data.get(event_field)
            else:
                # Check lead field
                try:
                    actual_value = getattr(lead, field, None)
                except AttributeError:
                    return False

            # Compare values
            if isinstance(expected_value, dict):
                # Range comparison
                if 'min' in expected_value and actual_value < expected_value['min']:
                    return False
                if 'max' in expected_value and actual_value > expected_value['max']:
                    return False
            elif isinstance(expected_value, list):
                # In list comparison
                if actual_value not in expected_value:
                    return False
            else:
                # Exact match
                if actual_value != expected_value:
                    return False

        return True

    def can_apply_to_lead(self, lead):
        """
        Check if rule can be applied to lead.

        Checks max_applications limit and decay.

        Args:
            lead (Lead): Lead to check

        Returns:
            bool: True if rule can be applied
        """
        if not self.is_active:
            return False

        if self.max_applications:
            application_count = ScoreAdjustment.objects.filter(
                lead=lead,
                rule=self
            ).count()
            if application_count >= self.max_applications:
                return False

        return True

    def apply_to_lead(self, lead, event_data=None, applied_by=None):
        """
        Apply scoring rule to lead.

        Args:
            lead (Lead): Lead to score
            event_data (dict): Optional event data
            applied_by (User): User who triggered the rule

        Returns:
            ScoreAdjustment: Created adjustment record, or None if not applied
        """
        if not self.can_apply_to_lead(lead):
            return None

        if not self.matches_conditions(lead, event_data):
            return None

        # Create score adjustment
        from django.utils import timezone
        adjustment = ScoreAdjustment.objects.create(
            lead=lead,
            rule=self,
            points=self.points,
            reason=f"Rule: {self.name}",
            trigger_event=self.trigger,
            event_data=event_data or {},
            applied_by=applied_by
        )

        # Update rule usage
        self.times_applied += 1
        self.last_applied_at = timezone.now()
        self.save(update_fields=['times_applied', 'last_applied_at'])

        # Recalculate lead score
        lead.recalculate_score()

        return adjustment


class ScoreAdjustment(models.Model):
    """
    Individual score adjustment record.

    Tracks each time a scoring rule is applied to a lead,
    creating an audit trail of score changes.
    """

    lead = models.ForeignKey(
        'crm.Lead',
        on_delete=models.CASCADE,
        related_name='score_adjustments',
        help_text='Lead this adjustment applies to'
    )
    rule = models.ForeignKey(
        ScoringRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjustments',
        help_text='Rule that created this adjustment (null if manual)'
    )

    # Adjustment Details
    points = models.IntegerField(
        help_text='Points added or subtracted'
    )
    reason = models.CharField(
        max_length=500,
        help_text='Reason for adjustment'
    )
    trigger_event = models.CharField(
        max_length=50,
        blank=True,
        help_text='Event that triggered this adjustment'
    )
    event_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Event data (e.g., email_id, page_url, form_id)'
    )

    # Decay
    decays_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When these points will decay to 0'
    )
    is_decayed = models.BooleanField(
        default=False,
        help_text='Whether these points have decayed'
    )

    # Metadata
    applied_at = models.DateTimeField(auto_now_add=True)
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='score_adjustments_applied',
        help_text='User who applied this adjustment (null if automated)'
    )

    objects = models.Manager()

    class Meta:
        db_table = 'score_adjustments'
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['lead', '-applied_at']),
            models.Index(fields=['rule', '-applied_at']),
            models.Index(fields=['trigger_event']),
            models.Index(fields=['decays_at', 'is_decayed']),
        ]

    def __str__(self):
        return f"{self.lead} {self.points:+d} points: {self.reason}"

    def save(self, *args, **kwargs):
        """Override save to set decay date."""
        if self.rule and self.rule.decay_days and not self.decays_at:
            from datetime import timedelta
            from django.utils import timezone
            self.decays_at = timezone.now() + timedelta(days=self.rule.decay_days)
        super().save(*args, **kwargs)


# Extend Lead model with scoring methods
def recalculate_score(self):
    """
    Recalculate lead score from scratch.

    Sums all non-decayed score adjustments.
    """
    from django.db.models import Sum
    from django.utils import timezone

    # Mark decayed adjustments
    ScoreAdjustment.objects.filter(
        lead=self,
        decays_at__lt=timezone.now(),
        is_decayed=False
    ).update(is_decayed=True)

    # Calculate total score
    total = ScoreAdjustment.objects.filter(
        lead=self,
        is_decayed=False
    ).aggregate(total=Sum('points'))['total'] or 0

    self.lead_score = max(0, min(100, total))  # Clamp between 0-100
    self.save(update_fields=['lead_score'])

    return self.lead_score


def add_score_points(self, points, reason, applied_by=None):
    """
    Manually add points to lead score.

    Args:
        points (int): Points to add (can be negative)
        reason (str): Reason for adjustment
        applied_by (User): User making the adjustment

    Returns:
        ScoreAdjustment: Created adjustment
    """
    adjustment = ScoreAdjustment.objects.create(
        lead=self,
        points=points,
        reason=reason,
        applied_by=applied_by
    )
    self.recalculate_score()
    return adjustment


def get_score_breakdown(self):
    """
    Get breakdown of score by rule/reason.

    Returns:
        list: List of dicts with rule name and points
    """
    from django.db.models import Sum

    breakdown = ScoreAdjustment.objects.filter(
        lead=self,
        is_decayed=False
    ).values(
        'reason', 'rule__name'
    ).annotate(
        total_points=Sum('points')
    ).order_by('-total_points')

    return list(breakdown)


# Add methods to Lead model
Lead.add_to_class('recalculate_score', recalculate_score)
Lead.add_to_class('add_score_points', add_score_points)
Lead.add_to_class('get_score_breakdown', get_score_breakdown)
