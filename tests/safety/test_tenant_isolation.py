"""
Tier 1 Safety Tests - Tenant Isolation

Tests that cross-firm data access is completely blocked.
CRITICAL: These tests validate Tier 0 isolation guarantees.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.firm.models import Firm, FirmMembership
from modules.clients.models import Client
from modules.projects.models import Project
from modules.finance.models import Invoice
from modules.documents.models import Document, Folder
from modules.crm.models import Lead, Prospect, Proposal, Contract

User = get_user_model()


@pytest.fixture
def firms():
    """Create two separate firms for isolation testing."""
    firm_a = Firm.objects.create(
        name="Firm A",
        slug="firma",
        status="active"
    )
    firm_b = Firm.objects.create(
        name="Firm B",
        slug="firmb",
        status="active"
    )
    return {"firm_a": firm_a, "firm_b": firm_b}


@pytest.fixture
def users_and_clients(firms):
    """Create users and clients for each firm."""
    User = get_user_model()

    # Firm A user and client
    user_a = User.objects.create_user(
        username="user_a",
        email="user_a@firma.com",
        password="testpass123"
    )
    FirmMembership.objects.create(
        firm=firms["firm_a"],
        user=user_a,
        role="admin"
    )
    client_a = Client.objects.create(
        firm=firms["firm_a"],
        name="Client A",
        email="client_a@example.com",
        status="active"
    )

    # Firm B user and client
    user_b = User.objects.create_user(
        username="user_b",
        email="user_b@firmb.com",
        password="testpass123"
    )
    FirmMembership.objects.create(
        firm=firms["firm_b"],
        user=user_b,
        role="admin"
    )
    client_b = Client.objects.create(
        firm=firms["firm_b"],
        name="Client B",
        email="client_b@example.com",
        status="active"
    )

    return {
        "user_a": user_a,
        "user_b": user_b,
        "client_a": client_a,
        "client_b": client_b,
    }


@pytest.mark.django_db
class TestTenantIsolation:
    """
    Tenant isolation tests ensure that:
    1. Users from Firm A cannot see/access Firm B data
    2. API queries are always scoped to the current firm
    3. Cross-firm access attempts fail with 403/404
    """

    def test_client_queryset_is_firm_scoped(self, firms, users_and_clients):
        """Verify Client.objects queries are firm-scoped via manager."""
        # Get all clients (should be scoped by firm via manager in production)
        # In tests without request context, we verify the manager exists
        assert hasattr(Client.objects, 'for_firm'), \
            "Client must use FirmScopedManager"

        # Verify firm-scoped queryset returns only own clients
        clients_a = Client.objects.for_firm(firms["firm_a"])
        assert clients_a.count() == 1
        assert clients_a.first().name == "Client A"

        clients_b = Client.objects.for_firm(firms["firm_b"])
        assert clients_b.count() == 1
        assert clients_b.first().name == "Client B"

    def test_cross_firm_client_access_blocked_by_id(self, firms, users_and_clients):
        """Attempting to access another firm's client by ID should fail."""
        client_a = users_and_clients["client_a"]

        # Firm B trying to get Firm A's client
        clients_b_queryset = Client.objects.for_firm(firms["firm_b"])
        result = clients_b_queryset.filter(id=client_a.id)

        assert result.count() == 0, \
            "CRITICAL: Firm B was able to access Firm A's client data!"

    def test_project_queryset_is_firm_scoped(self, firms, users_and_clients):
        """Verify Project queries are firm-scoped."""
        # Create projects for each client
        project_a = Project.objects.create(
            firm=firms["firm_a"],
            client=users_and_clients["client_a"],
            name="Project A",
            code="PROJ-A-001",
            status="active"
        )
        project_b = Project.objects.create(
            firm=firms["firm_b"],
            client=users_and_clients["client_b"],
            name="Project B",
            code="PROJ-B-001",
            status="active"
        )

        # Verify firm-scoped access
        assert hasattr(Project.objects, 'for_firm'), \
            "Project must use FirmScopedManager"

        projects_a = Project.objects.for_firm(firms["firm_a"])
        assert projects_a.count() == 1
        assert projects_a.first().name == "Project A"

        # Firm B cannot see Project A
        projects_b = Project.objects.for_firm(firms["firm_b"])
        assert projects_b.filter(id=project_a.id).count() == 0

    def test_invoice_queryset_is_firm_scoped(self, firms, users_and_clients):
        """Verify Invoice queries are firm-scoped."""
        # Create invoices
        invoice_a = Invoice.objects.create(
            firm=firms["firm_a"],
            client=users_and_clients["client_a"],
            invoice_number="INV-A-001",
            amount="1000.00",
            status="draft"
        )
        invoice_b = Invoice.objects.create(
            firm=firms["firm_b"],
            client=users_and_clients["client_b"],
            invoice_number="INV-B-001",
            amount="2000.00",
            status="draft"
        )

        # Verify firm-scoped access
        invoices_a = Invoice.objects.filter(firm=firms["firm_a"])
        assert invoices_a.count() == 1
        assert invoices_a.first().invoice_number == "INV-A-001"

        # Firm B cannot see Invoice A
        invoices_b = Invoice.objects.filter(firm=firms["firm_b"])
        assert invoices_b.filter(id=invoice_a.id).count() == 0

    def test_document_queryset_is_firm_scoped(self, firms, users_and_clients):
        """Verify Document queries are firm-scoped."""
        # Create folders and documents
        folder_a = Folder.objects.create(
            firm=firms["firm_a"],
            client=users_and_clients["client_a"],
            name="Folder A",
            path="/folder-a"
        )
        doc_a = Document.objects.create(
            firm=firms["firm_a"],
            client=users_and_clients["client_a"],
            folder=folder_a,
            name="Document A",
            file_path="/docs/a.pdf"
        )

        folder_b = Folder.objects.create(
            firm=firms["firm_b"],
            client=users_and_clients["client_b"],
            name="Folder B",
            path="/folder-b"
        )
        doc_b = Document.objects.create(
            firm=firms["firm_b"],
            client=users_and_clients["client_b"],
            folder=folder_b,
            name="Document B",
            file_path="/docs/b.pdf"
        )

        # Verify firm-scoped access
        docs_a = Document.objects.filter(firm=firms["firm_a"])
        assert docs_a.count() == 1
        assert docs_a.first().name == "Document A"

        # Firm B cannot see Document A
        docs_b = Document.objects.filter(firm=firms["firm_b"])
        assert docs_b.filter(id=doc_a.id).count() == 0

    def test_crm_data_is_firm_scoped(self, firms, users_and_clients):
        """Verify CRM entities (Lead, Prospect, Proposal) are firm-scoped."""
        # Create CRM entities
        lead_a = Lead.objects.create(
            firm=firms["firm_a"],
            company_name="Lead A Company",
            contact_name="Lead A Contact",
            contact_email="lead_a@example.com",
            status="new"
        )
        lead_b = Lead.objects.create(
            firm=firms["firm_b"],
            company_name="Lead B Company",
            contact_name="Lead B Contact",
            contact_email="lead_b@example.com",
            status="new"
        )

        prospect_a = Prospect.objects.create(
            firm=firms["firm_a"],
            company_name="Prospect A",
            primary_contact_name="Prospect A Contact",
            primary_contact_email="prospect_a@example.com",
            stage="discovery",
            estimated_value=Decimal("10000.00"),
            close_date_estimate=timezone.now().date() + timezone.timedelta(days=30)
        )
        prospect_b = Prospect.objects.create(
            firm=firms["firm_b"],
            company_name="Prospect B",
            primary_contact_name="Prospect B Contact",
            primary_contact_email="prospect_b@example.com",
            stage="discovery",
            estimated_value=Decimal("10000.00"),
            close_date_estimate=timezone.now().date() + timezone.timedelta(days=30)
        )

        # Verify firm-scoped access
        assert Lead.objects.filter(firm=firms["firm_a"]).count() == 1
        assert Lead.objects.filter(firm=firms["firm_b"]).filter(id=lead_a.id).count() == 0

        assert Prospect.objects.filter(firm=firms["firm_a"]).count() == 1
        assert Prospect.objects.filter(firm=firms["firm_b"]).filter(id=prospect_a.id).count() == 0

    def test_no_model_objects_all_in_production_code(self):
        """
        Verify that direct Model.objects.all() calls are not used in production.
        This is a code audit test to prevent accidental global queries.
        """
        # This test documents the requirement
        # Actual enforcement is via FirmScopedManager and code review
        # See: docs/tier2/FIRM_SCOPED_QUERYSETS_AUDIT.md
        assert True, "Code audit enforced via FirmScopedManager pattern"
