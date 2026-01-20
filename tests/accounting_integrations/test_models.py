import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from modules.accounting_integrations.models import (
    AccountingOAuthConnection,
    CustomerSyncMapping,
    InvoiceSyncMapping,
)
from modules.clients.models import Client, Organization
from modules.finance.models import Invoice
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
def invoice(db, firm, user, client):
    issue_date = date.today()
    return Invoice.objects.create(
        firm=firm,
        client=client,
        invoice_number="INV-1001",
        status="draft",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        amount_paid=Decimal("0.00"),
        currency="USD",
        issue_date=issue_date,
        due_date=issue_date + timedelta(days=30),
        created_by=user,
    )


@pytest.fixture
def connection(db, firm, user):
    return AccountingOAuthConnection.objects.create(
        firm=firm,
        user=user,
        provider="quickbooks",
        access_token="encrypted-token",
        refresh_token="encrypted-refresh",
        token_expires_at=timezone.now() + timedelta(hours=1),
    )


@pytest.mark.django_db
class TestAccountingOAuthConnection:
    """Test AccountingOAuthConnection model behavior."""

    def test_token_expiration_checks(self, firm, user):
        """Expired tokens should be detected."""
        expired_connection = AccountingOAuthConnection.objects.create(
            firm=firm,
            user=user,
            provider="quickbooks",
            token_expires_at=timezone.now() - timedelta(minutes=1),
        )

        assert expired_connection.is_token_expired() is True
        assert expired_connection.needs_refresh() is True

    def test_token_not_expired(self, firm, user):
        """Future token expiry should not be flagged."""
        connection = AccountingOAuthConnection.objects.create(
            firm=firm,
            user=user,
            provider="xero",
            token_expires_at=timezone.now() + timedelta(hours=2),
        )

        assert connection.is_token_expired() is False
        assert connection.needs_refresh() is False

    def test_unique_provider_per_firm(self, firm, user):
        """One connection per firm/provider should be enforced."""
        AccountingOAuthConnection.objects.create(
            firm=firm,
            user=user,
            provider="quickbooks",
        )

        with pytest.raises(IntegrityError):
            AccountingOAuthConnection.objects.create(
                firm=firm,
                user=user,
                provider="quickbooks",
            )


@pytest.mark.django_db
class TestSyncMappings:
    """Test sync mapping models."""

    def test_invoice_sync_mapping(self, firm, connection, invoice):
        """Invoice sync mappings should store external metadata."""
        mapping = InvoiceSyncMapping.objects.create(
            firm=firm,
            connection=connection,
            invoice=invoice,
            external_id="inv_123",
            external_number="QB-001",
        )

        assert mapping.sync_status == "synced"
        assert mapping.external_metadata == {}
        assert "inv_123" in str(mapping)

    def test_customer_sync_mapping(self, firm, connection, client):
        """Customer sync mappings should track external references."""
        mapping = CustomerSyncMapping.objects.create(
            firm=firm,
            connection=connection,
            client=client,
            external_id="cust_456",
            external_name="Acme Co",
        )

        assert mapping.sync_status == "synced"
        assert mapping.external_metadata == {}
        assert "cust_456" in str(mapping)
