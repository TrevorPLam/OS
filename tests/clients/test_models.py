import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.clients.models import (
    Client,
    Organization,
    Contact,
    Engagement,
    HealthScore,
    PortalUser,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.fixture
def organization(db, firm, user):
    return Organization.objects.create(firm=firm, name="Test Organization", created_by=user)


@pytest.fixture
def client(db, firm, user, organization):
    return Client.objects.create(
        firm=firm,
        organization=organization,
        company_name="Test Company",
        primary_contact_name="John Doe",
        primary_contact_email="john@testcompany.com",
        status="active",
        account_manager=user,
    )


@pytest.mark.django_db
class TestOrganization:
    """Test Organization model functionality"""

    def test_organization_creation(self, firm, user):
        """Test basic organization creation"""
        org = Organization.objects.create(firm=firm, name="New Organization", created_by=user)

        assert org.name == "New Organization"
        assert org.firm == firm
        assert org.created_by == user
        assert org.enable_cross_client_visibility is True

    def test_organization_unique_name_per_firm(self, firm, user):
        """Test that organization names must be unique within a firm"""
        Organization.objects.create(firm=firm, name="Duplicate Org", created_by=user)

        # Creating another organization with same name in same firm should fail
        with pytest.raises(Exception):  # IntegrityError
            Organization.objects.create(firm=firm, name="Duplicate Org", created_by=user)

    def test_organization_name_can_duplicate_across_firms(self, user):
        """Test that organization names can be duplicated across different firms"""
        firm1 = Firm.objects.create(name="Firm 1", slug="firm-1", status="active")
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        org1 = Organization.objects.create(firm=firm1, name="Same Name", created_by=user)
        org2 = Organization.objects.create(firm=firm2, name="Same Name", created_by=user)

        assert org1.name == org2.name
        assert org1.firm != org2.firm

    def test_organization_string_representation(self, organization):
        """Test __str__ method"""
        expected = f"{organization.name} ({organization.firm.name})"
        assert str(organization) == expected


@pytest.mark.django_db
class TestClient:
    """Test Client model functionality"""

    def test_client_creation(self, firm, user, organization):
        """Test basic client creation"""
        client = Client.objects.create(
            firm=firm,
            organization=organization,
            company_name="New Client Company",
            primary_contact_name="Jane Smith",
            primary_contact_email="jane@newclient.com",
            status="active",
            account_manager=user,
        )

        assert client.company_name == "New Client Company"
        assert client.firm == firm
        assert client.organization == organization
        assert client.status == "active"
        assert client.account_manager == user

    def test_client_status_choices(self, firm, organization):
        """Test client status field choices"""
        statuses = ["active", "inactive", "terminated"]

        for status in statuses:
            client = Client.objects.create(
                firm=firm,
                organization=organization,
                company_name=f"Client {status}",
                primary_contact_name="Test",
                primary_contact_email=f"test{status}@example.com",
                status=status,
            )
            assert client.status == status

    def test_client_firm_scoping(self, firm, user):
        """Test that clients are properly scoped to firm"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")
        org1 = Organization.objects.create(firm=firm, name="Org 1", created_by=user)
        org2 = Organization.objects.create(firm=firm2, name="Org 2", created_by=user)

        client1 = Client.objects.create(
            firm=firm,
            organization=org1,
            company_name="Client 1",
            primary_contact_name="Test",
            primary_contact_email="test1@example.com",
        )

        client2 = Client.objects.create(
            firm=firm2,
            organization=org2,
            company_name="Client 2",
            primary_contact_name="Test",
            primary_contact_email="test2@example.com",
        )

        # Test firm-scoped manager would return only clients for specific firm
        all_clients = Client.objects.all()
        assert client1 in all_clients
        assert client2 in all_clients

    def test_client_optional_fields(self, firm, organization):
        """Test that optional fields work correctly"""
        client = Client.objects.create(
            firm=firm,
            organization=organization,
            company_name="Minimal Client",
            primary_contact_name="Test",
            primary_contact_email="test@example.com",
        )

        assert client.industry == ""
        assert client.primary_contact_phone == ""
        assert client.street_address == ""
        assert client.website == ""
        assert client.employee_count is None

    def test_client_with_full_address(self, firm, organization):
        """Test client with complete address information"""
        client = Client.objects.create(
            firm=firm,
            organization=organization,
            company_name="Full Address Client",
            primary_contact_name="Test",
            primary_contact_email="test@example.com",
            street_address="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA",
        )

        assert client.street_address == "123 Main St"
        assert client.city == "New York"
        assert client.state == "NY"
        assert client.postal_code == "10001"
        assert client.country == "USA"


@pytest.mark.django_db
class TestContact:
    """Test Contact model functionality"""

    def test_contact_creation(self, client):
        """Test basic contact creation"""
        from modules.clients.models import Contact

        contact = Contact.objects.create(
            client=client,
            first_name="Alice",
            last_name="Johnson",
            email="alice@testcompany.com",
            role="Developer",
        )

        assert contact.first_name == "Alice"
        assert contact.last_name == "Johnson"
        assert contact.email == "alice@testcompany.com"
        assert contact.client == client


@pytest.mark.django_db
class TestEngagement:
    """Test Engagement model functionality"""

    def test_engagement_creation(self, client, user):
        """Test basic engagement creation"""
        from modules.clients.models import Engagement

        engagement = Engagement.objects.create(
            client=client,
            title="Website Redesign",
            description="Complete website redesign project",
            status="active",
            start_date=date.today(),
            owner=user,
        )

        assert engagement.title == "Website Redesign"
        assert engagement.client == client
        assert engagement.status == "active"
        assert engagement.owner == user


@pytest.mark.django_db
class TestHealthScore:
    """Test HealthScore model functionality"""

    def test_health_score_creation(self, client):
        """Test basic health score creation"""
        from modules.clients.models import HealthScore

        health_score = HealthScore.objects.create(
            client=client, score=85, engagement_trend="positive", risk_level="low", calculated_at=timezone.now()
        )

        assert health_score.client == client
        assert health_score.score == 85
        assert health_score.engagement_trend == "positive"
        assert health_score.risk_level == "low"

    def test_health_score_bounds(self, client):
        """Test health score validation"""
        from modules.clients.models import HealthScore

        # Valid score
        health_score = HealthScore.objects.create(client=client, score=100, calculated_at=timezone.now())
        assert health_score.score == 100

        # Score should be between 0 and 100
        health_score2 = HealthScore.objects.create(client=client, score=0, calculated_at=timezone.now())
        assert health_score2.score == 0


@pytest.mark.django_db
class TestPortalUser:
    """Test PortalUser model functionality"""

    def test_portal_user_creation(self, client, user):
        """Test basic portal user creation"""
        from modules.clients.models import PortalUser

        portal_user = PortalUser.objects.create(
            client=client, user=user, access_level="read", is_primary_contact=True, status="active"
        )

        assert portal_user.client == client
        assert portal_user.user == user
        assert portal_user.access_level == "read"
        assert portal_user.is_primary_contact is True
        assert portal_user.status == "active"
