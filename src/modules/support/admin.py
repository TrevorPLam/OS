"""
Admin interface for support module.

Provides Django admin configuration for support/ticketing system models.
"""

from django.contrib import admin
from modules.support.models import (
    SLAPolicy,
    Survey,
    SurveyResponse,
    Ticket,
    TicketComment,
)


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "firm",
        "priority",
        "response_time_hours",
        "resolution_time_hours",
        "business_hours_only",
        "is_active",
    ]
    list_filter = ["firm", "priority", "business_hours_only", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description", "priority")}),
        (
            "SLA Timings",
            {
                "fields": (
                    "response_time_hours",
                    "resolution_time_hours",
                    "business_hours_only",
                )
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        "ticket_number",
        "subject",
        "firm",
        "priority",
        "status",
        "assigned_to",
        "sla_breached",
        "created_at",
    ]
    list_filter = [
        "firm",
        "priority",
        "status",
        "channel",
        "sla_breached",
        "created_at",
    ]
    search_fields = ["ticket_number", "subject", "description", "requester_email"]
    readonly_fields = [
        "ticket_number",
        "created_at",
        "updated_at",
        "first_response_at",
        "resolved_at",
        "closed_at",
        "sla_response_deadline",
        "sla_resolution_deadline",
    ]
    raw_id_fields = ["client", "account", "contact", "related_project", "assigned_to", "created_by"]
    filter_horizontal = ["tags"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "firm",
                    "ticket_number",
                    "subject",
                    "description",
                    "priority",
                    "status",
                    "channel",
                )
            },
        ),
        (
            "Requester Info",
            {"fields": ("requester_name", "requester_email", "client", "account", "contact")},
        ),
        ("Assignment", {"fields": ("assigned_to", "team")}),
        ("SLA Tracking", {"fields": ("sla_policy", "sla_response_deadline", "sla_resolution_deadline", "sla_breached")}),
        (
            "Timeline",
            {
                "fields": (
                    "first_response_at",
                    "resolved_at",
                    "closed_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        ("Related Records", {"fields": ("related_project", "tags")}),
        ("Feedback", {"fields": ("satisfaction_rating", "satisfaction_comment")}),
        ("Metadata", {"fields": ("created_by",)}),
    )


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ["ticket", "created_by", "is_internal_note", "created_at"]
    list_filter = ["is_internal_note", "created_at"]
    search_fields = ["body", "ticket__ticket_number"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["ticket", "created_by"]


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ["name", "firm", "survey_type", "is_active", "created_at"]
    list_filter = ["firm", "survey_type", "is_active", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description", "survey_type")}),
        (
            "Questions",
            {
                "fields": ("questions", "intro_text", "thank_you_text"),
                "description": "Questions should be a JSON array of question objects",
            },
        ),
        (
            "Triggers",
            {
                "fields": ("trigger_on_ticket_resolution", "trigger_on_project_completion"),
                "description": "Automatically send survey when these events occur",
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )
    raw_id_fields = ["created_by"]


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = [
        "survey",
        "respondent_email",
        "nps_score",
        "nps_category",
        "submitted_at",
    ]
    list_filter = ["survey", "nps_category", "submitted_at"]
    search_fields = ["respondent_name", "respondent_email", "ticket__ticket_number"]
    readonly_fields = ["nps_category", "submitted_at"]
    raw_id_fields = ["survey", "ticket", "project", "client", "contact"]
    fieldsets = (
        (None, {"fields": ("survey",)}),
        (
            "Respondent",
            {"fields": ("respondent_name", "respondent_email", "client", "contact")},
        ),
        (
            "Related Records",
            {"fields": ("ticket", "project"), "description": "What triggered this survey"},
        ),
        (
            "Responses",
            {
                "fields": ("responses", "nps_score", "nps_category"),
                "description": "Responses is a JSON object of question_id: answer pairs",
            },
        ),
        ("Metadata", {"fields": ("submitted_at",)}),
    )
