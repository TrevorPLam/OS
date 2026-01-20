import pytest
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.clients.models import Client, Organization
from modules.firm.models import Firm
from modules.onboarding.models import (
    OnboardingDocument,
    OnboardingProcess,
    OnboardingTask,
    OnboardingTemplate,
)

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.fixture
def organization(db, firm, user):
    return Organization.objects.create(firm=firm, name="Test Org", created_by=user)


@pytest.fixture
def client(db, firm, user, organization):
    return Client.objects.create(
        firm=firm,
        organization=organization,
        company_name="Acme Co",
        primary_contact_name="Alex Smith",
        primary_contact_email="alex@acme.test",
        status="active",
        account_manager=user,
    )


@pytest.fixture
def template(db, firm, user):
    return OnboardingTemplate.objects.create(
        firm=firm,
        name="Standard Onboarding",
        description="Baseline onboarding steps",
        steps=[{"step_name": "Kickoff", "tasks": []}],
        status="active",
        created_by=user,
    )


@pytest.fixture
def process(db, firm, client, template, user):
    return OnboardingProcess.objects.create(
        firm=firm,
        template=template,
        client=client,
        name="Acme Onboarding",
        status="not_started",
        assigned_to=user,
        target_completion_date=date.today() + timedelta(days=30),
    )


@pytest.mark.django_db
class TestOnboardingTemplate:
    """Test onboarding template behavior."""

    def test_mark_used_increments_counter(self, template):
        """Templates should track usage."""
        template.mark_used()
        template.refresh_from_db()

        assert template.times_used == 1


@pytest.mark.django_db
class TestOnboardingProcess:
    """Test onboarding process lifecycle."""

    def test_progress_percentage_calculation(self, firm, client, template):
        """Progress percentage should reflect completed tasks."""
        process = OnboardingProcess.objects.create(
            firm=firm,
            template=template,
            client=client,
            name="Progress Test",
            total_tasks=4,
            completed_tasks=1,
        )

        assert process.progress_percentage == 25

    def test_start_and_complete(self, process):
        """Start and completion should set timestamps and status."""
        process.start()
        process.refresh_from_db()

        assert process.status == "in_progress"
        assert process.started_at is not None

        process.complete()
        process.refresh_from_db()

        assert process.status == "completed"
        assert process.completed_at is not None
        assert process.progress_percentage == 100

    def test_update_progress_counts_tasks(self, process):
        """Task completion should update process counters."""
        OnboardingTask.objects.create(
            process=process,
            name="Collect Info",
            task_type="information",
            status="completed",
            step_number=1,
        )
        OnboardingTask.objects.create(
            process=process,
            name="Upload Doc",
            task_type="document",
            status="pending",
            step_number=2,
        )

        process.update_progress()
        process.refresh_from_db()

        assert process.completed_tasks == 1
        assert process.total_tasks == 2


@pytest.mark.django_db
class TestOnboardingTask:
    """Test onboarding task behavior."""

    def test_complete_updates_process(self, process, user):
        """Completing a task should update process progress."""
        task = OnboardingTask.objects.create(
            process=process,
            name="Collect Info",
            task_type="information",
            status="pending",
            step_number=1,
        )

        task.complete(completed_by=user)
        task.refresh_from_db()
        process.refresh_from_db()

        assert task.status == "completed"
        assert task.completed_at is not None
        assert process.completed_tasks == 1

    def test_send_reminder_skips_unassigned(self, process):
        """Reminders should not send for non-client tasks."""
        task = OnboardingTask.objects.create(
            process=process,
            name="Internal Step",
            task_type="review",
            status="pending",
            step_number=1,
            assigned_to_client=False,
        )

        assert task.send_reminder() is False


@pytest.mark.django_db
class TestOnboardingDocument:
    """Test onboarding document workflow."""

    def test_mark_received_and_review(self, process, user):
        """Documents should update status on receipt and review."""
        document = OnboardingDocument.objects.create(
            process=process,
            document_name="W9",
            status="required",
        )

        document.mark_received(document=None)
        document.refresh_from_db()

        assert document.status == "received"
        assert document.received_at is not None

        document.approve(reviewed_by=user, notes="Looks good")
        document.refresh_from_db()

        assert document.status == "approved"
        assert document.reviewed_by == user

        document.reject(reviewed_by=user, notes="Needs revision")
        document.refresh_from_db()

        assert document.status == "rejected"
        assert document.review_notes == "Needs revision"

    def test_send_reminder_transitions_status(self, process, monkeypatch):
        """Reminders should move required documents to requested."""
        def fake_send(*args, **kwargs):
            return None

        monkeypatch.setattr("modules.onboarding.models.EmailNotification.send", fake_send)

        document = OnboardingDocument.objects.create(
            process=process,
            document_name="Operating Agreement",
            status="required",
        )

        assert document.send_reminder() is True
        document.refresh_from_db()

        assert document.status == "requested"
        assert document.reminder_count == 1
        assert document.requested_at is not None
