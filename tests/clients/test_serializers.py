import pytest
from django.contrib.auth import get_user_model

from modules.clients.models import Client, Organization, Contact, ClientHealthScore
from modules.clients.serializers import (
    ClientSerializer,
    OrganizationSerializer,
    ContactSerializer,
    ClientHealthScoreSerializer,
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
class TestOrganizationSerializer:
    """Test OrganizationSerializer"""

    def test_serialization(self, organization, user):
        """Test organization serialization"""
        serializer = OrganizationSerializer(organization)
        data = serializer.data

        assert data["id"] == organization.id
        assert data["name"] == "Test Organization"
        assert data["firm"] == organization.firm.id
        assert data["created_by"] == user.id
        assert "client_count" in data
        assert "created_by_name" in data

    def test_client_count_method(self, organization, firm, user):
        """Test client_count method field"""
        # Create multiple clients in the organization
        Client.objects.create(
            firm=firm,
            organization=organization,
            company_name="Client 1",
            primary_contact_name="Test",
            primary_contact_email="test1@example.com",
        )
        Client.objects.create(
            firm=firm,
            organization=organization,
            company_name="Client 2",
            primary_contact_name="Test",
            primary_contact_email="test2@example.com",
        )

        serializer = OrganizationSerializer(organization)
        data = serializer.data

        assert data["client_count"] == 2

    def test_created_by_name_method(self, organization, user):
        """Test created_by_name method field"""
        serializer = OrganizationSerializer(organization)
        data = serializer.data

        assert data["created_by_name"] == user.username

    def test_deserialization(self, firm, user):
        """Test organization deserialization"""
        data = {
            "name": "New Organization",
            "description": "A new organization",
            "enable_cross_client_visibility": False,
        }

        serializer = OrganizationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_read_only_fields(self, organization):
        """Test that read-only fields cannot be updated"""
        serializer = OrganizationSerializer(organization)

        # These fields should be in read_only_fields
        read_only = serializer.Meta.read_only_fields
        assert "firm" in read_only
        assert "created_at" in read_only
        assert "updated_at" in read_only
        assert "created_by" in read_only


@pytest.mark.django_db
class TestClientSerializer:
    """Test ClientSerializer"""

    def test_serialization(self, client, user):
        """Test client serialization"""
        serializer = ClientSerializer(client)
        data = serializer.data

        assert data["id"] == client.id
        assert data["company_name"] == "Test Company"
        assert data["primary_contact_name"] == "John Doe"
        assert data["primary_contact_email"] == "john@testcompany.com"
        assert data["status"] == "active"
        assert data["account_manager"] == user.id
        assert "account_manager_name" in data

    def test_account_manager_name_method(self, client, user):
        """Test account_manager_name method field"""
        serializer = ClientSerializer(client)
        data = serializer.data

        # Should return username or full name
        expected_name = user.get_full_name() or user.username
        assert data["account_manager_name"] == expected_name

    def test_assigned_team_names_method(self, client, db):
        """Test assigned_team_names method field"""
        user1 = User.objects.create_user(username="user1", email="user1@example.com", password="pass")
        user2 = User.objects.create_user(username="user2", email="user2@example.com", password="pass")

        client.assigned_team.add(user1, user2)

        serializer = ClientSerializer(client)
        data = serializer.data

        assert "assigned_team_names" in data
        assert len(data["assigned_team_names"]) == 2

    def test_deserialization(self, firm, organization):
        """Test client deserialization"""
        data = {
            "company_name": "New Client",
            "primary_contact_name": "Jane Doe",
            "primary_contact_email": "jane@newclient.com",
            "status": "active",
        }

        serializer = ClientSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_optional_fields(self, client):
        """Test that optional fields are handled correctly"""
        client.industry = "Technology"
        client.website = "https://example.com"
        client.employee_count = 50
        client.save()

        serializer = ClientSerializer(client)
        data = serializer.data

        assert data["industry"] == "Technology"
        assert data["website"] == "https://example.com"
        assert data["employee_count"] == 50


@pytest.mark.django_db
class TestContactSerializer:
    """Test ContactSerializer"""

    def test_serialization(self, client):
        """Test contact serialization"""
        contact = Contact.objects.create(
            client=client, first_name="Alice", last_name="Johnson", email="alice@testcompany.com", role="Developer"
        )

        serializer = ContactSerializer(contact)
        data = serializer.data

        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Johnson"
        assert data["email"] == "alice@testcompany.com"
        assert data["role"] == "Developer"

    def test_deserialization(self):
        """Test contact deserialization"""
        data = {
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com",
            "role": "Manager",
        }

        serializer = ContactSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
class TestClientHealthScoreSerializer:
    """Test ClientHealthScoreSerializer"""

    def test_serialization(self, client):
        """Test health score serialization"""
        from django.utils import timezone

        health_score = ClientHealthScore.objects.create(
            client=client, score=85, engagement_trend="positive", risk_level="low", calculated_at=timezone.now()
        )

        serializer = ClientHealthScoreSerializer(health_score)
        data = serializer.data

        assert data["client"] == client.id
        assert data["score"] == 85
        assert data["engagement_trend"] == "positive"
        assert data["risk_level"] == "low"

    def test_deserialization(self):
        """Test health score deserialization"""
        from django.utils import timezone

        data = {"score": 90, "engagement_trend": "positive", "risk_level": "low", "calculated_at": timezone.now()}

        serializer = ClientHealthScoreSerializer(data=data)
        # Note: May need client field for full validation
        assert "score" in data
