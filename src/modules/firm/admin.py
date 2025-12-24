from django.contrib import admin
from .models import Firm, FirmMembership, BreakGlassSession, UserProfile


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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile.
    
    TIER 0.5: Platform role assignment is sensitive.
    Only superusers should be able to assign platform roles.
    """
    list_display = ('user', 'platform_role', 'timezone', 'created_at')
    list_filter = ('platform_role', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Platform Role (Sensitive)', {
            'fields': ('platform_role',),
            'description': (
                'Platform roles grant special access. '
                'Operator = metadata-only access. '
                'Break-Glass = can activate break-glass sessions for content access.'
            )
        }),
        ('Preferences', {
            'fields': ('timezone',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_change_permission(self, request, obj=None):
        """Only superusers can change platform roles."""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete profiles."""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Only superusers can manually create profiles."""
        return request.user.is_superuser

