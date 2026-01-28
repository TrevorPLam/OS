"""
Django Admin configuration for Documents models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Document,
    DocumentAccessLog,
    DocumentLock,
    ExternalShare,
    Folder,
    ShareAccess,
    SharePermission,
    Version,
)


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ["name", "client", "project", "parent", "visibility", "created_at"]
    list_filter = ["visibility", "created_at", "client"]
    search_fields = ["name", "client__company_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Folder Information", {"fields": ("name", "description", "client", "project", "parent", "visibility")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "folder",
        "client",
        "file_type",
        "file_size_bytes",
        "current_version",
        "visibility",
        "created_at",
    ]
    list_filter = ["visibility", "file_type", "created_at"]
    search_fields = ["name", "client__company_name", "s3_key"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Document Information", {"fields": ("name", "description", "folder", "client", "project", "visibility")}),
        ("File Details", {"fields": ("file_type", "file_size_bytes", "current_version")}),
        ("S3 Storage", {"fields": ("s3_bucket", "s3_key")}),
        ("Audit", {"fields": ("uploaded_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ["document", "version_number", "file_type", "file_size_bytes", "uploaded_by", "created_at"]
    list_filter = ["created_at", "file_type"]
    search_fields = ["document__name", "change_summary"]
    readonly_fields = ["created_at"]
    fieldsets = (
        ("Version Information", {"fields": ("document", "version_number", "change_summary")}),
        ("File Details", {"fields": ("file_type", "file_size_bytes")}),
        ("S3 Storage", {"fields": ("s3_bucket", "s3_key")}),
        ("Audit", {"fields": ("uploaded_by", "created_at"), "classes": ("collapse",)}),
    )


@admin.register(ExternalShare)
class ExternalShareAdmin(admin.ModelAdmin):
    """Admin interface for ExternalShare model (Task 3.10)."""
    
    list_display = [
        "document",
        "share_token_display",
        "access_type",
        "created_by",
        "is_active_display",
        "download_count",
        "created_at",
    ]
    list_filter = ["access_type", "require_password", "revoked", "created_at"]
    search_fields = ["document__name", "share_token", "created_by__username"]
    readonly_fields = [
        "share_token",
        "download_count",
        "created_at",
        "updated_at",
        "revoked_at",
        "share_url_display",
    ]
    
    fieldsets = (
        (
            "Document & Token",
            {
                "fields": (
                    "document",
                    "share_token",
                    "share_url_display",
                )
            },
        ),
        (
            "Access Configuration",
            {
                "fields": (
                    "access_type",
                    "require_password",
                    "expires_at",
                    "max_downloads",
                    "download_count",
                )
            },
        ),
        (
            "Revocation",
            {
                "fields": (
                    "revoked",
                    "revoked_at",
                    "revoked_by",
                    "revoke_reason",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    
    actions = ["revoke_shares"]
    
    def share_token_display(self, obj):
        """Display truncated share token."""
        token_str = str(obj.share_token)
        return f"{token_str[:8]}...{token_str[-8:]}"
    share_token_display.short_description = "Share Token"
    
    def is_active_display(self, obj):
        """Display active status with color coding."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        elif obj.revoked:
            return format_html('<span style="color: red;">✗ Revoked</span>')
        elif obj.is_expired:
            return format_html('<span style="color: orange;">✗ Expired</span>')
        elif obj.is_download_limit_reached:
            return format_html('<span style="color: orange;">✗ Limit Reached</span>')
        return format_html('<span style="color: gray;">✗ Inactive</span>')
    is_active_display.short_description = "Status"
    
    def share_url_display(self, obj):
        """Display the full share URL."""
        if obj.share_token:
            # Note: In production, use proper domain from settings
            url = f"/api/public/shares/{obj.share_token}/"
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "-"
    share_url_display.short_description = "Share URL"
    
    def revoke_shares(self, request, queryset):
        """Admin action to revoke selected shares."""
        count = 0
        for share in queryset:
            if not share.revoked:
                share.revoke(user=request.user, reason="Revoked by admin")
                count += 1
        self.message_user(request, f"Successfully revoked {count} share(s).")
    revoke_shares.short_description = "Revoke selected shares"


