"""
Tests for Contact 360° Graph View (CRM-INT-1).

Tests cover:
- Graph data structure and format
- Firm isolation
- Relationship strength calculations
- Node and edge generation
- Filtering by contact and depth
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from modules.crm.models import Account, AccountContact, AccountRelationship
from modules.firm.models import Firm


User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def firm():
    """Create test firm."""
    return Firm.objects.create(
        name="Test Firm",
        slug="test-firm"
    )


@pytest.fixture
def user(firm):
    """Create test user."""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    user.firm = firm
    user.save()
    return user


@pytest.fixture
def accounts(firm, user):
    """Create test accounts."""
    account1 = Account.objects.create(
        firm=firm,
        name="Company A",
        account_type="customer",
        status="active",
        owner=user
    )
    account2 = Account.objects.create(
        firm=firm,
        name="Company B",
        account_type="partner",
        status="active",
        owner=user
    )
    account3 = Account.objects.create(
        firm=firm,
        name="Company C",
        account_type="prospect",
        status="active",
        owner=user
    )
    return {"account1": account1, "account2": account2, "account3": account3}


@pytest.fixture
def contacts(accounts, user):
    """Create test contacts."""
    contact1 = AccountContact.objects.create(
        account=accounts["account1"],
        first_name="John",
        last_name="Doe",
        email="john.doe@companya.com",
        job_title="CEO",
        is_primary_contact=True,
        is_decision_maker=True,
        is_active=True,
        created_by=user
    )
    contact2 = AccountContact.objects.create(
        account=accounts["account1"],
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@companya.com",
        job_title="CTO",
        is_primary_contact=False,
        is_decision_maker=True,
        is_active=True,
        created_by=user
    )
    contact3 = AccountContact.objects.create(
        account=accounts["account2"],
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@companyb.com",
        job_title="Manager",
        is_primary_contact=True,
        is_decision_maker=False,
        is_active=True,
        created_by=user
    )
    return {"contact1": contact1, "contact2": contact2, "contact3": contact3}


@pytest.fixture
def relationships(accounts, user):
    """Create test account relationships."""
    rel1 = AccountRelationship.objects.create(
        from_account=accounts["account1"],
        to_account=accounts["account2"],
        relationship_type="partnership",
        status="active",
        created_by=user
    )
    rel2 = AccountRelationship.objects.create(
        from_account=accounts["account2"],
        to_account=accounts["account3"],
        relationship_type="vendor_client",
        status="active",
        created_by=user
    )
    return {"rel1": rel1, "rel2": rel2}


@pytest.mark.integration
@pytest.mark.django_db
class TestContactGraphView:
    """Test suite for Contact 360° Graph View endpoint."""

    def test_graph_view_requires_authentication(self, api_client):
        """Test that graph view requires authentication."""
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        assert response.status_code == 401

    def test_graph_view_returns_valid_structure(self, api_client, user, contacts, relationships):
        """Test that graph view returns valid graph structure."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data
        
        # Check metadata
        assert "total_contacts" in data["metadata"]
        assert "total_accounts" in data["metadata"]
        assert "total_relationships" in data["metadata"]

    def test_graph_view_contains_contacts_and_accounts(self, api_client, user, contacts, relationships):
        """Test that graph contains both contact and account nodes."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check nodes contain both types
        node_types = {node["type"] for node in data["nodes"]}
        assert "contact" in node_types
        assert "account" in node_types
        
        # Check we have the expected number of contacts
        contact_nodes = [n for n in data["nodes"] if n["type"] == "contact"]
        assert len(contact_nodes) == 3

    def test_graph_view_has_relationship_edges(self, api_client, user, contacts, relationships):
        """Test that graph contains relationship edges between accounts."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check edges
        edge_types = {edge["type"] for edge in data["edges"]}
        assert "belongs_to" in edge_types
        assert "relationship" in edge_types
        
        # Check relationship edges exist
        rel_edges = [e for e in data["edges"] if e["type"] == "relationship"]
        assert len(rel_edges) >= 1

    def test_graph_view_includes_strength_indicators(self, api_client, user, contacts, relationships):
        """Test that nodes and edges have strength indicators."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check contact nodes have strength
        contact_nodes = [n for n in data["nodes"] if n["type"] == "contact"]
        for node in contact_nodes:
            assert "strength" in node
            assert 0 <= node["strength"] <= 1
        
        # Check edges have strength
        for edge in data["edges"]:
            assert "strength" in edge
            assert 0 <= edge["strength"] <= 1

    def test_graph_view_filters_by_contact_id(self, api_client, user, contacts, relationships):
        """Test that graph can be filtered by specific contact."""
        api_client.force_authenticate(user=user)
        contact_id = contacts["contact1"].id
        
        response = api_client.get(f"/api/crm/account-contacts/graph_view/?contact_id={contact_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check metadata reflects focus contact
        assert data["metadata"]["focus_contact_id"] == str(contact_id)
        
        # Should only include contacts from related accounts
        contact_nodes = [n for n in data["nodes"] if n["type"] == "contact"]
        assert len(contact_nodes) > 0

    def test_graph_view_excludes_inactive_contacts_by_default(self, api_client, user, accounts):
        """Test that inactive contacts are excluded by default."""
        # Create inactive contact
        inactive_contact = AccountContact.objects.create(
            account=accounts["account1"],
            first_name="Inactive",
            last_name="User",
            email="inactive@companya.com",
            is_active=False
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check inactive contact is not in results
        contact_ids = [n["data"]["contact_id"] for n in data["nodes"] if n["type"] == "contact"]
        assert inactive_contact.id not in contact_ids

    def test_graph_view_includes_inactive_when_requested(self, api_client, user, accounts):
        """Test that inactive contacts are included when requested."""
        # Create inactive contact
        inactive_contact = AccountContact.objects.create(
            account=accounts["account1"],
            first_name="Inactive",
            last_name="User",
            email="inactive@companya.com",
            is_active=False
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/?include_inactive=true")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check inactive contact is in results
        contact_ids = [n["data"]["contact_id"] for n in data["nodes"] if n["type"] == "contact"]
        assert inactive_contact.id in contact_ids

    def test_graph_view_respects_firm_isolation(self, api_client, user, accounts):
        """Test that graph view respects firm boundaries."""
        # Create another firm and account
        other_firm = Firm.objects.create(name="Other Firm", slug="other-firm")
        other_account = Account.objects.create(
            firm=other_firm,
            name="Other Company",
            account_type="customer",
            status="active"
        )
        other_contact = AccountContact.objects.create(
            account=other_account,
            first_name="Other",
            last_name="Person",
            email="other@othercompany.com",
            is_active=True
        )
        
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check other firm's contact is not in results
        contact_ids = [n["data"]["contact_id"] for n in data["nodes"] if n["type"] == "contact"]
        assert other_contact.id not in contact_ids

    def test_graph_view_handles_nonexistent_contact_id(self, api_client, user):
        """Test that graph view handles invalid contact ID gracefully."""
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/crm/account-contacts/graph_view/?contact_id=99999")
        
        assert response.status_code == 404
        assert "error" in response.json()
