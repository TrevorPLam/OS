"""
Serializers for onboarding module.

Provides DRF serializers for client onboarding models.
"""

from rest_framework import serializers
from modules.onboarding.models import (
    OnboardingTemplate,
    OnboardingProcess,
    OnboardingTask,
    OnboardingDocument,
)


class OnboardingTemplateSerializer(serializers.ModelSerializer):
    """Serializer for onboarding templates."""

    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = OnboardingTemplate
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "service_type",
            "steps",
            "estimated_duration_days",
            "status",
            "times_used",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "times_used", "created_at", "updated_at", "created_by_name"]


class OnboardingTaskSerializer(serializers.ModelSerializer):
    """Serializer for onboarding tasks."""

    completed_by_name = serializers.CharField(source="completed_by.get_full_name", read_only=True)

    class Meta:
        model = OnboardingTask
        fields = [
            "id",
            "process",
            "name",
            "description",
            "task_type",
            "status",
            "step_number",
            "depends_on",
            "is_required",
            "assigned_to_client",
            "due_date",
            "completed_at",
            "completed_by",
            "completed_by_name",
            "reminder_sent",
            "last_reminder_sent_at",
            "related_document",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "completed_at",
            "reminder_sent",
            "last_reminder_sent_at",
            "created_at",
            "updated_at",
            "completed_by_name",
        ]


class OnboardingDocumentSerializer(serializers.ModelSerializer):
    """Serializer for onboarding documents."""

    reviewed_by_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True)

    class Meta:
        model = OnboardingDocument
        fields = [
            "id",
            "process",
            "task",
            "document_name",
            "description",
            "document_type",
            "status",
            "is_required",
            "document",
            "requested_at",
            "received_at",
            "approved_at",
            "reviewed_by",
            "reviewed_by_name",
            "review_notes",
            "reminder_count",
            "last_reminder_sent_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "requested_at",
            "received_at",
            "approved_at",
            "reminder_count",
            "last_reminder_sent_at",
            "created_at",
            "updated_at",
            "reviewed_by_name",
        ]


class OnboardingProcessSerializer(serializers.ModelSerializer):
    """Serializer for onboarding processes (list view)."""

    template_name = serializers.CharField(source="template.name", read_only=True)
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = OnboardingProcess
        fields = [
            "id",
            "firm",
            "template",
            "template_name",
            "client",
            "client_name",
            "name",
            "status",
            "assigned_to",
            "assigned_to_name",
            "started_at",
            "target_completion_date",
            "completed_at",
            "total_tasks",
            "completed_tasks",
            "progress_percentage",
            "kickoff_scheduled",
            "kickoff_completed",
            "kickoff_appointment",
            "notes",
            "blockers",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "id",
            "started_at",
            "completed_at",
            "total_tasks",
            "completed_tasks",
            "progress_percentage",
            "created_at",
            "updated_at",
            "template_name",
            "client_name",
            "assigned_to_name",
            "created_by_name",
        ]


class OnboardingProcessDetailSerializer(OnboardingProcessSerializer):
    """Detailed serializer for onboarding processes (includes tasks and documents)."""

    tasks = OnboardingTaskSerializer(many=True, read_only=True)
    document_requirements = OnboardingDocumentSerializer(many=True, read_only=True)

    class Meta(OnboardingProcessSerializer.Meta):
        fields = OnboardingProcessSerializer.Meta.fields + ["tasks", "document_requirements"]
