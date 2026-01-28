"""
Active Directory Synchronization Service

Orchestrates user and group synchronization from Active Directory.
Part of AD-1 through AD-5 implementation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone as django_timezone
from cryptography.fernet import Fernet

from modules.ad_sync.connector import ActiveDirectoryConnector
from modules.ad_sync.models import (
    ADGroupMapping,
    ADProvisioningRule,
    ADSyncConfig,
    ADSyncLog,
    ADUserMapping,
)
from modules.firm.models import Firm, FirmMembership

User = get_user_model()
logger = logging.getLogger(__name__)


class ADSyncService:
    """
    Service class for Active Directory synchronization.
    
    Handles the complete sync workflow:
    - Connect to AD
    - Query users/groups
    - Apply attribute mapping
    - Apply provisioning rules
    - Create/update users
    - Sync group memberships
    - Log results
    """
    
    def __init__(self, firm: Firm):
        """
        Initialize sync service for a firm.
        
        Args:
            firm: Firm to sync
        """
        self.firm = firm
        self.config: Optional[ADSyncConfig] = None
        self.connector: Optional[ActiveDirectoryConnector] = None
        self.sync_log: Optional[ADSyncLog] = None
        
    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt AD service account password.
        
        Uses Fernet symmetric encryption with Django SECRET_KEY.
        
        Args:
            encrypted_password: Encrypted password string
        
        Returns:
            Decrypted password
        """
        # Use Django SECRET_KEY as encryption key (ensure it's 32 url-safe base64-encoded bytes)
        key = settings.SECRET_KEY[:32].encode('utf-8').ljust(32, b'=')
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_password.encode('utf-8'))
        return decrypted.decode('utf-8')
    
    def sync(self, sync_type: str = 'delta', triggered_by: Optional[Any] = None) -> ADSyncLog:
        """
        Perform AD synchronization.
        
        AD-1, AD-4: Main sync entry point.
        
        Args:
            sync_type: 'full', 'delta', or 'manual'
            triggered_by: User who triggered sync (for manual syncs)
        
        Returns:
            ADSyncLog with sync results
        """
        start_time = django_timezone.now()
        
        try:
            # Load configuration
            self.config = self.firm.ad_sync_config
            if not self.config.is_enabled:
                raise ValueError(f"AD sync is not enabled for firm {self.firm.name}")
            
            # Create sync log
            self.sync_log = ADSyncLog.objects.create(
                firm=self.firm,
                sync_type=sync_type,
                triggered_by=triggered_by,
                duration_seconds=0,  # Will update at end
                status='pending'
            )
            
            # Connect to AD
            password = self._decrypt_password(self.config.encrypted_password)
            self.connector = ActiveDirectoryConnector(
                server_url=self.config.server_url,
                service_account_dn=self.config.service_account_dn,
                password=password,
                base_dn=self.config.base_dn
            )
            self.connector.connect()
            
            # Determine which users to sync
            if sync_type == 'delta' and self.config.last_sync_at:
                logger.info(f"Performing delta sync since {self.config.last_sync_at}")
                ad_users = self.connector.get_delta_users(
                    since_timestamp=self.config.last_sync_at,
                    ou_filter=self.config.ou_filter
                )
            else:
                logger.info("Performing full sync")
                ad_users = self.connector.search_users(
                    ou_filter=self.config.ou_filter
                )
            
            self.sync_log.users_found = len(ad_users)
            self.sync_log.save()
            
            # Sync users
            sync_results = self._sync_users(ad_users)
            
            # Sync groups (AD-5)
            if self.config.is_enabled:
                group_results = self._sync_groups()
                sync_results['groups_synced'] = group_results['groups_synced']
                sync_results['group_members_synced'] = group_results['group_members_synced']
            
            # Update sync log with results
            self.sync_log.users_created = sync_results['created']
            self.sync_log.users_updated = sync_results['updated']
            self.sync_log.users_disabled = sync_results['disabled']
            self.sync_log.users_skipped = sync_results['skipped']
            self.sync_log.groups_synced = sync_results.get('groups_synced', 0)
            self.sync_log.group_members_synced = sync_results.get('group_members_synced', 0)
            self.sync_log.status = 'success'
            self.sync_log.completed_at = django_timezone.now()
            self.sync_log.duration_seconds = int((self.sync_log.completed_at - start_time).total_seconds())
            self.sync_log.save()
            
            # Update config last sync timestamp
            self.config.last_sync_at = django_timezone.now()
            self.config.last_sync_status = 'success'
            self.config.last_sync_error = ''
            self.config.save()
            
            logger.info(f"AD sync completed successfully: {sync_results}")
            return self.sync_log
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AD sync failed: {error_msg}", exc_info=True)
            
            # Update sync log with error
            if self.sync_log:
                self.sync_log.status = 'error'
                self.sync_log.error_message = error_msg
                self.sync_log.completed_at = django_timezone.now()
                self.sync_log.duration_seconds = int((self.sync_log.completed_at - start_time).total_seconds())
                self.sync_log.save()
            
            # Update config with error
            if self.config:
                self.config.last_sync_status = 'error'
                self.config.last_sync_error = error_msg
                self.config.save()
            
            raise
            
        finally:
            # Always close connection
            if self.connector:
                self.connector.close()
    
    def _sync_users(self, ad_users: list[Any]) -> dict[str, int]:
        """
        Sync users from AD to platform.
        
        AD-1, AD-2: User synchronization with attribute mapping.
        
        Args:
            ad_users: List of LDAP user entries
        
        Returns:
            Dict with counts: created, updated, disabled, skipped
        """
        results = {
            'created': 0,
            'updated': 0,
            'disabled': 0,
            'skipped': 0
        }
        
        # Get attribute mapping (AD-2)
        attr_map = self.config.attribute_mapping or {
            'email': 'mail',
            'first_name': 'givenName',
            'last_name': 'sn',
            'username': 'sAMAccountName'
        }
        
        for ad_user in ad_users:
            try:
                # Extract email (required)
                email_attr = attr_map.get('email', 'mail')
                email = getattr(ad_user, email_attr, None)
                if email:
                    email = str(email.value) if hasattr(email, 'value') else str(email)
                
                if not email:
                    logger.warning(f"Skipping AD user without email: {ad_user.distinguishedName}")
                    results['skipped'] += 1
                    continue
                
                # Extract AD identifiers
                ad_guid = str(ad_user.objectGUID.value) if hasattr(ad_user, 'objectGUID') else None
                if not ad_guid:
                    logger.warning(f"Skipping AD user without GUID: {email}")
                    results['skipped'] += 1
                    continue
                
                # Extract other attributes using mapping
                username = self._get_ad_attribute(ad_user, attr_map.get('username', 'sAMAccountName'))
                first_name = self._get_ad_attribute(ad_user, attr_map.get('first_name', 'givenName'))
                last_name = self._get_ad_attribute(ad_user, attr_map.get('last_name', 'sn'))
                
                # Check if user is enabled in AD
                is_enabled = self.connector.is_user_enabled(ad_user)
                
                # Get AD timestamps
                ad_last_modified = self._parse_ad_timestamp(
                    self._get_ad_attribute(ad_user, 'whenChanged')
                )
                
                # Check if user already exists (by AD GUID)
                with transaction.atomic():
                    try:
                        ad_mapping = ADUserMapping.objects.select_related('user').get(
                            firm=self.firm,
                            ad_guid=ad_guid
                        )
                        user = ad_mapping.user
                        user_existed = True
                    except ADUserMapping.DoesNotExist:
                        # Create new user
                        user = User.objects.create(
                            email=email,
                            username=username or email,
                            first_name=first_name or '',
                            last_name=last_name or '',
                            is_active=is_enabled
                        )
                        
                        # Create AD mapping
                        ad_mapping = ADUserMapping.objects.create(
                            user=user,
                            firm=self.firm,
                            ad_guid=ad_guid,
                            ad_upn=self._get_ad_attribute(ad_user, 'userPrincipalName'),
                            ad_sam_account=username,
                            ad_dn=str(ad_user.distinguishedName),
                            ad_last_modified=ad_last_modified,
                            is_ad_managed=True
                        )
                        
                        # Create firm membership (AD-3: apply provisioning rules)
                        role = self._apply_provisioning_rules(ad_user)
                        FirmMembership.objects.create(
                            firm=self.firm,
                            user=user,
                            role=role
                        )
                        
                        user_existed = False
                        results['created'] += 1
                        logger.info(f"Created new user from AD: {email} ({ad_guid})")
                    
                    if user_existed:
                        # Update existing user
                        updated = False
                        
                        # Update basic attributes if they changed
                        if user.first_name != first_name and first_name:
                            user.first_name = first_name
                            updated = True
                        if user.last_name != last_name and last_name:
                            user.last_name = last_name
                            updated = True
                        
                        # AD-3: Auto-disable users if configured
                        if self.config.auto_disable_users:
                            if user.is_active and not is_enabled:
                                user.is_active = False
                                updated = True
                                results['disabled'] += 1
                                logger.info(f"Disabled user {email} (AD account disabled)")
                            elif not user.is_active and is_enabled:
                                user.is_active = True
                                updated = True
                                logger.info(f"Re-enabled user {email} (AD account enabled)")
                        
                        if updated:
                            user.save()
                        
                        # Update AD mapping timestamps
                        ad_mapping.ad_last_modified = ad_last_modified
                        ad_mapping.ad_dn = str(ad_user.distinguishedName)
                        ad_mapping.save()
                        
                        results['updated'] += 1
                        
            except Exception as e:
                logger.error(f"Failed to sync user: {e}", exc_info=True)
                results['skipped'] += 1
                continue
        
        return results
    
    def _sync_groups(self) -> dict[str, int]:
        """
        Sync AD groups and memberships.
        
        AD-5: Group synchronization.
        
        Returns:
            Dict with counts: groups_synced, group_members_synced
        """
        results = {
            'groups_synced': 0,
            'group_members_synced': 0
        }
        
        # Get groups to sync
        group_mappings = ADGroupMapping.objects.filter(
            firm=self.firm,
            is_enabled=True,
            sync_members=True
        )
        
        for mapping in group_mappings:
            try:
                # Get group members from AD
                members = self.connector.get_group_members(mapping.ad_group_dn)
                
                # Update mapping
                mapping.member_count = len(members)
                mapping.last_synced_at = django_timezone.now()
                mapping.save()
                
                results['groups_synced'] += 1
                results['group_members_synced'] += len(members)
                
                logger.info(f"Synced group {mapping.ad_group_name}: {len(members)} members")
                
            except Exception as e:
                logger.error(f"Failed to sync group {mapping.ad_group_name}: {e}")
                continue
        
        return results
    
    def _apply_provisioning_rules(self, ad_user: Any) -> str:
        """
        Apply provisioning rules to determine user role.
        
        AD-3: Provisioning rules engine.
        
        Args:
            ad_user: LDAP user entry
        
        Returns:
            Role to assign to user
        """
        # Get provisioning rules for firm
        rules = ADProvisioningRule.objects.filter(
            firm=self.firm,
            is_enabled=True
        ).order_by('priority')
        
        for rule in rules:
            if self._evaluate_rule_condition(rule, ad_user):
                logger.info(f"Provisioning rule matched: {rule.name}")
                
                # Apply action
                if rule.action_type == 'assign_role':
                    role = rule.action_value.get('role', 'staff')
                    return role
                elif rule.action_type == 'skip_user':
                    raise ValueError(f"User skipped by provisioning rule: {rule.name}")
        
        # Default role if no rules matched
        return 'staff'
    
    def _evaluate_rule_condition(self, rule: ADProvisioningRule, ad_user: Any) -> bool:
        """
        Evaluate if a provisioning rule condition matches.
        
        AD-3: Rule condition evaluation.
        
        Args:
            rule: Provisioning rule to evaluate
            ad_user: LDAP user entry
        
        Returns:
            True if condition matches
        """
        if rule.condition_type == 'always':
            return True
        
        elif rule.condition_type == 'ad_group':
            # Check if user is member of specific AD group
            required_group_dn = rule.condition_value.get('group_dn')
            if not required_group_dn:
                return False
            
            user_groups = self.connector.get_user_groups(ad_user)
            return required_group_dn in user_groups
        
        elif rule.condition_type == 'ou_path':
            # Check if user's DN contains specific OU path
            required_ou = rule.condition_value.get('ou_path')
            if not required_ou:
                return False
            
            user_dn = str(ad_user.distinguishedName)
            return required_ou in user_dn
        
        elif rule.condition_type == 'attribute_value':
            # Check if user's AD attribute matches value
            attr_name = rule.condition_value.get('attribute')
            expected_value = rule.condition_value.get('value')
            if not attr_name or expected_value is None:
                return False
            
            actual_value = self._get_ad_attribute(ad_user, attr_name)
            return str(actual_value).lower() == str(expected_value).lower()
        
        return False
    
    def _get_ad_attribute(self, ad_user: Any, attr_name: str) -> str:
        """
        Get AD attribute value safely.
        
        Args:
            ad_user: LDAP user entry
            attr_name: Attribute name
        
        Returns:
            Attribute value as string, or empty string if not found
        """
        try:
            attr = getattr(ad_user, attr_name, None)
            if attr is None:
                return ''
            if hasattr(attr, 'value'):
                return str(attr.value) if attr.value is not None else ''
            return str(attr)
        except (AttributeError, TypeError):
            return ''
    
    def _parse_ad_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse AD timestamp string to Python datetime.
        
        Args:
            timestamp_str: AD timestamp string (GeneralizedTime format)
        
        Returns:
            Python datetime object in UTC, or None if parse fails
        """
        if not timestamp_str:
            return None
        
        try:
            # AD timestamps are in format: YYYYMMDDHHMMSSmmZ
            dt = datetime.strptime(timestamp_str[:14], '%Y%m%d%H%M%S')
            return dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
