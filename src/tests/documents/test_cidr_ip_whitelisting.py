"""
Tests for CIDR range support in IP whitelisting (T-005).
"""

import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from modules.documents.models import ExternalShare, SharePermission
from modules.firm.models import Firm


@pytest.mark.django_db
class TestCIDRIPWhitelisting:
    """Test CIDR range support in IP whitelisting (T-005)."""

    @pytest.fixture
    def setup_data(self):
        """Create test data."""
        user = get_user_model().objects.create_user(
            username="testuser", password="testpass123"
        )
        firm = Firm.objects.create(
            name="Test Firm", slug="test-firm", created_by=user
        )
        external_share = ExternalShare.objects.create(
            firm=firm,
            share_token="test-token-123",
            shared_by=user,
        )
        share_permission = SharePermission.objects.create(
            firm=firm,
            external_share=external_share,
        )

        return {
            "user": user,
            "firm": firm,
            "external_share": external_share,
            "share_permission": share_permission,
        }

    def test_single_ip_exact_match(self, setup_data):
        """Test exact IP address match."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.100"]
        perm.save()

        assert perm.is_ip_allowed("192.168.1.100") is True
        assert perm.is_ip_allowed("192.168.1.101") is False
        assert perm.is_ip_allowed("10.0.0.1") is False

    def test_multiple_ips_exact_match(self, setup_data):
        """Test multiple exact IP addresses."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.100", "10.0.0.1", "172.16.0.50"]
        perm.save()

        assert perm.is_ip_allowed("192.168.1.100") is True
        assert perm.is_ip_allowed("10.0.0.1") is True
        assert perm.is_ip_allowed("172.16.0.50") is True
        assert perm.is_ip_allowed("192.168.1.101") is False
        assert perm.is_ip_allowed("8.8.8.8") is False

    def test_cidr_range_class_c(self, setup_data):
        """Test CIDR range matching for Class C network."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.0/24"]
        perm.save()

        # IPs in range
        assert perm.is_ip_allowed("192.168.1.1") is True
        assert perm.is_ip_allowed("192.168.1.100") is True
        assert perm.is_ip_allowed("192.168.1.254") is True
        
        # IPs out of range
        assert perm.is_ip_allowed("192.168.2.1") is False
        assert perm.is_ip_allowed("192.168.0.1") is False
        assert perm.is_ip_allowed("10.0.0.1") is False

    def test_cidr_range_class_b(self, setup_data):
        """Test CIDR range matching for Class B network."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["172.16.0.0/16"]
        perm.save()

        # IPs in range
        assert perm.is_ip_allowed("172.16.0.1") is True
        assert perm.is_ip_allowed("172.16.255.254") is True
        assert perm.is_ip_allowed("172.16.128.50") is True
        
        # IPs out of range
        assert perm.is_ip_allowed("172.17.0.1") is False
        assert perm.is_ip_allowed("172.15.255.254") is False
        assert perm.is_ip_allowed("192.168.1.1") is False

    def test_cidr_range_class_a(self, setup_data):
        """Test CIDR range matching for Class A network."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["10.0.0.0/8"]
        perm.save()

        # IPs in range
        assert perm.is_ip_allowed("10.0.0.1") is True
        assert perm.is_ip_allowed("10.255.255.254") is True
        assert perm.is_ip_allowed("10.100.50.25") is True
        
        # IPs out of range
        assert perm.is_ip_allowed("11.0.0.1") is False
        assert perm.is_ip_allowed("9.255.255.254") is False
        assert perm.is_ip_allowed("192.168.1.1") is False

    def test_mixed_ips_and_cidr(self, setup_data):
        """Test combination of individual IPs and CIDR ranges."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = [
            "8.8.8.8",  # Google DNS
            "192.168.1.0/24",  # Local network
            "10.0.0.0/8",  # Private network
            "1.2.3.4",  # Specific IP
        ]
        perm.save()

        # Exact matches
        assert perm.is_ip_allowed("8.8.8.8") is True
        assert perm.is_ip_allowed("1.2.3.4") is True
        
        # CIDR ranges
        assert perm.is_ip_allowed("192.168.1.50") is True
        assert perm.is_ip_allowed("10.100.200.150") is True
        
        # Not in any range
        assert perm.is_ip_allowed("172.16.0.1") is False
        assert perm.is_ip_allowed("8.8.4.4") is False

    def test_no_ip_restrictions(self, setup_data):
        """Test that empty allowed_ip_addresses allows all IPs."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = []
        perm.save()

        # All IPs should be allowed
        assert perm.is_ip_allowed("192.168.1.1") is True
        assert perm.is_ip_allowed("10.0.0.1") is True
        assert perm.is_ip_allowed("8.8.8.8") is True
        assert perm.is_ip_allowed("1.2.3.4") is True

    def test_invalid_ip_address_format(self, setup_data):
        """Test handling of invalid IP address format."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.0/24"]
        perm.save()

        # Invalid IP formats should return False
        assert perm.is_ip_allowed("not-an-ip") is False
        assert perm.is_ip_allowed("256.1.1.1") is False
        assert perm.is_ip_allowed("192.168") is False
        assert perm.is_ip_allowed("") is False

    def test_invalid_cidr_in_allowed_list(self, setup_data):
        """Test that invalid CIDR entries are skipped gracefully."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = [
            "192.168.1.0/24",  # Valid
            "invalid-cidr",  # Invalid
            "10.0.0.1",  # Valid
        ]
        perm.save()

        # Valid entries should still work
        assert perm.is_ip_allowed("192.168.1.50") is True
        assert perm.is_ip_allowed("10.0.0.1") is True
        
        # Invalid entry is skipped, so other IPs are denied
        assert perm.is_ip_allowed("172.16.0.1") is False

    def test_validation_valid_ip_addresses(self, setup_data):
        """Test validation accepts valid IP addresses."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.1", "10.0.0.1"]
        
        # Should not raise ValidationError
        perm.clean()

    def test_validation_valid_cidr_ranges(self, setup_data):
        """Test validation accepts valid CIDR ranges."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = [
            "192.168.1.0/24",
            "10.0.0.0/8",
            "172.16.0.0/16",
        ]
        
        # Should not raise ValidationError
        perm.clean()

    def test_validation_mixed_valid(self, setup_data):
        """Test validation accepts mixed valid entries."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = [
            "192.168.1.1",
            "10.0.0.0/8",
            "8.8.8.8",
            "172.16.0.0/16",
        ]
        
        # Should not raise ValidationError
        perm.clean()

    def test_validation_invalid_ip_address(self, setup_data):
        """Test validation rejects invalid IP addresses."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.1", "not-an-ip", "10.0.0.1"]
        
        with pytest.raises(ValidationError) as exc_info:
            perm.clean()
        
        assert "allowed_ip_addresses" in exc_info.value.error_dict
        assert "not-an-ip" in str(exc_info.value)

    def test_validation_invalid_cidr_range(self, setup_data):
        """Test validation rejects invalid CIDR ranges."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.0/24", "invalid/cidr", "10.0.0.0/8"]
        
        with pytest.raises(ValidationError) as exc_info:
            perm.clean()
        
        assert "allowed_ip_addresses" in exc_info.value.error_dict
        assert "invalid/cidr" in str(exc_info.value)

    def test_validation_multiple_invalid(self, setup_data):
        """Test validation reports all invalid entries."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = [
            "192.168.1.1",  # Valid
            "not-an-ip",  # Invalid
            "999.999.999.999",  # Invalid
            "10.0.0.0/8",  # Valid
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            perm.clean()
        
        error_message = str(exc_info.value)
        assert "not-an-ip" in error_message
        assert "999.999.999.999" in error_message

    def test_ipv6_address_support(self, setup_data):
        """Test support for IPv6 addresses."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = [
            "2001:db8::1",  # IPv6 address
            "2001:db8::/32",  # IPv6 CIDR
        ]
        perm.save()

        # IPv6 exact match
        assert perm.is_ip_allowed("2001:db8::1") is True
        
        # IPv6 in CIDR range
        assert perm.is_ip_allowed("2001:db8::100") is True
        assert perm.is_ip_allowed("2001:db8:1::1") is True
        
        # IPv6 out of range
        assert perm.is_ip_allowed("2001:db9::1") is False

    def test_small_cidr_ranges(self, setup_data):
        """Test small CIDR ranges."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["192.168.1.0/30"]  # Only 4 addresses
        perm.save()

        # In range (network, .1, .2, broadcast)
        assert perm.is_ip_allowed("192.168.1.0") is True
        assert perm.is_ip_allowed("192.168.1.1") is True
        assert perm.is_ip_allowed("192.168.1.2") is True
        assert perm.is_ip_allowed("192.168.1.3") is True
        
        # Out of range
        assert perm.is_ip_allowed("192.168.1.4") is False
        assert perm.is_ip_allowed("192.168.1.255") is False

    def test_large_cidr_range(self, setup_data):
        """Test large CIDR range (entire internet subset)."""
        perm = setup_data["share_permission"]
        perm.allowed_ip_addresses = ["0.0.0.0/1"]  # First half of IPv4 space
        perm.save()

        # In range (0.0.0.0 to 127.255.255.255)
        assert perm.is_ip_allowed("0.0.0.0") is True
        assert perm.is_ip_allowed("127.255.255.255") is True
        assert perm.is_ip_allowed("50.100.150.200") is True
        
        # Out of range (128.0.0.0+)
        assert perm.is_ip_allowed("128.0.0.0") is False
        assert perm.is_ip_allowed("192.168.1.1") is False
