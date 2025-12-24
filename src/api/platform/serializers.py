"""
Platform API Serializers (TIER 0.6).

Serializers for platform operator and break-glass operations.
"""
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from modules.firm.models import BreakGlassSession, AuditEvent, Firm


class BreakGlassActivationSerializer(serializers.Serializer):
    """
    Serializer for activating a break-glass session.
    """
    firm_id = serializers.IntegerField(
        required=True,
        help_text="ID of the firm to access"
    )
    reason = serializers.CharField(
        required=True,
        min_length=20,
        max_length=1000,
        help_text="Detailed reason for break-glass access (min 20 chars)"
    )
    duration_hours = serializers.IntegerField(
        required=False,
        default=4,
        min_value=1,
        max_value=24,
        help_text="Session duration in hours (1-24, default 4)"
    )
    impersonated_user_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Optional: ID of firm user to impersonate"
    )
    
    def validate_firm_id(self, value):
        """Validate firm exists and is active."""
        try:
            firm = Firm.objects.get(id=value, status__in=['trial', 'active'])
            return value
        except Firm.DoesNotExist:
            raise serializers.ValidationError("Firm not found or inactive")
    
    def validate_reason(self, value):
        """Validate reason is meaningful."""
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Reason must be at least 20 characters and provide meaningful context"
            )
        return value


class BreakGlassSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for BreakGlassSession instances.
    """
    firm_name = serializers.CharField(source='firm.name', read_only=True)
    operator_username = serializers.CharField(source='operator.username', read_only=True)
    impersonated_username = serializers.CharField(
        source='impersonated_user.username', 
        read_only=True,
        allow_null=True
    )
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = BreakGlassSession
        fields = [
            'id', 'firm', 'firm_name', 'operator', 'operator_username',
            'impersonated_user', 'impersonated_username', 'reason',
            'status', 'activated_at', 'expires_at', 'revoked_at',
            'revoked_reason', 'reviewed_at', 'reviewed_by',
            'is_active', 'is_expired'
        ]
        read_only_fields = [
            'id', 'activated_at', 'status', 'is_active', 'is_expired'
        ]


class BreakGlassRevocationSerializer(serializers.Serializer):
    """
    Serializer for revoking a break-glass session.
    """
    reason = serializers.CharField(
        required=True,
        min_length=10,
        max_length=500,
        help_text="Reason for early revocation"
    )


class AuditEventSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditEvent instances (read-only).
    """
    firm_name = serializers.CharField(source='firm.name', read_only=True, allow_null=True)
    
    class Meta:
        model = AuditEvent
        fields = [
            'id', 'firm', 'firm_name', 'category', 'action',
            'actor', 'actor_username', 'actor_email',
            'target_model', 'target_id', 'target_description',
            'reason', 'metadata', 'timestamp'
        ]
        read_only_fields = '__all__'
