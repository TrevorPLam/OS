"""
Active Directory Synchronization Models

Models for AD integration, user/group sync, and configuration.
Part of AD-1 through AD-5 implementation.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ADSyncConfig(models.Model):
    """
    AD-1: Active Directory synchronization configuration per firm.
    
    Stores connection details, sync settings, and OU filters for AD integration.
    """
    SYNC_TYPE_CHOICES = [
        ('full', 'Full Sync'),
        ('delta', 'Delta/Incremental Sync'),
    ]
    
    SYNC_SCHEDULE_CHOICES = [
        ('manual', 'Manual Only'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    firm = models.OneToOneField(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ad_sync_config',
        help_text='Firm this AD configuration belongs to'
    )
    
    # Connection Settings
    server_url = models.CharField(
        max_length=255,
        help_text='LDAPS URL (e.g., ldaps://ad.company.com:636)'
    )
    service_account_dn = models.CharField(
        max_length=500,
        help_text='Service account Distinguished Name (e.g., CN=ServiceAccount,OU=Service Accounts,DC=company,DC=com)'
    )
    encrypted_password = models.TextField(
        help_text='Encrypted service account password (stored encrypted at rest)'
    )
    base_dn = models.CharField(
        max_length=500,
        help_text='Base Distinguished Name for searches (e.g., DC=company,DC=com)'
    )
    
    # Sync Settings
    is_enabled = models.BooleanField(
        default=False,
        help_text='Whether AD sync is currently enabled'
    )
    sync_type = models.CharField(
        max_length=20,
        choices=SYNC_TYPE_CHOICES,
        default='delta',
        help_text='Type of sync: full or delta/incremental'
    )
    sync_schedule = models.CharField(
        max_length=20,
        choices=SYNC_SCHEDULE_CHOICES,
        default='daily',
        help_text='How often to sync automatically'
    )
    
    # AD-1: OU Filtering
    ou_filter = models.CharField(
        max_length=500,
        blank=True,
        help_text='Optional: Specific OU to sync from (e.g., OU=Employees,DC=company,DC=com)'
    )
    
    # AD-2: Attribute Mapping
    attribute_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text='Map AD attributes to User model fields (e.g., {"email": "mail", "first_name": "givenName"})'
    )
    
    # AD-3: Auto-disable
    auto_disable_users = models.BooleanField(
        default=True,
        help_text='Automatically disable users when their AD account is disabled'
    )
    
    # Sync Status
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp of last successful sync'
    )
    last_sync_status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('error', 'Error'), ('pending', 'Pending')],
        default='pending',
        help_text='Status of last sync attempt'
    )
    last_sync_error = models.TextField(
        blank=True,
        help_text='Error message from last failed sync'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ad_configs',
        help_text='User who created this configuration'
    )
    
    class Meta:
        db_table = 'ad_sync_config'
        verbose_name = 'AD Sync Configuration'
        verbose_name_plural = 'AD Sync Configurations'
    
    def __str__(self):
        return f"AD Config for {self.firm.name}"
    
    def clean(self):
        """Validate AD configuration"""
        errors = {}
        
        if not self.server_url.startswith('ldaps://'):
            errors['server_url'] = 'Server URL must use LDAPS (secure LDAP) protocol'
        
        if not self.base_dn:
            errors['base_dn'] = 'Base DN is required'
        
        if errors:
            raise ValidationError(errors)


class ADSyncLog(models.Model):
    """
    AD-1: Log entry for each AD synchronization run.
    
    Tracks sync metrics, errors, and performance for auditing and troubleshooting.
    """
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ad_sync_logs',
        help_text='Firm this sync log belongs to'
    )
    
    sync_type = models.CharField(
        max_length=20,
        choices=[('full', 'Full Sync'), ('delta', 'Delta Sync'), ('manual', 'Manual Sync')],
        help_text='Type of sync that was performed'
    )
    
    # Sync Metrics
    users_found = models.IntegerField(
        default=0,
        help_text='Number of users found in AD'
    )
    users_created = models.IntegerField(
        default=0,
        help_text='Number of new users created'
    )
    users_updated = models.IntegerField(
        default=0,
        help_text='Number of existing users updated'
    )
    users_disabled = models.IntegerField(
        default=0,
        help_text='Number of users disabled'
    )
    users_skipped = models.IntegerField(
        default=0,
        help_text='Number of users skipped (e.g., missing email)'
    )
    
    # Group Sync Metrics (AD-5)
    groups_synced = models.IntegerField(
        default=0,
        help_text='Number of AD groups synchronized'
    )
    group_members_synced = models.IntegerField(
        default=0,
        help_text='Number of group memberships synchronized'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Success'), ('error', 'Error'), ('partial', 'Partial Success')],
        help_text='Overall sync status'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error details if sync failed'
    )
    
    # Performance
    duration_seconds = models.IntegerField(
        help_text='How long the sync took in seconds'
    )
    
    # Metadata
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When sync completed (null if still running)'
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_ad_syncs',
        help_text='User who manually triggered this sync (null for scheduled syncs)'
    )
    
    class Meta:
        db_table = 'ad_sync_log'
        ordering = ['-started_at']
        verbose_name = 'AD Sync Log'
        verbose_name_plural = 'AD Sync Logs'
        indexes = [
            models.Index(fields=['firm', '-started_at'], name='ad_firm_start_idx'),
            models.Index(fields=['status'], name='ad_status_idx'),
        ]
    
    def __str__(self):
        return f"AD Sync {self.id} for {self.firm.name} - {self.status}"


class ADProvisioningRule(models.Model):
    """
    AD-3: Provisioning rules for automatic user creation and role assignment.
    
    Define conditions and actions for automatically provisioning users from AD.
    """
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ad_provisioning_rules',
        help_text='Firm this rule belongs to'
    )
    
    name = models.CharField(
        max_length=255,
        help_text='Descriptive name for this rule'
    )
    
    is_enabled = models.BooleanField(
        default=True,
        help_text='Whether this rule is currently active'
    )
    
    priority = models.IntegerField(
        default=100,
        help_text='Rule priority (lower number = higher priority). Rules are evaluated in order.'
    )
    
    # AD-3: Condition Configuration
    condition_type = models.CharField(
        max_length=50,
        choices=[
            ('ad_group', 'AD Group Membership'),
            ('ou_path', 'OU Path Match'),
            ('attribute_value', 'Attribute Value Match'),
            ('always', 'Always Apply'),
        ],
        help_text='Type of condition to evaluate'
    )
    condition_value = models.JSONField(
        default=dict,
        help_text='Condition parameters (e.g., {"group_dn": "CN=Developers,OU=Groups,DC=company,DC=com"})'
    )
    
    # AD-3: Action Configuration
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('assign_role', 'Assign Firm Role'),
            ('skip_user', 'Skip User Creation'),
            ('set_active', 'Set User Active/Inactive'),
        ],
        help_text='Action to perform when condition matches'
    )
    action_value = models.JSONField(
        default=dict,
        help_text='Action parameters (e.g., {"role": "staff", "is_active": true})'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ad_rules',
        help_text='User who created this rule'
    )
    
    class Meta:
        db_table = 'ad_provisioning_rule'
        ordering = ['priority', 'name']
        verbose_name = 'AD Provisioning Rule'
        verbose_name_plural = 'AD Provisioning Rules'
        indexes = [
            models.Index(fields=['firm', 'is_enabled', 'priority'], name='ad_rule_prio_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.firm.name})"


class ADGroupMapping(models.Model):
    """
    AD-5: Mapping between AD security groups and platform groups/roles.
    
    Links AD groups to platform distribution groups or role assignments.
    """
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ad_group_mappings',
        help_text='Firm this mapping belongs to'
    )
    
    # AD Group Info
    ad_group_dn = models.CharField(
        max_length=500,
        help_text='AD group Distinguished Name (e.g., CN=Developers,OU=Groups,DC=company,DC=com)'
    )
    ad_group_name = models.CharField(
        max_length=255,
        help_text='AD group common name for display'
    )
    ad_group_guid = models.CharField(
        max_length=36,
        blank=True,
        help_text='AD group GUID for tracking'
    )
    
    # Sync Settings
    is_enabled = models.BooleanField(
        default=True,
        help_text='Whether to sync this group'
    )
    sync_members = models.BooleanField(
        default=True,
        help_text='Whether to sync group member list'
    )
    
    # Platform Mapping
    assign_role = models.CharField(
        max_length=20,
        blank=True,
        help_text='Optional: Automatically assign this firm role to group members'
    )
    
    # Sync Status
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this group was last synced'
    )
    member_count = models.IntegerField(
        default=0,
        help_text='Number of members in this group (from last sync)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ad_group_mapping'
        unique_together = [['firm', 'ad_group_dn']]
        verbose_name = 'AD Group Mapping'
        verbose_name_plural = 'AD Group Mappings'
        indexes = [
            models.Index(fields=['firm', 'is_enabled'], name='ad_grp_firm_idx'),
        ]
    
    def __str__(self):
        return f"{self.ad_group_name} → {self.firm.name}"


class ADUserMapping(models.Model):
    """
    AD-1, AD-2: Mapping between platform users and AD accounts.
    
    Tracks AD-specific user attributes for sync and reconciliation.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ad_mapping',
        help_text='Platform user this mapping belongs to'
    )
    
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='ad_user_mappings',
        help_text='Firm this user belongs to'
    )
    
    # AD Attributes
    ad_guid = models.CharField(
        max_length=36,
        unique=True,
        help_text='AD objectGUID (used for tracking across renames)'
    )
    ad_upn = models.CharField(
        max_length=255,
        blank=True,
        help_text='AD userPrincipalName'
    )
    ad_sam_account = models.CharField(
        max_length=255,
        blank=True,
        help_text='AD sAMAccountName (username)'
    )
    ad_dn = models.CharField(
        max_length=500,
        help_text='AD Distinguished Name'
    )
    
    # Sync Status
    first_synced_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When user was first synced from AD'
    )
    last_synced_at = models.DateTimeField(
        auto_now=True,
        help_text='When user was last synced from AD'
    )
    ad_last_modified = models.DateTimeField(
        null=True,
        blank=True,
        help_text='AD whenChanged timestamp'
    )
    
    # Status
    is_ad_managed = models.BooleanField(
        default=True,
        help_text='Whether this user is managed by AD sync (cannot be edited manually if True)'
    )
    
    class Meta:
        db_table = 'ad_user_mapping'
        unique_together = [['firm', 'ad_guid']]
        verbose_name = 'AD User Mapping'
        verbose_name_plural = 'AD User Mappings'
        indexes = [
            models.Index(fields=['firm', 'is_ad_managed'], name='ad_usr_firm_idx'),
            models.Index(fields=['ad_guid'], name='ad_usr_guid_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (AD: {self.ad_sam_account})"
