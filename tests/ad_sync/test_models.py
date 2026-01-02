"""
Tests for Active Directory Synchronization Models

Tests AD sync configuration, logging, and mapping models.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.ad_sync.models import (
    ADGroupMapping,
    ADProvisioningRule,
    ADSyncConfig,
    ADSyncLog,
    ADUserMapping,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm():
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Firm",
        slug="test-firm",
        status="active"
    )


@pytest.fixture
def user(firm):
    """Create a test user."""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    return user


@pytest.fixture
def ad_config(firm, user):
    """Create a test AD sync configuration."""
    return ADSyncConfig.objects.create(
        firm=firm,
        server_url="ldaps://ad.example.com:636",
        service_account_dn="CN=Service,DC=example,DC=com",
        encrypted_password="encrypted_password_here",
        base_dn="DC=example,DC=com",
        is_enabled=True,
        created_by=user
    )


@pytest.mark.django_db
class TestADSyncConfig:
    """Tests for ADSyncConfig model."""
    
    def test_create_ad_config(self, firm, user):
        """Test creating an AD sync configuration."""
        config = ADSyncConfig.objects.create(
            firm=firm,
            server_url="ldaps://ad.example.com:636",
            service_account_dn="CN=Service,DC=example,DC=com",
            encrypted_password="encrypted_password",
            base_dn="DC=example,DC=com",
            is_enabled=True,
            created_by=user
        )
        
        assert config.firm == firm
        assert config.server_url == "ldaps://ad.example.com:636"
        assert config.is_enabled is True
        assert config.sync_type == "delta"  # Default
        assert config.sync_schedule == "daily"  # Default
    
    def test_server_url_validation(self, firm, user):
        """Test that server URL must use LDAPS protocol."""
        config = ADSyncConfig(
            firm=firm,
            server_url="ldap://ad.example.com:389",  # Non-secure LDAP
            service_account_dn="CN=Service,DC=example,DC=com",
            encrypted_password="encrypted_password",
            base_dn="DC=example,DC=com",
            created_by=user
        )
        
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        
        assert 'server_url' in exc_info.value.error_dict
        assert 'LDAPS' in str(exc_info.value)
    
    def test_base_dn_required(self, firm, user):
        """Test that base DN is required."""
        config = ADSyncConfig(
            firm=firm,
            server_url="ldaps://ad.example.com:636",
            service_account_dn="CN=Service,DC=example,DC=com",
            encrypted_password="encrypted_password",
            base_dn="",  # Empty base DN
            created_by=user
        )
        
        with pytest.raises(ValidationError) as exc_info:
            config.full_clean()
        
        assert 'base_dn' in exc_info.value.error_dict
    
    def test_one_config_per_firm(self, firm, user):
        """Test that a firm can have only one AD sync config."""
        # Create first config
        ADSyncConfig.objects.create(
            firm=firm,
            server_url="ldaps://ad.example.com:636",
            service_account_dn="CN=Service,DC=example,DC=com",
            encrypted_password="encrypted_password",
            base_dn="DC=example,DC=com",
            created_by=user
        )
        
        # Trying to create second config for same firm should use OneToOne
        # This will raise IntegrityError due to unique constraint
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ADSyncConfig.objects.create(
                firm=firm,
                server_url="ldaps://ad2.example.com:636",
                service_account_dn="CN=Service2,DC=example,DC=com",
                encrypted_password="encrypted_password2",
                base_dn="DC=example,DC=com",
                created_by=user
            )


@pytest.mark.django_db
class TestADSyncLog:
    """Tests for ADSyncLog model."""
    
    def test_create_sync_log(self, firm, user):
        """Test creating a sync log entry."""
        log = ADSyncLog.objects.create(
            firm=firm,
            sync_type="full",
            users_found=100,
            users_created=10,
            users_updated=80,
            users_disabled=5,
            users_skipped=5,
            groups_synced=5,
            group_members_synced=50,
            status="success",
            duration_seconds=120,
            triggered_by=user
        )
        
        assert log.firm == firm
        assert log.sync_type == "full"
        assert log.users_created == 10
        assert log.status == "success"
        assert log.triggered_by == user
    
    def test_sync_log_ordering(self, firm, user):
        """Test that sync logs are ordered by started_at descending."""
        # Create multiple logs
        log1 = ADSyncLog.objects.create(
            firm=firm,
            sync_type="full",
            status="success",
            duration_seconds=60,
        )
        
        log2 = ADSyncLog.objects.create(
            firm=firm,
            sync_type="delta",
            status="success",
            duration_seconds=30,
        )
        
        # Query logs - should be ordered by started_at descending
        logs = list(ADSyncLog.objects.all())
        assert logs[0] == log2  # Most recent
        assert logs[1] == log1


@pytest.mark.django_db
class TestADProvisioningRule:
    """Tests for ADProvisioningRule model."""
    
    def test_create_provisioning_rule(self, firm, user):
        """Test creating a provisioning rule."""
        rule = ADProvisioningRule.objects.create(
            firm=firm,
            name="Assign Staff Role",
            is_enabled=True,
            priority=100,
            condition_type="ad_group",
            condition_value={"group_dn": "CN=Staff,DC=example,DC=com"},
            action_type="assign_role",
            action_value={"role": "staff"},
            created_by=user
        )
        
        assert rule.firm == firm
        assert rule.name == "Assign Staff Role"
        assert rule.condition_type == "ad_group"
        assert rule.action_type == "assign_role"
        assert rule.priority == 100
    
    def test_rule_ordering_by_priority(self, firm, user):
        """Test that rules are ordered by priority."""
        rule1 = ADProvisioningRule.objects.create(
            firm=firm,
            name="Rule 1",
            priority=200,
            condition_type="always",
            action_type="assign_role",
            created_by=user
        )
        
        rule2 = ADProvisioningRule.objects.create(
            firm=firm,
            name="Rule 2",
            priority=50,  # Lower = higher priority
            condition_type="always",
            action_type="assign_role",
            created_by=user
        )
        
        rules = list(ADProvisioningRule.objects.all())
        assert rules[0] == rule2  # Higher priority (lower number)
        assert rules[1] == rule1


@pytest.mark.django_db
class TestADGroupMapping:
    """Tests for ADGroupMapping model."""
    
    def test_create_group_mapping(self, firm):
        """Test creating an AD group mapping."""
        mapping = ADGroupMapping.objects.create(
            firm=firm,
            ad_group_dn="CN=Developers,OU=Groups,DC=example,DC=com",
            ad_group_name="Developers",
            ad_group_guid="12345678-1234-1234-1234-123456789abc",
            is_enabled=True,
            sync_members=True,
            assign_role="staff"
        )
        
        assert mapping.firm == firm
        assert mapping.ad_group_name == "Developers"
        assert mapping.is_enabled is True
        assert mapping.sync_members is True
    
    def test_group_mapping_uniqueness(self, firm):
        """Test that group DN must be unique per firm."""
        group_dn = "CN=Developers,OU=Groups,DC=example,DC=com"
        
        # Create first mapping
        ADGroupMapping.objects.create(
            firm=firm,
            ad_group_dn=group_dn,
            ad_group_name="Developers",
            is_enabled=True
        )
        
        # Trying to create duplicate should raise error
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ADGroupMapping.objects.create(
                firm=firm,
                ad_group_dn=group_dn,  # Same DN
                ad_group_name="Developers",
                is_enabled=True
            )


@pytest.mark.django_db
class TestADUserMapping:
    """Tests for ADUserMapping model."""
    
    def test_create_user_mapping(self, firm, user):
        """Test creating an AD user mapping."""
        mapping = ADUserMapping.objects.create(
            user=user,
            firm=firm,
            ad_guid="12345678-1234-1234-1234-123456789abc",
            ad_upn="testuser@example.com",
            ad_sam_account="testuser",
            ad_dn="CN=Test User,OU=Users,DC=example,DC=com",
            is_ad_managed=True
        )
        
        assert mapping.user == user
        assert mapping.firm == firm
        assert mapping.ad_guid == "12345678-1234-1234-1234-123456789abc"
        assert mapping.is_ad_managed is True
    
    def test_ad_guid_uniqueness(self, firm, user):
        """Test that AD GUID must be unique across all firms."""
        ad_guid = "12345678-1234-1234-1234-123456789abc"
        
        # Create first mapping
        ADUserMapping.objects.create(
            user=user,
            firm=firm,
            ad_guid=ad_guid,
            ad_dn="CN=Test,DC=example,DC=com",
            is_ad_managed=True
        )
        
        # Create another user
        user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpass123"
        )
        
        # Trying to create mapping with same AD GUID should fail
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ADUserMapping.objects.create(
                user=user2,
                firm=firm,
                ad_guid=ad_guid,  # Same GUID
                ad_dn="CN=Test2,DC=example,DC=com",
                is_ad_managed=True
            )
    
    def test_one_mapping_per_user(self, firm, user):
        """Test that a user can have only one AD mapping."""
        # Create first mapping
        ADUserMapping.objects.create(
            user=user,
            firm=firm,
            ad_guid="12345678-1234-1234-1234-123456789abc",
            ad_dn="CN=Test,DC=example,DC=com",
            is_ad_managed=True
        )
        
        # Trying to create second mapping for same user should fail
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ADUserMapping.objects.create(
                user=user,
                firm=firm,
                ad_guid="87654321-4321-4321-4321-cba987654321",
                ad_dn="CN=Test2,DC=example,DC=com",
                is_ad_managed=True
            )
