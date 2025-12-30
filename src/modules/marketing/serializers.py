"""
Serializers for marketing module.

Provides DRF serializers for marketing automation models.
"""

from rest_framework import serializers
from modules.marketing.models import (
    Tag,
    Segment,
    EmailTemplate,
    CampaignExecution,
    EntityTag,
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = Tag
        fields = [
            "id",
            "firm",
            "name",
            "slug",
            "description",
            "category",
            "color",
            "usage_count",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "usage_count", "created_at", "updated_at", "created_by_name"]


class SegmentSerializer(serializers.ModelSerializer):
    """Serializer for segments."""

    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = Segment
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "criteria",
            "status",
            "auto_update",
            "last_refreshed_at",
            "member_count",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "id",
            "last_refreshed_at",
            "member_count",
            "created_at",
            "updated_at",
            "created_by_name",
        ]


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for email templates."""

    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "template_type",
            "subject_line",
            "preheader_text",
            "html_content",
            "plain_text_content",
            "design_json",
            "available_merge_fields",
            "status",
            "times_used",
            "last_used_at",
            "avg_open_rate",
            "avg_click_rate",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "id",
            "times_used",
            "last_used_at",
            "avg_open_rate",
            "avg_click_rate",
            "created_at",
            "updated_at",
            "created_by_name",
        ]


class CampaignExecutionSerializer(serializers.ModelSerializer):
    """Serializer for campaign executions."""

    campaign_name = serializers.CharField(source="campaign.name", read_only=True)
    email_template_name = serializers.CharField(source="email_template.name", read_only=True)
    segment_name = serializers.CharField(source="segment.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = CampaignExecution
        fields = [
            "id",
            "campaign",
            "campaign_name",
            "email_template",
            "email_template_name",
            "segment",
            "segment_name",
            "recipient_count",
            "status",
            "scheduled_for",
            "started_at",
            "completed_at",
            "emails_sent",
            "emails_failed",
            "emails_opened",
            "emails_clicked",
            "emails_bounced",
            "emails_unsubscribed",
            "open_rate",
            "click_rate",
            "bounce_rate",
            "is_ab_test",
            "ab_variant",
            "error_message",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "id",
            "started_at",
            "completed_at",
            "emails_sent",
            "emails_failed",
            "emails_opened",
            "emails_clicked",
            "emails_bounced",
            "emails_unsubscribed",
            "open_rate",
            "click_rate",
            "bounce_rate",
            "created_at",
            "updated_at",
            "campaign_name",
            "email_template_name",
            "segment_name",
            "created_by_name",
        ]


class EntityTagSerializer(serializers.ModelSerializer):
    """Serializer for entity tags."""

    tag_name = serializers.CharField(source="tag.name", read_only=True)
    applied_by_name = serializers.CharField(source="applied_by.get_full_name", read_only=True)

    class Meta:
        model = EntityTag
        fields = [
            "id",
            "tag",
            "tag_name",
            "entity_type",
            "entity_id",
            "applied_by",
            "applied_by_name",
            "applied_at",
            "auto_applied",
            "auto_rule_id",
        ]
        read_only_fields = ["id", "applied_at", "tag_name", "applied_by_name"]
