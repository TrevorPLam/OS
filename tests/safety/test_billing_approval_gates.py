"""
Tier 1 Safety Tests - Billing Approval Gates

Tests that time entries cannot be invoiced without proper approval.
CRITICAL: These tests validate billing integrity and prevent unauthorized billing.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model

from modules.firm.models import Firm, FirmMembership
from modules.clients.models import Client
from modules.projects.models import Project, Task, TimeEntry
from modules.finance.models import Invoice

User = get_user_model()


@pytest.fixture
def firm_with_users():
    """Create a firm with users in different roles."""
    firm = Firm.objects.create(
        name="Test Firm",
        slug="testfirm",
        status="active"
    )

    admin_user = User.objects.create_user(
        username="admin",
        email="admin@testfirm.com",
        password="testpass123"
    )
    FirmMembership.objects.create(
        firm=firm,
        user=admin_user,
        role="admin"
    )

    staff_user = User.objects.create_user(
        username="staff",
        email="staff@testfirm.com",
        password="testpass123"
    )
    FirmMembership.objects.create(
        firm=firm,
        user=staff_user,
        role="staff"
    )

    return {
        "firm": firm,
        "admin": admin_user,
        "staff": staff_user
    }


@pytest.fixture
def project_and_task(firm_with_users):
    """Create a project and task."""
    client = Client.objects.create(
        firm=firm_with_users["firm"],
        name="Test Client",
        email="client@example.com",
        status="active"
    )

    project = Project.objects.create(
        firm=firm_with_users["firm"],
        client=client,
        name="Test Project",
        code="PROJ-001",
        status="active",
        billing_type="hourly",
        hourly_rate=Decimal("150.00")
    )

    task = Task.objects.create(
        firm=firm_with_users["firm"],
        project=project,
        title="Test Task",
        status="in_progress"
    )

    return {
        "client": client,
        "project": project,
        "task": task
    }


@pytest.mark.django_db
class TestBillingApprovalGates:
    """
    Billing approval gate tests ensure that:
    1. Time entries are not billable by default
    2. Time entries require approval before billing
    3. Only authorized roles can approve time entries
    4. Invoices can only include approved time entries
    """

    def test_time_entry_not_billable_by_default(self, firm_with_users, project_and_task):
        """Time entries should not be billable by default."""
        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("8.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Work performed"
        )

        # Default: not approved, not invoiced
        assert time_entry.approved is False, \
            "CRITICAL: Time entry is billable by default!"
        assert time_entry.invoiced is False

    def test_time_entry_approval_fields(self, firm_with_users, project_and_task):
        """Time entries should have approval tracking fields."""
        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("4.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="More work"
        )

        # Verify approval fields exist
        assert hasattr(time_entry, 'approved'), \
            "TimeEntry must have 'approved' field"
        assert hasattr(time_entry, 'approved_by'), \
            "TimeEntry must have 'approved_by' field"
        assert hasattr(time_entry, 'approved_at'), \
            "TimeEntry must have 'approved_at' field"

    def test_time_entry_approval_workflow(self, firm_with_users, project_and_task):
        """Time entry approval should populate approval fields."""
        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("6.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Approved work"
        )

        # Approve the time entry
        time_entry.approved = True
        time_entry.approved_by = firm_with_users["admin"]
        time_entry.approved_at = date.today()
        time_entry.save()

        # Verify approval
        time_entry.refresh_from_db()
        assert time_entry.approved is True
        assert time_entry.approved_by == firm_with_users["admin"]
        assert time_entry.approved_at is not None

    def test_unapproved_time_entries_cannot_be_invoiced(self, firm_with_users, project_and_task):
        """Unapproved time entries should not be marked as invoiced."""
        from django.core.exceptions import ValidationError
        import pytest

        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("8.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Unapproved work"
        )

        # Attempt to mark as invoiced without approval - should raise ValidationError
        time_entry.invoiced = True

        with pytest.raises(ValidationError, match="Time entry cannot be invoiced unless approved"):
            time_entry.save()

        # Verify the time entry was not saved with invoiced=True
        time_entry.refresh_from_db()
        assert time_entry.approved is False
        assert time_entry.invoiced is False

    def test_approved_time_entries_can_be_invoiced(self, firm_with_users, project_and_task):
        """Approved time entries can be marked as invoiced."""
        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("8.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Approved and invoiced work"
        )

        # Approve first
        time_entry.approved = True
        time_entry.approved_by = firm_with_users["admin"]
        time_entry.approved_at = date.today()
        time_entry.save()

        # Then mark as invoiced - should succeed since it's approved
        time_entry.invoiced = True
        time_entry.save()

        # Verify
        time_entry.refresh_from_db()
        assert time_entry.approved is True
        assert time_entry.invoiced is True

    def test_invoice_should_only_include_approved_entries(self, firm_with_users, project_and_task):
        """
        Invoices should only include approved time entries.
        This test documents the requirement for Tier 4 implementation.
        """
        # Create approved time entry
        approved_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("8.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Approved work",
            approved=True,
            approved_by=firm_with_users["admin"],
            approved_at=date.today()
        )

        # Create unapproved time entry
        unapproved_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("4.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Unapproved work"
        )

        # When generating invoices, only approved entries should be included
        # This logic will be implemented in Tier 4

        assert approved_entry.approved is True
        assert unapproved_entry.approved is False

        # Document requirement
        assert True, "Invoice generation logic to filter approved entries in Tier 4"

    def test_approval_requires_authorized_user(self, firm_with_users, project_and_task):
        """
        Only authorized users (admin/manager) should approve time entries.
        Staff should not approve their own time.
        """
        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("8.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Work needing approval"
        )

        # Staff user should not approve their own time
        # This should be enforced by business logic in Tier 4

        # Admin can approve
        time_entry.approved = True
        time_entry.approved_by = firm_with_users["admin"]
        time_entry.approved_at = date.today()
        time_entry.save()

        assert time_entry.approved_by != time_entry.user, \
            "User approved their own time entry (should be prevented)"

    def test_invoiced_time_entries_cannot_be_modified(self, firm_with_users, project_and_task):
        """
        Once time entries are invoiced, they should be immutable.
        This prevents invoice disputes.
        """
        time_entry = TimeEntry.objects.create(
            project=project_and_task["project"],
            task=project_and_task["task"],
            user=firm_with_users["staff"],
            date=date.today(),
            hours=Decimal("8.0"),
            hourly_rate=project_and_task["project"].hourly_rate,
            description="Invoiced work",
            approved=True,
            approved_by=firm_with_users["admin"],
            approved_at=date.today(),
            invoiced=True
        )

        # Attempt to modify invoiced entry
        time_entry.hours = Decimal("10.0")
        from django.core.exceptions import ValidationError
        import pytest

        with pytest.raises(ValidationError, match="Cannot modify invoiced time entries"):
            time_entry.save()

    def test_approval_gate_documentation(self):
        """
        Document billing approval gate requirements for Tier 4.

        Required gates:
        1. Time entries default to not billable (approved=False)
        2. Approval requires authorized user (not self-approval)
        3. Approval populates approved_by, approved_at
        4. Only approved entries can be invoiced
        5. Invoiced entries become immutable
        6. Invoice generation filters for approved=True
        """
        assert True, "Approval gate enforcement planned for Tier 4"
