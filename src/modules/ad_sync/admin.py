"""
Active Directory Synchronization Admin Interface
"""

from django.contrib import admin
from django.utils.html import format_html

from modules.ad_sync.models import (
    ADGroupMapping,
    ADProvisioningRule,
    ADSyncConfig,
    ADSyncLog,
    ADUserMapping,
)


@admin.register(ADSyncConfig)
class ADSyncConfigAdmin(admin.ModelAdmin):
    """Admin interface for AD synchronization configuration."""
    
    list_display = [
        'firm',
        'is_enabled',
        'sync_type',
        'sync_schedule',
        'last_sync_status_badge',
        'last_sync_at'
    ]
    list_filter = ['is_enabled', 'sync_type', 'sync_schedule', 'last_sync_status']
    search_fields = ['firm__name', 'server_url', 'base_dn']
    readonly_fields = [
        'last_sync_at',
        'last_sync_status',
        'last_sync_error',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = [
        ('Firm', {
            'fields': ['firm', 'is_enabled']
        }),
        ('Connection Settings', {
            'fields': [
                'server_url',
                'service_account_dn',
                'encrypted_password',
                'base_dn',
                'ou_filter'
            ]
        }),
        ('Sync Settings', {
            'fields': [
                'sync_type',
                'sync_schedule',
                'auto_disable_users',
                'attribute_mapping'
            ]
        }),
        ('Sync Status', {
            'fields': [
                'last_sync_at',
                'last_sync_status',
                'last_sync_error'
            ]
        }),
        ('Metadata', {
            'fields': [
                'created_at',
                'updated_at',
                'created_by'
            ],
            'classes': ['collapse']
        })
    ]
    
    def last_sync_status_badge(self, obj):
        """Display sync status with colored badge."""
        if obj.last_sync_status == 'success':
            color = 'green'
            icon = '✓'
        elif obj.last_sync_status == 'error':
            color = 'red'
            icon = '✗'
        else:
            color = 'gray'
            icon = '?'
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.last_sync_status
        )
    last_sync_status_badge.short_description = 'Status'


@admin.register(ADSyncLog)
class ADSyncLogAdmin(admin.ModelAdmin):
    """Admin interface for AD sync logs."""
    
    list_display = [
        'id',
        'firm',
        'sync_type',
        'status_badge',
        'users_summary',
        'duration_seconds',
        'started_at'
    ]
    list_filter = ['status', 'sync_type', 'started_at']
    search_fields = ['firm__name', 'error_message']
    readonly_fields = [
        'firm',
        'sync_type',
        'users_found',
        'users_created',
        'users_updated',
        'users_disabled',
        'users_skipped',
        'groups_synced',
        'group_members_synced',
        'status',
        'error_message',
        'duration_seconds',
        'started_at',
        'completed_at',
        'triggered_by'
    ]
    
    fieldsets = [
        ('Sync Info', {
            'fields': [
                'firm',
                'sync_type',
                'status',
                'triggered_by'
            ]
        }),
        ('User Metrics', {
            'fields': [
                'users_found',
                'users_created',
                'users_updated',
                'users_disabled',
                'users_skipped'
            ]
        }),
        ('Group Metrics', {
            'fields': [
                'groups_synced',
                'group_members_synced'
            ]
        }),
        ('Performance', {
            'fields': [
                'started_at',
                'completed_at',
                'duration_seconds'
            ]
        }),
        ('Errors', {
            'fields': ['error_message'],
            'classes': ['collapse']
        })
    ]
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        if obj.status == 'success':
            color = 'green'
            icon = '✓'
        elif obj.status == 'error':
            color = 'red'
            icon = '✗'
        elif obj.status == 'partial':
            color = 'orange'
            icon = '⚠'
        else:
            color = 'gray'
            icon = '?'
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.status
        )
    status_badge.short_description = 'Status'
    
    def users_summary(self, obj):
        """Display user sync summary."""
        return format_html(
            '<span title="Created/Updated/Disabled/Skipped">+{} ~{} -{} ✗{}</span>',
            obj.users_created,
            obj.users_updated,
            obj.users_disabled,
            obj.users_skipped
        )
    users_summary.short_description = 'Users'
    
    def has_add_permission(self, request):
        """Sync logs are created automatically, not manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Sync logs are read-only."""
        return False


