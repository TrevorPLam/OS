"""
Active Directory Synchronization Serializers

REST API serializers for AD sync configuration and status.
"""

from rest_framework import serializers

from modules.ad_sync.models import (
    ADGroupMapping,
    ADProvisioningRule,
    ADSyncConfig,
    ADSyncLog,
    ADUserMapping,
)


class ADSyncConfigSerializer(serializers.ModelSerializer):
    """Serializer for AD sync configuration."""
    
    last_sync_at_display = serializers.DateTimeField(source='last_sync_at', read_only=True)
    
    class Meta:
        model = ADSyncConfig
        fields = [
            'id',
            'firm',
            'server_url',
            'service_account_dn',
            'encrypted_password',  # Write-only in practice
            'base_dn',
            'ou_filter',
            'is_enabled',
            'sync_type',
            'sync_schedule',
            'auto_disable_users',
            'attribute_mapping',
            'last_sync_at',
            'last_sync_at_display',
            'last_sync_status',
            'last_sync_error',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'last_sync_at',
            'last_sync_status',
            'last_sync_error',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'encrypted_password': {'write_only': True},
        }
    
    def validate_server_url(self, value):
        """Ensure server URL uses LDAPS protocol."""
        if not value.startswith('ldaps://'):
            raise serializers.ValidationError(
                'Server URL must use LDAPS (secure LDAP) protocol for security'
            )
        return value


class ADSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for AD sync log entries."""
    
    triggered_by_name = serializers.CharField(source='triggered_by.get_full_name', read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ADSyncLog
        fields = [
            'id',
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
            'duration_display',
            'started_at',
            'completed_at',
            'triggered_by',
            'triggered_by_name',
        ]
        read_only_fields = '__all__'
    
    def get_duration_display(self, obj):
        """Format duration in human-readable format."""
        seconds = obj.duration_seconds
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"


class ADProvisioningRuleSerializer(serializers.ModelSerializer):
    """Serializer for AD provisioning rules."""
    
    class Meta:
        model = ADProvisioningRule
        fields = [
            'id',
            'firm',
            'name',
            'is_enabled',
            'priority',
            'condition_type',
            'condition_value',
            'action_type',
            'action_value',
            'created_at',
            'updated_at',
            'created_by',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ADGroupMappingSerializer(serializers.ModelSerializer):
    """Serializer for AD group mappings."""
    
    class Meta:
        model = ADGroupMapping
        fields = [
            'id',
            'firm',
            'ad_group_dn',
            'ad_group_name',
            'ad_group_guid',
            'is_enabled',
            'sync_members',
            'assign_role',
            'last_synced_at',
            'member_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'last_synced_at',
            'member_count',
            'created_at',
            'updated_at',
        ]


class ADUserMappingSerializer(serializers.ModelSerializer):
    """Serializer for AD user mappings."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ADUserMapping
        fields = [
            'id',
            'user',
            'user_email',
            'user_name',
            'firm',
            'ad_guid',
            'ad_upn',
            'ad_sam_account',
            'ad_dn',
            'first_synced_at',
            'last_synced_at',
            'ad_last_modified',
            'is_ad_managed',
        ]
        read_only_fields = '__all__'


class ADSyncTriggerSerializer(serializers.Serializer):
    """Serializer for manually triggering AD sync."""
    
    sync_type = serializers.ChoiceField(
        choices=['full', 'delta', 'manual'],
        default='manual',
        help_text='Type of sync to perform'
    )


class ADConnectionTestSerializer(serializers.Serializer):
    """Serializer for testing AD connection."""
    
    server_url = serializers.CharField(required=True)
    service_account_dn = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    base_dn = serializers.CharField(required=True)
    
    def validate_server_url(self, value):
        """Ensure server URL uses LDAPS protocol."""
        if not value.startswith('ldaps://'):
            raise serializers.ValidationError(
                'Server URL must use LDAPS (secure LDAP) protocol for security'
            )
        return value
