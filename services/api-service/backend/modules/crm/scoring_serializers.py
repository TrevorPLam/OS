"""
Serializers for lead scoring automation.

Provides DRF serializers for ScoringRule and ScoreAdjustment models.
"""

from rest_framework import serializers
from modules.crm.lead_scoring import ScoringRule, ScoreAdjustment
from modules.crm.models import Lead


class ScoringRuleSerializer(serializers.ModelSerializer):
    """Serializer for ScoringRule."""

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = ScoringRule
        fields = [
            'id',
            'firm',
            'name',
            'description',
            'rule_type',
            'trigger',
            'conditions',
            'points',
            'max_applications',
            'decay_days',
            'is_active',
            'priority',
            'times_applied',
            'last_applied_at',
            'created_at',
            'updated_at',
            'created_by',
            'created_by_name',
        ]
        read_only_fields = [
            'id',
            'times_applied',
            'last_applied_at',
            'created_at',
            'updated_at',
            'created_by_name',
        ]


class ScoreAdjustmentSerializer(serializers.ModelSerializer):
    """Serializer for ScoreAdjustment."""

    lead_company_name = serializers.CharField(source='lead.company_name', read_only=True)
    lead_contact_name = serializers.CharField(source='lead.contact_name', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)

    class Meta:
        model = ScoreAdjustment
        fields = [
            'id',
            'lead',
            'lead_company_name',
            'lead_contact_name',
            'rule',
            'rule_name',
            'points',
            'reason',
            'trigger_event',
            'event_data',
            'decays_at',
            'is_decayed',
            'applied_at',
            'applied_by',
            'applied_by_name',
        ]
        read_only_fields = [
            'id',
            'decays_at',
            'is_decayed',
            'applied_at',
            'lead_company_name',
            'lead_contact_name',
            'rule_name',
            'applied_by_name',
        ]


class LeadScoreBreakdownSerializer(serializers.Serializer):
    """Serializer for lead score breakdown."""

    reason = serializers.CharField(read_only=True)
    rule__name = serializers.CharField(read_only=True, allow_null=True)
    total_points = serializers.IntegerField(read_only=True)


class TestRuleSerializer(serializers.Serializer):
    """Serializer for testing a scoring rule against leads."""

    lead_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='List of lead IDs to test against (if not provided, tests against all leads)'
    )
    event_data = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Optional event data for behavioral triggers'
    )


class ApplyRuleSerializer(serializers.Serializer):
    """Serializer for applying a rule to leads."""

    lead_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text='List of lead IDs to apply rule to'
    )
    event_data = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Optional event data for behavioral triggers'
    )

    def validate_lead_ids(self, value):
        """Validate lead IDs exist."""
        if not value:
            raise serializers.ValidationError('At least one lead ID is required')
        return value


class ManualScoreAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual score adjustments."""

    points = serializers.IntegerField(
        required=True,
        help_text='Points to add (positive) or subtract (negative)'
    )
    reason = serializers.CharField(
        required=True,
        max_length=500,
        help_text='Reason for manual adjustment'
    )

    def validate_points(self, value):
        """Validate points range."""
        if value < -100 or value > 100:
            raise serializers.ValidationError('Points must be between -100 and 100')
        if value == 0:
            raise serializers.ValidationError('Points cannot be zero')
        return value

    def validate_reason(self, value):
        """Validate reason is provided."""
        if not value or not value.strip():
            raise serializers.ValidationError('Reason is required')
        return value.strip()
