from django.contrib import admin
from .models import Firm, FirmMembership, BreakGlassSession, PlatformUserProfile, AuditEvent


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'subscription_tier', 'current_users_count', 'current_clients_count', 'created_at')
    list_filter = ('status', 'subscription_tier', 'created_at')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at', 'current_users_count', 'current_clients_count', 'current_storage_gb')
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug')
        }),
        ('Subscription', {
            'fields': ('status', 'subscription_tier', 'trial_ends_at')
        }),
        ('Settings', {
            'fields': ('timezone', 'currency')
        }),
        ('Limits & Quotas', {
            'fields': ('max_users', 'max_clients', 'max_storage_gb')
        }),
        ('Usage', {
            'fields': ('current_users_count', 'current_clients_count', 'current_storage_gb')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at', 'notes')
        }),
    )


@admin.register(FirmMembership)
class FirmMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'firm', 'role', 'is_active', 'invited_at')
    list_filter = ('role', 'is_active', 'invited_at')
    search_fields = ('user__username', 'user__email', 'firm__name')
    readonly_fields = ('invited_at', 'invited_by')
    fieldsets = (
        ('Membership', {
            'fields': ('firm', 'user', 'role', 'is_active')
        }),
        ('Permissions', {
            'fields': ('can_manage_users', 'can_manage_clients', 'can_manage_billing', 'can_manage_settings', 'can_view_reports')
        }),
        ('Audit', {
            'fields': ('invited_by', 'invited_at', 'last_active_at')
        }),
    )


@admin.register(BreakGlassSession)
class BreakGlassSessionAdmin(admin.ModelAdmin):
    list_display = ('firm', 'operator', 'status', 'activated_at', 'expires_at', 'reviewed_at')
    list_filter = ('status', 'activated_at', 'expires_at', 'reviewed_at')
    search_fields = ('firm__name', 'operator__username', 'operator__email', 'reason')
    readonly_fields = ('activated_at',)
    fieldsets = (
        ('Scope', {
            'fields': ('firm', 'operator', 'impersonated_user')
        }),
        ('Activation', {
            'fields': ('reason', 'status', 'activated_at', 'expires_at')
        }),
        ('Revocation', {
            'fields': ('revoked_at', 'revoked_reason')
        }),
        ('Review', {
            'fields': ('reviewed_at', 'reviewed_by')
        }),
    )


@admin.register(PlatformUserProfile)
class PlatformUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform_role', 'is_platform_active', 'can_activate_break_glass', 'granted_at', 'revoked_at')
    list_filter = ('platform_role', 'is_platform_active', 'can_activate_break_glass', 'granted_at')
    search_fields = ('user__username', 'user__email', 'notes')
    readonly_fields = ('granted_at', 'revoked_at')
    fieldsets = (
        ('User & Role', {
            'fields': ('user', 'platform_role', 'is_platform_active')
        }),
        ('Permissions', {
            'fields': ('can_activate_break_glass',),
            'description': 'Explicit permission to activate break-glass sessions (required for break-glass operators)'
        }),
        ('Audit', {
            'fields': ('granted_by', 'granted_at', 'revoked_by', 'revoked_at', 'notes')
        }),
    )


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditEvent (read-only, immutable).

    TIER 3 REQUIREMENT: Audit events are immutable and cannot be modified or deleted
    via the Django admin interface. This enforces audit integrity.
    """
    list_display = ('timestamp', 'firm', 'category', 'action', 'actor', 'severity', 'retention_until')
    list_filter = ('category', 'severity', 'timestamp', 'retention_until')
    search_fields = ('action', 'actor__username', 'actor__email', 'firm__name', 'reason', 'target_description')
    readonly_fields = (
        'firm', 'category', 'action', 'severity',
        'actor', 'actor_ip', 'actor_user_agent',
        'target_content_type', 'target_object_id', 'target_description',
        'client', 'reason', 'metadata',
        'timestamp', 'retention_until'
    )
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Event Classification', {
            'fields': ('category', 'action', 'severity', 'timestamp')
        }),
        ('Tenant Context', {
            'fields': ('firm', 'client')
        }),
        ('Actor (Who)', {
            'fields': ('actor', 'actor_ip', 'actor_user_agent')
        }),
        ('Target (What)', {
            'fields': ('target_content_type', 'target_object_id', 'target_description')
        }),
        ('Details', {
            'fields': ('reason', 'metadata')
        }),
        ('Retention', {
            'fields': ('retention_until',),
            'description': 'When this event can be deleted per retention policy (null = keep forever)'
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation via admin (use create_audit_event helper)."""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing (immutable records)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion via admin (use retention cleanup jobs)."""
        return False

    def get_actions(self, request):
        """Remove bulk delete action."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
