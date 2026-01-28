"""
Serializers for support module.

Provides DRF serializers for support/ticketing system models.
"""

from rest_framework import serializers
from modules.support.models import (
    SLAPolicy,
    Survey,
    SurveyResponse,
    Ticket,
    TicketComment,
)


class SLAPolicySerializer(serializers.ModelSerializer):
    """Serializer for SLA policies."""

    class Meta:
        model = SLAPolicy
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "priority",
            "response_time_hours",
            "resolution_time_hours",
            "business_hours_only",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets."""

    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    sla_policy_name = serializers.CharField(source="sla_policy.name", read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "firm",
            "ticket_number",
            "subject",
            "description",
            "priority",
            "status",
            "channel",
            "requester_name",
            "requester_email",
            "client",
            "account",
            "contact",
            "assigned_to",
            "assigned_to_name",
            "team",
            "sla_policy",
            "sla_policy_name",
            "sla_response_deadline",
            "sla_resolution_deadline",
            "sla_breached",
            "first_response_at",
            "resolved_at",
            "closed_at",
            "related_project",
            "tags",
            "satisfaction_rating",
            "satisfaction_comment",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "id",
            "ticket_number",
            "sla_response_deadline",
            "sla_resolution_deadline",
            "sla_breached",
            "first_response_at",
            "resolved_at",
            "closed_at",
            "created_at",
            "updated_at",
            "assigned_to_name",
            "created_by_name",
            "sla_policy_name",
        ]


class TicketCommentSerializer(serializers.ModelSerializer):
    """Serializer for ticket comments."""

    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = TicketComment
        fields = [
            "id",
            "ticket",
            "body",
            "is_internal_note",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by_name"]


class SurveySerializer(serializers.ModelSerializer):
    """Serializer for surveys."""

    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = Survey
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "survey_type",
            "questions",
            "intro_text",
            "thank_you_text",
            "trigger_on_ticket_resolution",
            "trigger_on_project_completion",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by_name"]


class SurveyResponseSerializer(serializers.ModelSerializer):
    """Serializer for survey responses."""

    survey_name = serializers.CharField(source="survey.name", read_only=True)

    class Meta:
        model = SurveyResponse
        fields = [
            "id",
            "survey",
            "survey_name",
            "ticket",
            "project",
            "client",
            "contact",
            "respondent_name",
            "respondent_email",
            "responses",
            "nps_score",
            "nps_category",
            "submitted_at",
        ]
        read_only_fields = ["id", "nps_category", "submitted_at"]
