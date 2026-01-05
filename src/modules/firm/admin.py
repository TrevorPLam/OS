from django.contrib import admin

from modules.firm.audit import AuditEvent
from modules.firm.profile_extensions import UserProfile
from .models import BreakGlassSession, Firm, FirmMembership, PlatformUserProfile


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "status",
        "subscription_tier",
        "current_users_count",
        "current_clients_count",
        "created_at",
    )
    list_filter = ("status", "subscription_tier", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at", "current_users_count", "current_clients_count", "current_storage_gb")
    fieldsets = (
        ("Identity", {"fields": ("name", "slug")}),
        ("Subscription", {"fields": ("status", "subscription_tier", "trial_ends_at")}),
        ("Settings", {"fields": ("timezone", "currency")}),
        ("Limits & Quotas", {"fields": ("max_users", "max_clients", "max_storage_gb")}),
        ("Usage", {"fields": ("current_users_count", "current_clients_count", "current_storage_gb")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at", "notes")}),
    )

    def save_model(self, request, obj, form, change):
        if change:
            updates = {field: form.cleaned_data[field] for field in form.changed_data if field in Firm.CONFIG_FIELDS}
            if updates:
                obj.apply_config_update(
                    actor=request.user,
                    updates=updates,
                    reason="Updated via admin",
                )
                return
        super().save_model(request, obj, form, change)


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'firm_membership'

    fieldsets = (
        (
            'Visual Identity',
            {
                'fields': (
                    'profile_photo',
                    'job_title',
                    'bio',
                )
            }
        ),
        (
            'Email Signature',
            {
                'fields': (
                    'email_signature_html',
                    'email_signature_plain',
                    'include_signature_by_default',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            'Meeting & Scheduling',
            {
                'fields': (
                    'personal_meeting_link',
                    'meeting_link_description',
                    'calendar_booking_link',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            'Contact Information',
            {
                'fields': (
                    'phone_number',
                    'phone_extension',
                    'mobile_number',
                    'office_location',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            'Social & Professional Links',
            {
                'fields': (
                    'linkedin_url',
                    'twitter_handle',
                    'website_url',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            'Preferences',
            {
                'fields': (
                    'timezone_preference',
                    'language_preference',
                    'notification_preferences',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            'Visibility Settings',
            {
                'fields': (
                    'show_phone_in_directory',
                    'show_email_in_directory',
                    'show_availability_to_clients',
                ),
                'classes': ('collapse',)
            }
        ),
    )


@admin.register(FirmMembership)
class FirmMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "firm", "role", "is_active", "invited_at")
    list_filter = ("role", "is_active", "invited_at")
    search_fields = ("user__username", "user__email", "firm__name")
    readonly_fields = ("invited_at", "invited_by")
    inlines = [UserProfileInline]
    fieldsets = (
        ("Membership", {"fields": ("firm", "user", "role", "is_active")}),
        (
            "Permissions",
            {
                "fields": (
                    "can_manage_users",
                    "can_manage_clients",
                    "can_manage_billing",
                    "can_manage_settings",
                    "can_view_reports",
                )
            },
        ),
        ("Audit", {"fields": ("invited_by", "invited_at", "last_active_at")}),
    )


@admin.register(BreakGlassSession)
class BreakGlassSessionAdmin(admin.ModelAdmin):
    list_display = ("firm", "operator", "status", "activated_at", "expires_at", "reviewed_at")
    list_filter = ("status", "activated_at", "expires_at", "reviewed_at")
    search_fields = ("firm__name", "operator__username", "operator__email", "reason")
    readonly_fields = ("activated_at",)
    fieldsets = (
        ("Scope", {"fields": ("firm", "operator", "impersonated_user")}),
        ("Activation", {"fields": ("reason", "status", "activated_at", "expires_at")}),
        ("Revocation", {"fields": ("revoked_at", "revoked_reason")}),
        ("Review", {"fields": ("reviewed_at", "reviewed_by")}),
    )


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "firm",
        "category",
        "action",
        "severity",
        "actor_email",
        "target_model",
        "outcome",
    )
    list_filter = (
        "firm",
        "category",
        "severity",
        "outcome",
        "timestamp",
    )
    search_fields = (
        "action",
        "actor_email",
        "target_model",
        "target_id",
        "request_id",
    )
    readonly_fields = (
        "firm",
        "category",
        "action",
        "severity",
        "actor",
        "actor_email",
        "actor_role",
        "target_model",
        "target_id",
        "target_repr",
        "timestamp",
        "reason",
        "outcome",
        "metadata",
        "ip_address",
        "user_agent",
        "request_id",
        "reviewed_at",
        "reviewed_by",
        "review_notes",
    )
    date_hierarchy = "timestamp"


@admin.register(PlatformUserProfile)
class PlatformUserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "platform_role",
        "is_platform_active",
        "can_activate_break_glass",
        "granted_at",
        "revoked_at",
    )
    list_filter = ("platform_role", "is_platform_active", "can_activate_break_glass", "granted_at")
    search_fields = ("user__username", "user__email", "notes")
    readonly_fields = ("granted_at", "revoked_at")
    fieldsets = (
        ("User & Role", {"fields": ("user", "platform_role", "is_platform_active")}),
        (
            "Permissions",
            {
                "fields": ("can_activate_break_glass",),
                "description": (
                    "Explicit permission to activate break-glass sessions "
                    "(required for break-glass operators)"
                ),
            },
        ),
        ("Audit", {"fields": ("granted_by", "granted_at", "revoked_by", "revoked_at", "notes")}),
    )