@admin.register(SharePermission)
class SharePermissionAdmin(admin.ModelAdmin):
    """Admin interface for SharePermission model (Task 3.10)."""
    
    list_display = [
        "external_share",
        "allow_print",
        "allow_copy",
        "apply_watermark",
        "notify_on_access",
    ]
    list_filter = ["allow_print", "allow_copy", "apply_watermark", "notify_on_access"]
    search_fields = ["external_share__share_token", "external_share__document__name"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (
            "External Share",
            {
                "fields": ("external_share",)
            },
        ),
        (
            "Permission Flags",
            {
                "fields": (
                    "allow_print",
                    "allow_copy",
                )
            },
        ),
        (
            "Watermark Settings",
            {
                "fields": (
                    "apply_watermark",
                    "watermark_text",
                    "watermark_settings",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "IP Restrictions",
            {
                "fields": ("allowed_ip_addresses",),
                "classes": ("collapse",),
            },
        ),
        (
            "Notifications",
            {
                "fields": (
                    "notify_on_access",
                    "notification_emails",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ShareAccess)
class ShareAccessAdmin(admin.ModelAdmin):
    """Admin interface for ShareAccess model (Task 3.10)."""
    
    list_display = [
        "external_share",
        "action",
        "success_display",
        "ip_address",
        "accessed_at",
    ]
    list_filter = ["action", "success", "accessed_at"]
    search_fields = [
        "external_share__share_token",
        "external_share__document__name",
        "ip_address",
    ]
    readonly_fields = ["accessed_at"]
    
    fieldsets = (
        (
            "Access Information",
            {
                "fields": (
                    "external_share",
                    "action",
                    "success",
                    "accessed_at",
                )
            },
        ),
        (
            "Request Metadata",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                    "referer",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional Data",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
    )
    
    def success_display(self, obj):
        """Display success status with color coding."""
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    success_display.short_description = "Result"
    
    def has_add_permission(self, request):
        """Prevent manual creation of access logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of access logs."""
        return False


@admin.register(DocumentLock)
class DocumentLockAdmin(admin.ModelAdmin):
    """Admin interface for DocumentLock model."""
    
    list_display = ["document", "locked_by", "locked_at", "expires_at", "is_overridden"]
    list_filter = ["locked_at", "expires_at"]
    search_fields = ["document__name", "locked_by__username"]
    readonly_fields = ["locked_at"]
    
    fieldsets = (
        (
            "Lock Information",
            {
                "fields": (
                    "document",
                    "locked_by",
                    "locked_at",
                    "expires_at",
                    "lock_reason",
                )
            },
        ),
        (
            "Override Tracking",
            {
                "fields": (
                    "override_by",
                    "override_at",
                    "override_reason",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    """Admin interface for DocumentAccessLog model."""
    
    list_display = [
        "document",
        "action",
        "actor_type",
        "actor_user",
        "timestamp",
    ]
    list_filter = ["action", "actor_type", "timestamp"]
    search_fields = ["document__name", "actor_user__username", "correlation_id"]
    readonly_fields = ["timestamp"]
    
    fieldsets = (
        (
            "Access Information",
            {
                "fields": (
                    "document",
                    "version",
                    "action",
                    "timestamp",
                )
            },
        ),
        (
            "Actor Information",
            {
                "fields": (
                    "actor_type",
                    "actor_user",
                    "actor_portal_user_id",
                )
            },
        ),
        (
            "Tracing",
            {
                "fields": (
                    "correlation_id",
                    "ip_address",
                    "user_agent",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of access logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of access logs."""
        return False
