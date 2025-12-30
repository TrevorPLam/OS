"""
Email Ingestion Serializers.

Provides API serialization for email triage and mapping workflows.
"""

from rest_framework import serializers
from .models import EmailConnection, EmailArtifact, EmailAttachment, IngestionAttempt


class EmailConnectionSerializer(serializers.ModelSerializer):
    """Serializer for EmailConnection."""

    class Meta:
        model = EmailConnection
        fields = [
            "id",
            "name",
            "provider",
            "email_address",
            "is_active",
            "last_sync_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_sync_at", "created_at", "updated_at"]


class EmailAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for EmailAttachment."""

    document_name = serializers.CharField(source="document.name", read_only=True)

    class Meta:
        model = EmailAttachment
        fields = [
            "id",
            "original_filename",
            "content_type",
            "size_bytes",
            "attachment_index",
            "document",
            "document_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EmailArtifactListSerializer(serializers.ModelSerializer):
    """Serializer for EmailArtifact list view (triage queue)."""

    attachment_count = serializers.SerializerMethodField()
    connection_name = serializers.CharField(source="connection.name", read_only=True)

    class Meta:
        model = EmailArtifact
        fields = [
            "email_artifact_id",
            "from_address",
            "subject",
            "sent_at",
            "status",
            "mapping_confidence",
            "connection_name",
            "attachment_count",
            "created_at",
        ]
        read_only_fields = fields

    def get_attachment_count(self, obj):
        """Return count of attachments."""
        return obj.attachments.count()


class EmailArtifactDetailSerializer(serializers.ModelSerializer):
    """Serializer for EmailArtifact detail view."""

    attachments = EmailAttachmentSerializer(many=True, read_only=True)
    connection_name = serializers.CharField(source="connection.name", read_only=True)
    suggested_account_name = serializers.CharField(source="suggested_account.name", read_only=True, allow_null=True)
    suggested_engagement_title = serializers.CharField(
        source="suggested_engagement.title", read_only=True, allow_null=True
    )
    confirmed_account_name = serializers.CharField(source="confirmed_account.name", read_only=True, allow_null=True)
    confirmed_engagement_title = serializers.CharField(
        source="confirmed_engagement.title", read_only=True, allow_null=True
    )

    class Meta:
        model = EmailArtifact
        fields = [
            "email_artifact_id",
            "provider",
            "external_message_id",
            "thread_id",
            "from_address",
            "to_addresses",
            "cc_addresses",
            "subject",
            "body_preview",
            "sent_at",
            "received_at",
            "status",
            "mapping_confidence",
            "mapping_reasons",
            "suggested_account",
            "suggested_account_name",
            "suggested_engagement",
            "suggested_engagement_title",
            "suggested_work_item",
            "confirmed_account",
            "confirmed_account_name",
            "confirmed_engagement",
            "confirmed_engagement_title",
            "confirmed_work_item",
            "ignored_reason",
            "connection_name",
            "attachments",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ConfirmMappingSerializer(serializers.Serializer):
    """Serializer for confirming email mapping (per docs/15 section 5)."""

    account_id = serializers.IntegerField(required=False, allow_null=True)
    engagement_id = serializers.IntegerField(required=False, allow_null=True)
    work_item_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        """At least one mapping must be provided."""
        if not any([data.get("account_id"), data.get("engagement_id"), data.get("work_item_id")]):
            raise serializers.ValidationError("At least one mapping (account, engagement, or work_item) must be provided.")
        return data


class MarkIgnoredSerializer(serializers.Serializer):
    """Serializer for marking email as ignored (per docs/15 section 5)."""

    reason = serializers.CharField(required=True, max_length=500)

    def validate_reason(self, value):
        """Reason must not be empty."""
        if not value.strip():
            raise serializers.ValidationError("Reason cannot be empty.")
        return value.strip()


class IngestionAttemptSerializer(serializers.ModelSerializer):
    """Serializer for IngestionAttempt logs."""

    connection_name = serializers.CharField(source="connection.name", read_only=True)

    class Meta:
        model = IngestionAttempt
        fields = [
            "attempt_id",
            "connection",
            "connection_name",
            "email_artifact",
            "operation",
            "status",
            "error_summary",
            "correlation_id",
            "occurred_at",
            "duration_ms",
        ]
        read_only_fields = fields
