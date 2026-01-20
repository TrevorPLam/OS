import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.clients.models import Client, Organization
from modules.firm.models import Firm
from modules.support.models import SLAPolicy, Survey, SurveyResponse, Ticket, TicketComment

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
def sla_policy(db, firm, user):
    return SLAPolicy.objects.create(
        firm=firm,
        name="Standard SLA",
        priority="normal",
        first_response_minutes=60,
        resolution_minutes=240,
        created_by=user,
    )


@pytest.mark.django_db
class TestSLAPolicy:
    """Test SLA policy deadlines."""

    def test_deadline_calculations(self, sla_policy):
        """SLA deadlines should match configured minutes."""
        created_at = timezone.now()

        assert sla_policy.get_first_response_deadline(created_at) == created_at + timedelta(minutes=60)
        assert sla_policy.get_resolution_deadline(created_at) == created_at + timedelta(minutes=240)


@pytest.mark.django_db
class TestTicket:
    """Test ticket lifecycle and SLA behavior."""

    def test_ticket_number_and_sla_assignment(self, firm, client, sla_policy):
        """Ticket number should auto-generate and SLA should assign."""
        ticket = Ticket.objects.create(
            firm=firm,
            client=client,
            contact_email="alex@acme.test",
            contact_name="Alex Smith",
            subject="Help needed",
            description="Issue details",
            priority="normal",
        )

        assert ticket.ticket_number
        assert ticket.sla_policy == sla_policy

    def test_mark_first_response(self, firm, client):
        """First response should update status and timestamp."""
        ticket = Ticket.objects.create(
            firm=firm,
            client=client,
            contact_email="alex@acme.test",
            contact_name="Alex Smith",
            subject="Question",
            description="Details",
        )

        ticket.mark_first_response()
        ticket.refresh_from_db()

        assert ticket.first_response_at is not None
        assert ticket.status == "open"

    def test_sla_breach_detection(self, firm, client, sla_policy):
        """SLA breach flags should set when overdue."""
        ticket = Ticket.objects.create(
            firm=firm,
            client=client,
            contact_email="alex@acme.test",
            contact_name="Alex Smith",
            subject="Critical",
            description="Details",
            priority="normal",
        )

        past_time = timezone.now() - timedelta(minutes=300)
        Ticket.objects.filter(pk=ticket.pk).update(created_at=past_time)
        ticket.refresh_from_db()

        ticket.check_sla_breach()
        ticket.refresh_from_db()

        assert ticket.first_response_sla_breached is True
        assert ticket.resolution_sla_breached is True


@pytest.mark.django_db
class TestTicketComment:
    """Test ticket comment effects."""

    def test_comment_marks_first_response(self, firm, client, user):
        """Staff comments should trigger first response timestamp."""
        ticket = Ticket.objects.create(
            firm=firm,
            client=client,
            contact_email="alex@acme.test",
            contact_name="Alex Smith",
            subject="Comment",
            description="Details",
        )

        TicketComment.objects.create(
            ticket=ticket,
            body="We are looking into this",
            created_by=user,
            is_internal=False,
            is_customer_reply=False,
        )

        ticket.refresh_from_db()
        assert ticket.first_response_at is not None


@pytest.mark.django_db
class TestSurveyResponse:
    """Test survey response scoring."""

    def test_nps_category_assignment(self, firm, client, user):
        """NPS category should map to score."""
        survey = Survey.objects.create(
            firm=firm,
            name="NPS Survey",
            survey_type="nps",
            status="active",
            created_by=user,
        )

        response = SurveyResponse.objects.create(
            survey=survey,
            client=client,
            contact_email="alex@acme.test",
            contact_name="Alex Smith",
            nps_score=9,
        )

        response.refresh_from_db()
        assert response.nps_category == "promoter"
