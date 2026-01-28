"""
Tests for Contact lifecycle states and transitions.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.clients.models import Client, Contact, Organization
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    """Create a test firm."""
    return Firm.objects.create(
        name="Test Firm",
        subdomain="testfirm",
        plan="professional",
    )


@pytest.fixture
def firm_user(db, firm):
    """Create a test user belonging to the firm."""
    user = User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
    )
    user.firm = firm
    user.save()
    return user


@pytest.fixture
def client(db, firm):
    """Create a test client."""
    return Client.objects.create(
        firm=firm,
        company_name="Test Company",
        primary_contact_name="John Doe",
        primary_contact_email="john@testcompany.com",
        status="active",
        client_since=timezone.now().date(),
    )


@pytest.fixture
def contact(db, client, firm_user):
    """Create a test contact."""
    return Contact.objects.create(
        client=client,
        first_name="Jane",
        last_name="Smith",
        email="jane@testcompany.com",
        phone="555-0100",
        job_title="Manager",
        created_by=firm_user,
    )


class TestContactLifecycle:
    """Test Contact lifecycle state management."""

    def test_contact_default_status_is_active(self, contact):
        """Test that new contacts default to active status."""
        assert contact.status == Contact.STATUS_ACTIVE
        assert contact.is_active is True

    def test_contact_status_choices(self):
        """Test that all expected status choices are defined."""
        expected_statuses = {
            Contact.STATUS_ACTIVE,
            Contact.STATUS_UNSUBSCRIBED,
            Contact.STATUS_BOUNCED,
            Contact.STATUS_UNCONFIRMED,
            Contact.STATUS_INACTIVE,
        }
        actual_statuses = {choice[0] for choice in Contact.STATUS_CHOICES}
        assert expected_statuses == actual_statuses

    def test_change_status_updates_fields(self, contact, firm_user):
        """Test that change_status properly updates all tracking fields."""
        initial_time = timezone.now()
        
        result = contact.change_status(
            Contact.STATUS_UNSUBSCRIBED,
            reason="User requested unsubscribe",
            changed_by=firm_user,
        )
        
        assert result is True
        assert contact.status == Contact.STATUS_UNSUBSCRIBED
        assert contact.status_reason == "User requested unsubscribe"
        assert contact.status_changed_by == firm_user
        assert contact.status_changed_at is not None
        assert contact.status_changed_at >= initial_time
        assert contact.is_active is False  # Backwards compatibility

    def test_change_status_returns_false_for_same_status(self, contact):
        """Test that changing to the same status returns False."""
        result = contact.change_status(Contact.STATUS_ACTIVE)
        assert result is False
        assert contact.status_changed_at is None  # No change recorded

    def test_change_status_raises_error_for_invalid_status(self, contact):
        """Test that invalid status raises ValueError."""
        with pytest.raises(ValueError, match="Invalid status"):
            contact.change_status("invalid_status")

    def test_mark_as_unsubscribed(self, contact, firm_user):
        """Test mark_as_unsubscribed method."""
        contact.mark_as_unsubscribed(
            reason="Clicked unsubscribe link",
            changed_by=firm_user,
        )
        contact.save()
        
        contact.refresh_from_db()
        assert contact.status == Contact.STATUS_UNSUBSCRIBED
        assert contact.opt_out_marketing is True
        assert contact.is_active is False

    def test_mark_as_bounced(self, contact, firm_user):
        """Test mark_as_bounced method."""
        contact.mark_as_bounced(
            reason="Hard bounce: mailbox does not exist",
            changed_by=firm_user,
        )
        contact.save()
        
        contact.refresh_from_db()
        assert contact.status == Contact.STATUS_BOUNCED
        assert "mailbox does not exist" in contact.status_reason

    def test_mark_as_inactive(self, contact, firm_user):
        """Test mark_as_inactive method."""
        contact.mark_as_inactive(
            reason="No engagement in 2 years",
            changed_by=firm_user,
        )
        contact.save()
        
        contact.refresh_from_db()
        assert contact.status == Contact.STATUS_INACTIVE
        assert contact.is_active is False

    def test_reactivate_inactive_contact(self, contact, firm_user):
        """Test reactivating an inactive contact."""
        contact.mark_as_inactive(changed_by=firm_user)
        contact.save()
        
        contact.reactivate(reason="Re-engaged with firm", changed_by=firm_user)
        contact.save()
        
        contact.refresh_from_db()
        assert contact.status == Contact.STATUS_ACTIVE
        assert contact.is_active is True

    def test_reactivate_bounced_contact(self, contact, firm_user):
        """Test reactivating a bounced contact."""
        contact.mark_as_bounced(reason="Email issue", changed_by=firm_user)
        contact.save()
        
        contact.reactivate(reason="Email fixed", changed_by=firm_user)
        contact.save()
        
        contact.refresh_from_db()
        assert contact.status == Contact.STATUS_ACTIVE

    def test_confirm_email_for_unconfirmed_contact(self, contact, firm_user):
        """Test confirming email for unconfirmed contact."""
        contact.status = Contact.STATUS_UNCONFIRMED
        contact.save()
        
        contact.confirm_email(changed_by=firm_user)
        contact.save()
        
        contact.refresh_from_db()
        assert contact.status == Contact.STATUS_ACTIVE
        assert "Email confirmed" in contact.status_reason


class TestContactManager:
    """Test ContactManager custom queryset methods."""

    def test_active_filter(self, client, firm_user):
        """Test active() manager method."""
        contact1 = Contact.objects.create(
            client=client,
            first_name="Active",
            last_name="User",
            email="active@test.com",
            status=Contact.STATUS_ACTIVE,
            created_by=firm_user,
        )
        contact2 = Contact.objects.create(
            client=client,
            first_name="Inactive",
            last_name="User",
            email="inactive@test.com",
            status=Contact.STATUS_INACTIVE,
            created_by=firm_user,
        )
        
        active_contacts = Contact.objects.active()
        assert contact1 in active_contacts
        assert contact2 not in active_contacts

    def test_unsubscribed_filter(self, client, firm_user):
        """Test unsubscribed() manager method."""
        contact1 = Contact.objects.create(
            client=client,
            first_name="Active",
            last_name="User",
            email="active@test.com",
            status=Contact.STATUS_ACTIVE,
            created_by=firm_user,
        )
        contact2 = Contact.objects.create(
            client=client,
            first_name="Unsubscribed",
            last_name="User",
            email="unsub@test.com",
            status=Contact.STATUS_UNSUBSCRIBED,
            created_by=firm_user,
        )
        
        unsubscribed_contacts = Contact.objects.unsubscribed()
        assert contact1 not in unsubscribed_contacts
        assert contact2 in unsubscribed_contacts

    def test_bounced_filter(self, client, firm_user):
        """Test bounced() manager method."""
        contact1 = Contact.objects.create(
            client=client,
            first_name="Good",
            last_name="Email",
            email="good@test.com",
            status=Contact.STATUS_ACTIVE,
            created_by=firm_user,
        )
        contact2 = Contact.objects.create(
            client=client,
            first_name="Bounced",
            last_name="Email",
            email="bounced@test.com",
            status=Contact.STATUS_BOUNCED,
            created_by=firm_user,
        )
        
        bounced_contacts = Contact.objects.bounced()
        assert contact1 not in bounced_contacts
        assert contact2 in bounced_contacts

    def test_can_receive_emails_filter(self, client, firm_user):
        """Test can_receive_emails() manager method."""
        active_contact = Contact.objects.create(
            client=client,
            first_name="Active",
            last_name="User",
            email="active@test.com",
            status=Contact.STATUS_ACTIVE,
            created_by=firm_user,
        )
        unconfirmed_contact = Contact.objects.create(
            client=client,
            first_name="Unconfirmed",
            last_name="User",
            email="unconfirmed@test.com",
            status=Contact.STATUS_UNCONFIRMED,
            created_by=firm_user,
        )
        bounced_contact = Contact.objects.create(
            client=client,
            first_name="Bounced",
            last_name="User",
            email="bounced@test.com",
            status=Contact.STATUS_BOUNCED,
            created_by=firm_user,
        )
        
        can_receive = Contact.objects.can_receive_emails()
        assert active_contact in can_receive
        assert unconfirmed_contact in can_receive
        assert bounced_contact not in can_receive

    def test_can_receive_marketing_filter(self, client, firm_user):
        """Test can_receive_marketing() manager method."""
        marketing_contact = Contact.objects.create(
            client=client,
            first_name="Marketing",
            last_name="User",
            email="marketing@test.com",
            status=Contact.STATUS_ACTIVE,
            opt_out_marketing=False,
            created_by=firm_user,
        )
        opted_out_contact = Contact.objects.create(
            client=client,
            first_name="Opted",
            last_name="Out",
            email="optedout@test.com",
            status=Contact.STATUS_ACTIVE,
            opt_out_marketing=True,
            created_by=firm_user,
        )
        
        can_market_to = Contact.objects.can_receive_marketing()
        assert marketing_contact in can_market_to
        assert opted_out_contact not in can_market_to
