"""Knowledge System Admin (DOC-35.1)."""

from django.contrib import admin
from .models import KnowledgeItem, KnowledgeVersion, KnowledgeReview, KnowledgeAttachment


@admin.register(KnowledgeItem)
class KnowledgeItemAdmin(admin.ModelAdmin):
    list_display = ["title", "type", "status", "version_number", "owner", "published_at"]
    list_filter = ["type", "status", "access_level", "category"]
    search_fields = ["title", "summary", "content"]
    readonly_fields = ["version_number", "published_at", "deprecated_at", "created_at", "updated_at"]


@admin.register(KnowledgeVersion)
class KnowledgeVersionAdmin(admin.ModelAdmin):
    list_display = ["knowledge_item", "version_number", "created_at", "created_by"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]


@admin.register(KnowledgeReview)
class KnowledgeReviewAdmin(admin.ModelAdmin):
    list_display = ["knowledge_item", "reviewer", "decision", "requested_at", "reviewed_at"]
    list_filter = ["decision", "requested_at"]
    readonly_fields = ["requested_at", "reviewed_at"]


@admin.register(KnowledgeAttachment)
class KnowledgeAttachmentAdmin(admin.ModelAdmin):
    list_display = ["knowledge_item", "attachment_type", "created_at"]
    list_filter = ["attachment_type"]
    readonly_fields = ["created_at"]
