"""Admin configuration for email ingestion."""

from django.contrib import admin
from .models import EmailConnection, EmailArtifact, EmailAttachment, IngestionAttempt


@admin.register(EmailConnection)
class EmailConnectionAdmin(admin.ModelAdmin):
    """Admin for EmailConnection."""

    list_display = ["name", "email_address", "provider", "firm", "is_active", "last_sync_at"]
    list_filter = ["provider", "is_active", "firm"]
    search_fields = ["name", "email_address"]
    readonly_fields = ["created_at", "updated_at", "last_sync_at"]
    fieldsets = [
        (
            "Connection Info",
            {
                "fields": [
                    "firm",
                    "name",
                    "provider",
                    "email_address",
                    "is_active",
                ]
            },
        ),
        (
            "Credentials",
            {
                "fields": ["credentials_encrypted"],
                "classes": ["collapse"],
            },
        ),
        (
            "Audit",
            {
                "fields": ["created_by", "created_at", "updated_at", "last_sync_at"],
            },
        ),
    ]


@admin.register(EmailArtifact)
class EmailArtifactAdmin(admin.ModelAdmin):
    """Admin for EmailArtifact."""

    list_display = [
        "email_artifact_id",
        "subject_preview",
        "from_address",
        "sent_at",
        "status",
        "mapping_confidence",
        "firm",
    ]
    list_filter = ["status", "provider", "firm", "sent_at"]
    search_fields = ["subject", "from_address", "to_addresses", "external_message_id"]
    readonly_fields = [
        "email_artifact_id",
        "created_at",
        "updated_at",
        "reviewed_at",
        "mapping_confidence",
        "mapping_reasons",
    ]
    fieldsets = [
        (
            "Email Metadata",
            {
                "fields": [
                    "email_artifact_id",
                    "firm",
                    "connection",
                    "provider",
                    "external_message_id",
                    "thread_id",
                ]
            },
        ),
        (
            "Email Content",
            {
                "fields": [
                    "from_address",
                    "to_addresses",
                    "cc_addresses",
                    "subject",
                    "body_preview",
                    "sent_at",
                    "received_at",
                    "storage_ref",
                ]
            },
        ),
        (
            "Status & Mapping",
            {
                "fields": [
                    "status",
                    "ignored_reason",
                ]
            },
        ),
        (
            "Suggested Mapping",
            {
                "fields": [
                    "suggested_account",
                    "suggested_engagement",
                    "suggested_work_item",
                    "mapping_confidence",
                    "mapping_reasons",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Confirmed Mapping",
            {
                "fields": [
                    "confirmed_account",
                    "confirmed_engagement",
                    "confirmed_work_item",
                ],
            },
        ),
        (
            "Audit",
            {
                "fields": [
                    "reviewed_by",
                    "reviewed_at",
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    ]

    def subject_preview(self, obj):
        """Show truncated subject in list view."""
        return obj.subject[:60] + "..." if len(obj.subject) > 60 else obj.subject

    subject_preview.short_description = "Subject"


@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    """Admin for EmailAttachment."""

    list_display = [
        "original_filename",
        "email_artifact",
        "content_type",
        "size_bytes",
        "attachment_index",
    ]
    list_filter = ["content_type"]
    search_fields = ["original_filename", "email_artifact__subject"]
    readonly_fields = ["created_at"]


@admin.register(IngestionAttempt)
class IngestionAttemptAdmin(admin.ModelAdmin):
    """Admin for IngestionAttempt."""

    list_display = [
        "attempt_id",
        "operation",
        "status",
        "connection",
        "occurred_at",
        "duration_ms",
    ]
    list_filter = ["operation", "status", "firm", "occurred_at"]
    search_fields = ["correlation_id", "error_summary"]
    readonly_fields = ["attempt_id", "occurred_at", "duration_ms", "correlation_id"]
    fieldsets = [
        (
            "Attempt Info",
            {
                "fields": [
                    "attempt_id",
                    "firm",
                    "connection",
                    "email_artifact",
                    "operation",
                    "status",
                    "correlation_id",
                ]
            },
        ),
        (
            "Error Details",
            {
                "fields": ["error_summary"],
                "classes": ["collapse"],
            },
        ),
        (
            "Timing",
            {
                "fields": ["occurred_at", "duration_ms"],
            },
        ),
    ]
