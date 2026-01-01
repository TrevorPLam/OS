"""
Tests for Client Acceptance Gate (Medium Feature 2.8).

Tests the client acceptance workflow before invoicing.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.clients.models import Client
from modules.firm.models import Firm
from modules.projects.models import Project

User = get_user_model()


@pytest.fixture
def firm(db):
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Consulting Firm",
        slug="test-firm",
        subdomain="test",
    )


@pytest.fixture
def user(db, firm):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        firm=firm,
    )


@pytest.fixture
def client(db, firm):
    """Create a test client."""
    return Client.objects.create(
        firm=firm,
        company_name="Test Client Co",
        email="client@example.com",
    )


@pytest.fixture
def project(db, firm, client, user):
    """Create a test project."""
    return Project.objects.create(
        firm=firm,
        client=client,
        project_code="PROJ-001",
        name="Test Project",
        status="in_progress",
        billing_type="time_and_materials",
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
        project_manager=user,
    )


@pytest.mark.django_db
class TestClientAcceptanceGate:
    """Test client acceptance gate before invoicing (Medium Feature 2.8)."""

    def test_mark_client_accepted_success(self, project, user):
        """Test marking a project as client-accepted."""
        assert not project.client_accepted
        assert project.acceptance_date is None
        assert project.accepted_by is None

        notes = "Client signed off on all deliverables"
        project.mark_client_accepted(user, notes)

        assert project.client_accepted is True
        assert project.acceptance_date == timezone.now().date()
        assert project.accepted_by == user
        assert project.acceptance_notes == notes

    def test_mark_client_accepted_already_accepted_fails(self, project, user):
        """Test that accepting an already accepted project fails."""
        project.mark_client_accepted(user, "Initial acceptance")

        with pytest.raises(ValidationError, match="already been accepted"):
            project.mark_client_accepted(user, "Trying again")

    def test_can_generate_invoice_in_progress_project(self, project):
        """Test that in-progress projects can be invoiced (not completed yet)."""
        project.status = "in_progress"
        project.save()

        can_invoice, reason = project.can_generate_invoice()

        assert can_invoice is True
        assert reason == ""

    def test_can_generate_invoice_on_hold_project(self, project):
        """Test that on-hold projects can be invoiced."""
        project.status = "on_hold"
        project.save()

        can_invoice, reason = project.can_generate_invoice()

        assert can_invoice is True
        assert reason == ""

    def test_cannot_invoice_cancelled_project(self, project):
        """Test that cancelled projects cannot be invoiced."""
        project.status = "cancelled"
        project.save()

        can_invoice, reason = project.can_generate_invoice()

        assert can_invoice is False
        assert "cancelled" in reason.lower()

    def test_cannot_invoice_planning_project(self, project):
        """Test that projects in planning phase cannot be invoiced."""
        project.status = "planning"
        project.save()

        can_invoice, reason = project.can_generate_invoice()

        assert can_invoice is False
        assert "planning" in reason.lower()

    def test_cannot_invoice_completed_without_acceptance(self, project):
        """Test that completed projects require client acceptance before final invoicing."""
        project.status = "completed"
        project.save()

        can_invoice, reason = project.can_generate_invoice()

        assert can_invoice is False
        assert "client-accepted" in reason.lower()
        assert "final invoicing" in reason.lower()

    def test_can_invoice_completed_with_acceptance(self, project, user):
        """Test that completed and accepted projects can be invoiced."""
        project.status = "completed"
        project.save()
        project.mark_client_accepted(user, "Project completed successfully")

        can_invoice, reason = project.can_generate_invoice()

        assert can_invoice is True
        assert reason == ""

    def test_acceptance_gate_workflow(self, project, user):
        """Test the complete acceptance gate workflow."""
        # 1. Project in progress - can invoice for interim billing
        project.status = "in_progress"
        project.save()
        can_invoice, _ = project.can_generate_invoice()
        assert can_invoice is True

        # 2. Project completed - cannot invoice until accepted
        project.status = "completed"
        project.save()
        can_invoice, reason = project.can_generate_invoice()
        assert can_invoice is False
        assert "client-accepted" in reason.lower()

        # 3. Client accepts project - now can invoice
        project.mark_client_accepted(user, "All deliverables approved")
        can_invoice, _ = project.can_generate_invoice()
        assert can_invoice is True

    def test_acceptance_with_empty_notes(self, project, user):
        """Test that acceptance notes are optional."""
        project.mark_client_accepted(user, "")

        assert project.client_accepted is True
        assert project.acceptance_notes == ""

    def test_acceptance_preserves_other_fields(self, project, user):
        """Test that marking acceptance doesn't affect other fields."""
        original_name = project.name
        original_status = project.status
        original_budget = project.budget

        project.mark_client_accepted(user, "Accepted")

        # Refresh from DB
        project.refresh_from_db()

        assert project.name == original_name
        assert project.status == original_status
        assert project.budget == original_budget
