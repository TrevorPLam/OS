"""
Tests for Utilization Tracking and Reporting (Medium Feature 2.9).

Tests project and team utilization metrics.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model

from modules.clients.models import Client
from modules.firm.models import Firm
from modules.projects.models import Project, Task, TimeEntry

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
def user1(db, firm):
    """Create first test user."""
    return User.objects.create_user(
        email="user1@example.com",
        password="testpass123",
        firm=firm,
    )


@pytest.fixture
def user2(db, firm):
    """Create second test user."""
    return User.objects.create_user(
        email="user2@example.com",
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
def project(db, firm, client, user1):
    """Create a test project with budget."""
    return Project.objects.create(
        firm=firm,
        client=client,
        project_code="PROJ-001",
        name="Test Project",
        status="in_progress",
        billing_type="time_and_materials",
        budget=Decimal("10000.00"),
        hourly_rate=Decimal("100.00"),
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=30),
        project_manager=user1,
    )


@pytest.fixture
def task(db, project):
    """Create a test task."""
    return Task.objects.create(
        project=project,
        title="Test Task",
        status="in_progress",
        estimated_hours=Decimal("10.00"),
    )


@pytest.mark.django_db
class TestUtilizationTracking:
    """Test utilization tracking and reporting (Medium Feature 2.9)."""

    def test_calculate_utilization_no_time_entries(self, project):
        """Test utilization calculation with no time entries."""
        metrics = project.calculate_utilization_metrics()

        assert metrics["total_hours"] == Decimal("0.00")
        assert metrics["billable_hours"] == Decimal("0.00")
        assert metrics["non_billable_hours"] == Decimal("0.00")
        assert metrics["utilization_rate"] == Decimal("0.00")
        assert metrics["team_members"] == 0

    def test_calculate_utilization_with_billable_time(self, project, user1, task):
        """Test utilization with billable time entries."""
        # Add billable time entries
        TimeEntry.objects.create(
            project=project,
            task=task,
            user=user1,
            date=date.today(),
            hours=Decimal("8.00"),
            description="Billable work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("800.00"),
        )
        TimeEntry.objects.create(
            project=project,
            task=task,
            user=user1,
            date=date.today() - timedelta(days=1),
            hours=Decimal("4.00"),
            description="More billable work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("400.00"),
        )

        metrics = project.calculate_utilization_metrics()

        assert metrics["total_hours"] == Decimal("12.00")
        assert metrics["billable_hours"] == Decimal("12.00")
        assert metrics["non_billable_hours"] == Decimal("0.00")
        assert metrics["utilization_rate"] == Decimal("100.00")
        assert metrics["team_members"] == 1
        assert metrics["avg_hours_per_user"] == Decimal("12.00")

    def test_calculate_utilization_mixed_billable_non_billable(
        self, project, user1, user2, task
    ):
        """Test utilization with mixed billable and non-billable time."""
        # User 1: 8 billable, 2 non-billable
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("8.00"),
            description="Billable work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("800.00"),
        )
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("2.00"),
            description="Internal meetings",
            is_billable=False,
            hourly_rate=Decimal("0.00"),
            billed_amount=Decimal("0.00"),
        )

        # User 2: 6 billable, 4 non-billable
        TimeEntry.objects.create(
            project=project,
            user=user2,
            date=date.today(),
            hours=Decimal("6.00"),
            description="Billable work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("600.00"),
        )
        TimeEntry.objects.create(
            project=project,
            user=user2,
            date=date.today(),
            hours=Decimal("4.00"),
            description="Training",
            is_billable=False,
            hourly_rate=Decimal("0.00"),
            billed_amount=Decimal("0.00"),
        )

        metrics = project.calculate_utilization_metrics()

        assert metrics["total_hours"] == Decimal("20.00")
        assert metrics["billable_hours"] == Decimal("14.00")
        assert metrics["non_billable_hours"] == Decimal("6.00")
        assert metrics["utilization_rate"] == Decimal("70.00")  # 14/20 * 100
        assert metrics["team_members"] == 2
        assert metrics["avg_hours_per_user"] == Decimal("10.00")

    def test_calculate_utilization_with_budget(self, project, user1):
        """Test utilization calculation with budget comparison."""
        # Add 50 hours of time (budgeted hours = 10000/100 = 100 hours)
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("50.00"),
            description="Work done",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("5000.00"),
        )

        metrics = project.calculate_utilization_metrics()

        assert metrics["budgeted_hours"] == Decimal("100.00")  # 10000/100
        assert metrics["hours_variance"] == Decimal("-50.00")  # 50 - 100

    def test_calculate_utilization_over_budget(self, project, user1):
        """Test utilization when project exceeds budget hours."""
        # Add 120 hours (over budgeted 100 hours)
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("120.00"),
            description="Extended work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("12000.00"),
        )

        metrics = project.calculate_utilization_metrics()

        assert metrics["total_hours"] == Decimal("120.00")
        assert metrics["budgeted_hours"] == Decimal("100.00")
        assert metrics["hours_variance"] == Decimal("20.00")  # Over budget

    def test_calculate_utilization_date_range(self, project, user1):
        """Test utilization with date range filtering."""
        # Add entries across different dates
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date(2024, 1, 1),
            hours=Decimal("8.00"),
            description="January work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("800.00"),
        )
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date(2024, 2, 1),
            hours=Decimal("10.00"),
            description="February work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("1000.00"),
        )
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date(2024, 3, 1),
            hours=Decimal("12.00"),
            description="March work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("1200.00"),
        )

        # Filter to February only
        metrics = project.calculate_utilization_metrics(
            start_date=date(2024, 2, 1), end_date=date(2024, 2, 29)
        )

        assert metrics["total_hours"] == Decimal("10.00")
        assert metrics["billable_hours"] == Decimal("10.00")

    def test_calculate_user_utilization(self, firm, user1, project):
        """Test calculating utilization for a specific user."""
        # Add time entries for user1
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("8.00"),
            description="Billable work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("800.00"),
        )
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("2.00"),
            description="Non-billable work",
            is_billable=False,
            hourly_rate=Decimal("0.00"),
            billed_amount=Decimal("0.00"),
        )

        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        metrics = Project.calculate_user_utilization(firm, user1, start_date, end_date)

        assert metrics["total_hours"] == Decimal("10.00")
        assert metrics["billable_hours"] == Decimal("8.00")
        assert metrics["non_billable_hours"] == Decimal("2.00")
        assert metrics["utilization_rate"] == Decimal("80.00")  # 8/10 * 100
        assert metrics["projects_worked"] == 1
        assert metrics["user_id"] == user1.id
        assert metrics["user_email"] == user1.email

    def test_calculate_user_utilization_capacity(self, firm, user1, project):
        """Test user capacity utilization calculation."""
        # Add entries spanning 1 week (7 days = 1 week = 40 available hours)
        for i in range(5):  # 5 working days
            TimeEntry.objects.create(
                project=project,
                user=user1,
                date=date.today() - timedelta(days=i),
                hours=Decimal("8.00"),
                description=f"Day {i} work",
                is_billable=True,
                hourly_rate=Decimal("100.00"),
                billed_amount=Decimal("800.00"),
            )

        start_date = date.today() - timedelta(days=6)
        end_date = date.today()

        metrics = Project.calculate_user_utilization(firm, user1, start_date, end_date)

        assert metrics["total_hours"] == Decimal("40.00")
        assert metrics["available_hours"] == Decimal("40.00")  # 1 week = 40 hours
        assert metrics["capacity_utilization"] == Decimal("100.00")

    def test_calculate_user_utilization_multiple_projects(
        self, firm, user1, client, project
    ):
        """Test user utilization across multiple projects."""
        # Create second project
        project2 = Project.objects.create(
            firm=firm,
            client=client,
            project_code="PROJ-002",
            name="Second Project",
            status="in_progress",
            billing_type="time_and_materials",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30),
        )

        # Add time to both projects
        TimeEntry.objects.create(
            project=project,
            user=user1,
            date=date.today(),
            hours=Decimal("5.00"),
            description="Project 1 work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("500.00"),
        )
        TimeEntry.objects.create(
            project=project2,
            user=user1,
            date=date.today(),
            hours=Decimal("3.00"),
            description="Project 2 work",
            is_billable=True,
            hourly_rate=Decimal("100.00"),
            billed_amount=Decimal("300.00"),
        )

        start_date = date.today()
        end_date = date.today()

        metrics = Project.calculate_user_utilization(firm, user1, start_date, end_date)

        assert metrics["total_hours"] == Decimal("8.00")
        assert metrics["projects_worked"] == 2

    def test_utilization_no_budget_or_rate(self, firm, client, user1):
        """Test utilization calculation when project has no budget or rate."""
        project_no_budget = Project.objects.create(
            firm=firm,
            client=client,
            project_code="PROJ-003",
            name="No Budget Project",
            status="in_progress",
            billing_type="fixed_price",
            budget=None,  # No budget
            hourly_rate=None,  # No hourly rate
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30),
        )

        TimeEntry.objects.create(
            project=project_no_budget,
            user=user1,
            date=date.today(),
            hours=Decimal("10.00"),
            description="Work",
            is_billable=True,
            hourly_rate=Decimal("0.00"),
            billed_amount=Decimal("0.00"),
        )

        metrics = project_no_budget.calculate_utilization_metrics()

        assert metrics["total_hours"] == Decimal("10.00")
        assert metrics["budgeted_hours"] is None
        assert metrics["hours_variance"] is None
