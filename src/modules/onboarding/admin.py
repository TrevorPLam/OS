"""
Admin interface for onboarding module.

Provides Django admin configuration for client onboarding workflow models.
"""

from django.contrib import admin
from modules.onboarding.models import (
    OnboardingDocument,
    OnboardingProcess,
    OnboardingTask,
    OnboardingTemplate,
)


class OnboardingTaskInline(admin.TabularInline):
    model = OnboardingTask
    extra = 0
    fields = [
        "sequence",
        "title",
        "task_type",
        "assigned_to_client",
        "status",
        "due_date",
    ]
    readonly_fields = ["completed_at"]


@admin.register(OnboardingTemplate)
class OnboardingTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "firm",
        "status",
        "estimated_duration_days",
        "times_used",
        "created_at",
    ]
    list_filter = ["firm", "status", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["times_used", "created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description", "service_type")}),
        (
            "Configuration",
            {
                "fields": ("steps", "estimated_duration_days"),
                "description": "steps is a JSON array defining the template tasks",
            },
        ),
        ("Status", {"fields": ("status",)}),
        (
            "Usage Stats",
            {"fields": ("times_used",), "classes": ("collapse",)},
        ),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )
    raw_id_fields = ["created_by"]


@admin.register(OnboardingProcess)
class OnboardingProcessAdmin(admin.ModelAdmin):
    list_display = [
        "client",
        "status",
        "progress_percentage",
        "kickoff_meeting",
        "target_completion_date",
        "created_at",
    ]
    list_filter = ["firm", "status", "created_at"]
    search_fields = ["client__name", "notes"]
    readonly_fields = [
        "progress_percentage",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["firm", "client", "template", "kickoff_meeting", "created_by", "assigned_to"]
    inlines = [OnboardingTaskInline]
    fieldsets = (
        (None, {"fields": ("firm", "client", "template")}),
        ("Assignment", {"fields": ("assigned_to",)}),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "progress_percentage",
                    "started_at",
                    "completed_at",
                )
            },
        ),
        (
            "Scheduling",
            {
                "fields": (
                    "kickoff_meeting",
                    "target_completion_date",
                    "actual_completion_date",
                )
            },
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )


@admin.register(OnboardingTask)
class OnboardingTaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "process",
        "task_type",
        "status",
        "assigned_to_client",
        "due_date",
        "is_blocker",
    ]
    list_filter = ["task_type", "status", "assigned_to_client", "is_blocker"]
    search_fields = ["title", "description", "process__client__name"]
    readonly_fields = ["completed_at", "created_at", "updated_at"]
    raw_id_fields = ["process", "assigned_to", "depends_on"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "process",
                    "sequence",
                    "title",
                    "description",
                    "task_type",
                )
            },
        ),
        ("Assignment", {"fields": ("assigned_to_client", "assigned_to")}),
        (
            "Status & Timing",
            {"fields": ("status", "due_date", "completed_at", "is_blocker")},
        ),
        ("Dependencies", {"fields": ("depends_on",)}),
        (
            "Metadata",
            {
                "fields": (
                    "metadata",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(OnboardingDocument)
class OnboardingDocumentAdmin(admin.ModelAdmin):
    list_display = [
        "document_name",
        "process",
        "status",
        "required",
        "requested_at",
        "received_at",
    ]
    list_filter = ["status", "required", "requested_at", "received_at"]
    search_fields = ["document_name", "description", "process__client__name"]
    readonly_fields = [
        "requested_at",
        "received_at",
        "reviewed_at",
        "approved_at",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["process", "uploaded_document", "reviewed_by", "approved_by"]
    fieldsets = (
        (
            None,
            {"fields": ("process", "document_name", "description", "document_type")},
        ),
        ("Requirements", {"fields": ("required",)}),
        (
            "Status & Timeline",
            {
                "fields": (
                    "status",
                    "requested_at",
                    "received_at",
                    "reviewed_at",
                    "approved_at",
                )
            },
        ),
        (
            "Document",
            {"fields": ("uploaded_document", "rejection_reason"), "classes": ("collapse",)},
        ),
        ("Review", {"fields": ("reviewed_by", "approved_by")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )
