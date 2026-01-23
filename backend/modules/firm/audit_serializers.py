"""Serializers for audit event APIs."""

from rest_framework import serializers

from modules.firm.audit import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    """Read-only serializer for immutable audit events."""

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "category",
            "action",
            "severity",
            "actor",
            "actor_email",
            "actor_role",
            "target_model",
            "target_id",
            "target_repr",
            "timestamp",
            "reason",
            "outcome",
            "metadata",
            "ip_address",
            "user_agent",
            "request_id",
            "reviewed_at",
            "reviewed_by",
            "review_notes",
        ]
        read_only_fields = fields