@admin.register(ADProvisioningRule)
class ADProvisioningRuleAdmin(admin.ModelAdmin):
    """Admin interface for AD provisioning rules."""
    
    list_display = [
        'name',
        'firm',
        'is_enabled',
        'priority',
        'condition_type',
        'action_type'
    ]
    list_filter = ['is_enabled', 'condition_type', 'action_type']
    search_fields = ['name', 'firm__name']
    ordering = ['firm', 'priority', 'name']
    
    fieldsets = [
        ('Rule Info', {
            'fields': [
                'firm',
                'name',
                'is_enabled',
                'priority'
            ]
        }),
        ('Condition', {
            'fields': [
                'condition_type',
                'condition_value'
            ],
            'description': 'Define when this rule should apply'
        }),
        ('Action', {
            'fields': [
                'action_type',
                'action_value'
            ],
            'description': 'Define what happens when condition matches'
        }),
        ('Metadata', {
            'fields': [
                'created_at',
                'updated_at',
                'created_by'
            ],
            'classes': ['collapse']
        })
    ]


@admin.register(ADGroupMapping)
class ADGroupMappingAdmin(admin.ModelAdmin):
    """Admin interface for AD group mappings."""
    
    list_display = [
        'ad_group_name',
        'firm',
        'is_enabled',
        'sync_members',
        'assign_role',
        'member_count',
        'last_synced_at'
    ]
    list_filter = ['is_enabled', 'sync_members']
    search_fields = ['ad_group_name', 'ad_group_dn', 'firm__name']
    
    fieldsets = [
        ('Firm', {
            'fields': ['firm']
        }),
        ('AD Group Info', {
            'fields': [
                'ad_group_name',
                'ad_group_dn',
                'ad_group_guid'
            ]
        }),
        ('Sync Settings', {
            'fields': [
                'is_enabled',
                'sync_members',
                'assign_role'
            ]
        }),
        ('Status', {
            'fields': [
                'last_synced_at',
                'member_count'
            ]
        }),
        ('Metadata', {
            'fields': [
                'created_at',
                'updated_at'
            ],
            'classes': ['collapse']
        })
    ]


@admin.register(ADUserMapping)
class ADUserMappingAdmin(admin.ModelAdmin):
    """Admin interface for AD user mappings."""
    
    list_display = [
        'user',
        'firm',
        'ad_sam_account',
        'is_ad_managed',
        'last_synced_at'
    ]
    list_filter = ['is_ad_managed', 'firm']
    search_fields = [
        'user__email',
        'user__username',
        'ad_sam_account',
        'ad_upn',
        'ad_guid'
    ]
    readonly_fields = [
        'user',
        'firm',
        'ad_guid',
        'ad_upn',
        'ad_sam_account',
        'ad_dn',
        'first_synced_at',
        'last_synced_at',
        'ad_last_modified'
    ]
    
    fieldsets = [
        ('User', {
            'fields': ['user', 'firm']
        }),
        ('AD Attributes', {
            'fields': [
                'ad_guid',
                'ad_upn',
                'ad_sam_account',
                'ad_dn'
            ]
        }),
        ('Sync Status', {
            'fields': [
                'is_ad_managed',
                'first_synced_at',
                'last_synced_at',
                'ad_last_modified'
            ]
        })
    ]
    
    def has_add_permission(self, request):
        """User mappings are created automatically during sync."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of AD-managed users."""
        if obj and obj.is_ad_managed:
            return False
        return super().has_delete_permission(request, obj)
