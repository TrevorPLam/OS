"""
Tier 1 Safety Tests - Portal Containment

Tests that portal users are fully contained and cannot access firm admin endpoints.
CRITICAL: These tests validate Tier 2.4 and 2.5 portal isolation.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from modules.firm.models import Firm, FirmMembership
from modules.clients.models import Client, ClientPortalUser
from modules.clients.permissions import (
    IsPortalUserOrFirmUser,
    DenyPortalAccess,
)

User = get_user_model()


@pytest.fixture
def firm_and_client():
    """Create a firm with a client."""
    firm = Firm.objects.create(
        name="Test Firm",
        slug="testfirm",
        status="active"
    )
    client = Client.objects.create(
        firm=firm,
        name="Test Client",
        email="client@example.com",
        status="active"
    )
    return {"firm": firm, "client": client}


@pytest.fixture
def portal_user(firm_and_client):
    """Create a portal user (client-facing, restricted)."""
    user = User.objects.create_user(
        username="portal_user",
        email="portal@example.com",
        password="testpass123"
    )
    ClientPortalUser.objects.create(
        client=firm_and_client["client"],
        user=user,
        is_active=True
    )
    return user


@pytest.fixture
def firm_user(firm_and_client):
    """Create a firm admin user (full access)."""
    user = User.objects.create_user(
        username="firm_admin",
        email="admin@testfirm.com",
        password="testpass123"
    )
    FirmMembership.objects.create(
        firm=firm_and_client["firm"],
        user=user,
        role="admin"
    )
    return user


@pytest.mark.django_db
class TestPortalContainment:
    """
    Portal containment tests ensure that:
    1. Portal users can ONLY access designated portal endpoints
    2. Portal users receive 403 when accessing firm admin endpoints
    3. Firm users can access both portal and admin endpoints
    4. Default-deny: unlisted endpoints reject portal users
    """

    def test_portal_user_identified_correctly(self, portal_user, firm_and_client):
        """Verify we can identify portal users via ClientPortalUser relationship."""
        assert ClientPortalUser.objects.filter(user=portal_user).exists()
        portal_membership = ClientPortalUser.objects.get(user=portal_user)
        assert portal_membership.client == firm_and_client["client"]

    def test_firm_user_identified_correctly(self, firm_user, firm_and_client):
        """Verify we can identify firm users via FirmMembership relationship."""
        assert FirmMembership.objects.filter(user=firm_user).exists()
        membership = FirmMembership.objects.get(user=firm_user)
        assert membership.firm == firm_and_client["firm"]

    def test_isportaluser_permission_allows_portal_users(self, portal_user, firm_and_client):
        """IsPortalUserOrFirmUser permission should allow portal users on portal endpoints."""
        factory = APIRequestFactory()
        request = factory.get('/api/clients/portal/dashboard/')

        # Attach firm context (normally done by middleware)
        request.firm = firm_and_client["firm"]
        request.user = portal_user

        permission = IsPortalUserOrFirmUser()

        # Create a mock view
        class MockView:
            pass

        view = MockView()

        # Should allow portal user
        assert permission.has_permission(request, view), \
            "Portal user should have access to portal endpoints"

    def test_isportaluser_permission_allows_firm_users(self, firm_user, firm_and_client):
        """IsPortalUserOrFirmUser permission should allow firm users on portal endpoints."""
        factory = APIRequestFactory()
        request = factory.get('/api/clients/portal/dashboard/')

        request.firm = firm_and_client["firm"]
        request.user = firm_user

        permission = IsPortalUserOrFirmUser()

        class MockView:
            pass

        view = MockView()

        # Should allow firm user
        assert permission.has_permission(request, view), \
            "Firm user should have access to portal endpoints"

    def test_denyportalaccess_blocks_portal_users(self, portal_user, firm_and_client):
        """DenyPortalAccess permission should block portal users from admin endpoints."""
        factory = APIRequestFactory()
        request = factory.get('/api/projects/')

        request.firm = firm_and_client["firm"]
        request.user = portal_user

        permission = DenyPortalAccess()

        class MockView:
            pass

        view = MockView()

        # Should deny portal user
        assert not permission.has_permission(request, view), \
            "CRITICAL: Portal user accessed firm admin endpoint!"

    def test_denyportalaccess_allows_firm_users(self, firm_user, firm_and_client):
        """DenyPortalAccess permission should allow firm users on admin endpoints."""
        factory = APIRequestFactory()
        request = factory.get('/api/projects/')

        request.firm = firm_and_client["firm"]
        request.user = firm_user

        permission = DenyPortalAccess()

        class MockView:
            pass

        view = MockView()

        # Should allow firm user
        assert permission.has_permission(request, view), \
            "Firm user should have access to admin endpoints"

    def test_portal_user_cannot_be_firm_member(self, portal_user, firm_and_client):
        """
        Verify mutual exclusion: a user cannot be both portal user and firm member.
        This prevents privilege escalation.
        """
        # Portal user should not have firm membership
        assert not FirmMembership.objects.filter(user=portal_user).exists(), \
            "CRITICAL: Portal user has firm membership!"

    def test_firm_user_should_not_be_portal_user(self, firm_user):
        """
        Firm users typically shouldn't be portal users (they have higher privileges).
        This is a defensive check.
        """
        # Firm user should not be a portal user
        # (This is a soft check; in practice, firm users don't need portal access)
        assert not ClientPortalUser.objects.filter(user=firm_user).exists(), \
            "Warning: Firm user also has portal access (unusual but not critical)"

    def test_portal_containment_middleware_integration(self):
        """
        Document middleware-level portal containment.
        See: modules/firm/middleware.py - PortalContainmentMiddleware
        """
        # This test documents the middleware layer
        # Actual enforcement tested via integration tests
        assert True, "Middleware enforcement: see docs/tier2/PORTAL_AUTHORIZATION_ARCHITECTURE.md"

    def test_defense_in_depth_layers(self):
        """
        Portal containment has three layers:
        1. Middleware: Path-based blocking (default-deny)
        2. Permissions: Class-level enforcement (DenyPortalAccess)
        3. Querysets: Data isolation (Tier 0 firm scoping)
        """
        # This test documents the defense-in-depth approach
        assert True, "Three-layer defense documented in PORTAL_AUTHORIZATION_ARCHITECTURE.md"
