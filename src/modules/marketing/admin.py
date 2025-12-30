"""
Admin interface for marketing module.

Provides Django admin configuration for marketing automation models.
"""

from django.contrib import admin
from modules.marketing.models import (
    CampaignExecution,
    EmailTemplate,
    EntityTag,
    Segment,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "firm", "category", "color", "usage_count", "created_at"]
    list_filter = ["firm", "category", "created_at"]
    search_fields = ["name", "slug", "description"]
    readonly_fields = ["slug", "usage_count", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("firm", "name", "slug", "description", "category")}),
        ("Display", {"fields": ("color",)}),
        ("Usage", {"fields": ("usage_count",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )
    raw_id_fields = ["created_by"]


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "firm",
        "status",
        "auto_update",
        "member_count",
        "last_refreshed_at",
    ]
    list_filter = ["firm", "status", "auto_update", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["member_count", "last_refreshed_at", "created_at", "updated_at"]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description")}),
        (
            "Criteria",
            {
                "fields": ("criteria",),
                "description": "JSON object defining segmentation rules (tags, lead_score, status, etc.)",
            },
        ),
        (
            "Membership",
            {
                "fields": ("auto_update", "member_count", "last_refreshed_at"),
            },
        ),
        ("Status", {"fields": ("status",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )
    raw_id_fields = ["created_by"]


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "firm",
        "template_type",
        "status",
        "avg_open_rate",
        "avg_click_rate",
        "times_used",
    ]
    list_filter = ["firm", "template_type", "status", "created_at"]
    search_fields = ["name", "subject_line", "description"]
    readonly_fields = [
        "avg_open_rate",
        "avg_click_rate",
        "times_used",
        "last_used_at",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description", "template_type")}),
        (
            "Email Content",
            {
                "fields": ("subject_line", "preheader_text", "html_content", "plain_text_content"),
            },
        ),
        (
            "Design",
            {
                "fields": ("design_json",),
                "description": "JSON representation for drag-and-drop email builder",
                "classes": ("collapse",),
            },
        ),
        (
            "Performance",
            {
                "fields": (
                    "avg_open_rate",
                    "avg_click_rate",
                    "times_used",
                    "last_used_at",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Status", {"fields": ("status",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )
    raw_id_fields = ["created_by"]


@admin.register(CampaignExecution)
class CampaignExecutionAdmin(admin.ModelAdmin):
    list_display = [
        "campaign",
        "template",
        "status",
        "emails_sent",
        "open_rate",
        "click_rate",
        "scheduled_at",
    ]
    list_filter = ["status", "scheduled_at", "sent_at"]
    search_fields = ["campaign__name", "notes"]
    readonly_fields = [
        "open_rate",
        "click_rate",
        "bounce_rate",
        "unsubscribe_rate",
        "sent_at",
        "completed_at",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["campaign", "template", "segment", "created_by"]
    fieldsets = (
        (None, {"fields": ("campaign", "template", "segment")}),
        (
            "Execution Details",
            {"fields": ("scheduled_at", "sent_at", "completed_at", "status")},
        ),
        (
            "Email Counts",
            {
                "fields": (
                    "emails_sent",
                    "emails_failed",
                    "emails_opened",
                    "emails_clicked",
                    "emails_bounced",
                    "emails_unsubscribed",
                )
            },
        ),
        (
            "Performance Rates",
            {
                "fields": (
                    "open_rate",
                    "click_rate",
                    "bounce_rate",
                    "unsubscribe_rate",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "A/B Testing",
            {
                "fields": ("ab_test_variant",),
                "description": "Variant identifier for split testing (e.g., 'A', 'B', 'control')",
                "classes": ("collapse",),
            },
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )


@admin.register(EntityTag)
class EntityTagAdmin(admin.ModelAdmin):
    list_display = [
        "tag",
        "entity_type",
        "entity_id",
        "applied_by",
        "auto_tagged",
        "created_at",
    ]
    list_filter = ["entity_type", "auto_tagged", "created_at"]
    search_fields = ["tag__name", "entity_id"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["tag", "applied_by"]
    fieldsets = (
        (None, {"fields": ("tag", "entity_type", "entity_id")}),
        (
            "Application Details",
            {
                "fields": ("applied_by", "auto_tagged", "auto_tag_rule"),
                "description": "auto_tag_rule stores the rule that triggered automatic tagging",
            },
        ),
        ("Metadata", {"fields": ("created_at",)}),
    )
