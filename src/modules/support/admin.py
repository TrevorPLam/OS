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
        "first_response_minutes",
        "resolution_minutes",
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
                    "first_response_minutes",
                    "resolution_minutes",
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
        "first_response_sla_breached",
        "created_at",
    ]
    list_filter = [
        "firm",
        "priority",
        "status",
        "channel",
        "first_response_sla_breached",
        "resolution_sla_breached",
        "created_at",
    ]
    search_fields = ["ticket_number", "subject", "description", "contact_email"]
    readonly_fields = [
        "ticket_number",
        "created_at",
        "updated_at",
        "first_response_at",
        "resolved_at",
        "closed_at",
    ]
    raw_id_fields = ["client", "assigned_to", "sla_policy", "related_conversation"]
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
            {"fields": ("contact_name", "contact_email", "client")},
        ),
        ("Assignment", {"fields": ("assigned_to", "assigned_team")}),
        ("SLA Tracking", {"fields": ("sla_policy", "first_response_sla_breached", "resolution_sla_breached")}),
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
        ("Related Records", {"fields": ("related_conversation", "category", "tags")}),
        ("Feedback", {"fields": ("satisfaction_rating", "satisfaction_comment")}),
    )


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ["ticket", "created_by", "is_internal", "created_at"]
    list_filter = ["is_internal", "is_customer_reply", "created_at"]
    search_fields = ["body", "ticket__ticket_number", "customer_name", "customer_email"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["ticket", "created_by"]

    fieldsets = (
        (
            "Comment",
            {
                "fields": ("ticket", "body", "is_internal", "is_customer_reply"),
            },
        ),
        (
            "Author",
            {
                "fields": ("created_by", "customer_name", "customer_email"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ["name", "firm", "survey_type", "status", "created_at"]
    list_filter = ["firm", "survey_type", "status", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description", "survey_type", "status")}),
        (
            "Questions",
            {
                "fields": ("introduction_text", "questions", "thank_you_text"),
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
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )
    raw_id_fields = ["created_by"]


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = [
        "survey",
        "contact_email",
        "nps_score",
        "nps_category",
        "submitted_at",
    ]
    list_filter = ["survey", "nps_category", "submitted_at"]
    search_fields = ["contact_name", "contact_email"]
    readonly_fields = ["nps_category", "submitted_at"]
    raw_id_fields = ["survey", "client"]
    fieldsets = (
        (None, {"fields": ("survey",)}),
        (
            "Respondent",
            {"fields": ("contact_name", "contact_email", "client")},
        ),
        (
            "Responses",
            {
                "fields": ("answers", "nps_score", "nps_category"),
                "description": "Answers is a JSON object of question_id: answer pairs",
            },
        ),
        ("Metadata", {"fields": ("submitted_at",)}),
    )
