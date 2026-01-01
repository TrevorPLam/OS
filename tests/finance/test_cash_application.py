"""
Tests for Cash Application Matching (Medium Feature 2.10).

Tests payment allocation including partial, over, and under payments.
"""

import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from modules.clients.models import Client
from modules.firm.models import Firm
from modules.finance.models import Invoice, Payment, PaymentAllocation

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
def invoice(db, firm, client, user):
    """Create a test invoice."""
    return Invoice.objects.create(
        firm=firm,
        client=client,
        invoice_number="INV-001",
        status="sent",
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1100.00"),
        amount_paid=Decimal("0.00"),
        issue_date=date.today(),
        due_date=date.today(),
        created_by=user,
    )


@pytest.fixture
def payment(db, firm, client, user):
    """Create a test payment."""
    return Payment.objects.create(
        firm=firm,
        client=client,
        payment_number="PAY-001",
        payment_date=date.today(),
        amount=Decimal("1100.00"),
        payment_method="stripe",
        status="cleared",
        created_by=user,
    )


@pytest.mark.django_db
class TestCashApplicationMatching:
    """Test cash application matching for partial/over/under payments (Medium Feature 2.10)."""

    def test_create_payment(self, firm, client, user):
        """Test creating a payment record."""
        payment = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-TEST",
            payment_date=date.today(),
            amount=Decimal("500.00"),
            payment_method="credit_card",
            status="pending",
            created_by=user,
        )

        assert payment.amount == Decimal("500.00")
        assert payment.amount_allocated == Decimal("0.00")
        assert payment.amount_unallocated == Decimal("500.00")
        assert payment.status == "pending"

    def test_exact_payment_allocation(self, invoice, payment, user):
        """Test allocating payment that exactly matches invoice amount."""
        # Payment is $1100, Invoice is $1100
        allocation = PaymentAllocation.objects.create(
            firm=payment.firm,
            payment=payment,
            invoice=invoice,
            amount=Decimal("1100.00"),
            created_by=user,
        )

        # Refresh from DB to get updated values
        payment.refresh_from_db()
        invoice.refresh_from_db()

        assert allocation.amount == Decimal("1100.00")
        assert payment.amount_allocated == Decimal("1100.00")
        assert payment.amount_unallocated == Decimal("0.00")
        assert invoice.amount_paid == Decimal("1100.00")
        assert invoice.status == "paid"
        assert invoice.balance_due == Decimal("0.00")

    def test_partial_payment_allocation(self, invoice, firm, client, user):
        """Test under-payment: payment less than invoice amount."""
        # Payment is only $500, Invoice is $1100
        partial_payment = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-PARTIAL",
            payment_date=date.today(),
            amount=Decimal("500.00"),
            payment_method="check",
            status="cleared",
            created_by=user,
        )

        allocation = PaymentAllocation.objects.create(
            firm=firm,
            payment=partial_payment,
            invoice=invoice,
            amount=Decimal("500.00"),
            created_by=user,
        )

        partial_payment.refresh_from_db()
        invoice.refresh_from_db()

        assert partial_payment.amount_allocated == Decimal("500.00")
        assert partial_payment.amount_unallocated == Decimal("0.00")
        assert invoice.amount_paid == Decimal("500.00")
        assert invoice.status == "partial"  # Invoice partially paid
        assert invoice.balance_due == Decimal("600.00")

    def test_overpayment_allocation(self, invoice, firm, client, user):
        """Test over-payment: payment exceeds invoice amount."""
        # Payment is $1500, Invoice is $1100
        overpayment = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-OVER",
            payment_date=date.today(),
            amount=Decimal("1500.00"),
            payment_method="bank_transfer",
            status="cleared",
            created_by=user,
        )

        # Allocate full invoice amount to this payment
        allocation = PaymentAllocation.objects.create(
            firm=firm,
            payment=overpayment,
            invoice=invoice,
            amount=Decimal("1100.00"),
            created_by=user,
        )

        overpayment.refresh_from_db()
        invoice.refresh_from_db()

        assert overpayment.amount_allocated == Decimal("1100.00")
        assert overpayment.amount_unallocated == Decimal("400.00")  # Credit remaining
        assert invoice.amount_paid == Decimal("1100.00")
        assert invoice.status == "paid"
        assert invoice.balance_due == Decimal("0.00")

    def test_split_payment_to_multiple_invoices(self, firm, client, user):
        """Test allocating one payment to multiple invoices."""
        # Create two invoices
        invoice1 = Invoice.objects.create(
            firm=firm,
            client=client,
            invoice_number="INV-001",
            status="sent",
            subtotal=Decimal("500.00"),
            tax_amount=Decimal("50.00"),
            total_amount=Decimal("550.00"),
            amount_paid=Decimal("0.00"),
            issue_date=date.today(),
            due_date=date.today(),
            created_by=user,
        )
        invoice2 = Invoice.objects.create(
            firm=firm,
            client=client,
            invoice_number="INV-002",
            status="sent",
            subtotal=Decimal("700.00"),
            tax_amount=Decimal("70.00"),
            total_amount=Decimal("770.00"),
            amount_paid=Decimal("0.00"),
            issue_date=date.today(),
            due_date=date.today(),
            created_by=user,
        )

        # Payment that covers both
        payment = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-SPLIT",
            payment_date=date.today(),
            amount=Decimal("1320.00"),  # Covers both invoices
            payment_method="stripe",
            status="cleared",
            created_by=user,
        )

        # Allocate to first invoice
        PaymentAllocation.objects.create(
            firm=firm,
            payment=payment,
            invoice=invoice1,
            amount=Decimal("550.00"),
            created_by=user,
        )

        # Allocate to second invoice
        PaymentAllocation.objects.create(
            firm=firm,
            payment=payment,
            invoice=invoice2,
            amount=Decimal("770.00"),
            created_by=user,
        )

        payment.refresh_from_db()
        invoice1.refresh_from_db()
        invoice2.refresh_from_db()

        assert payment.amount_allocated == Decimal("1320.00")
        assert payment.amount_unallocated == Decimal("0.00")
        assert invoice1.status == "paid"
        assert invoice2.status == "paid"

    def test_multiple_payments_to_one_invoice(self, invoice, firm, client, user):
        """Test applying multiple payments to a single invoice."""
        # First payment: $600
        payment1 = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-001",
            payment_date=date.today(),
            amount=Decimal("600.00"),
            status="cleared",
            created_by=user,
        )
        PaymentAllocation.objects.create(
            firm=firm,
            payment=payment1,
            invoice=invoice,
            amount=Decimal("600.00"),
            created_by=user,
        )

        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("600.00")
        assert invoice.status == "partial"

        # Second payment: $500 (completes the invoice)
        payment2 = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-002",
            payment_date=date.today(),
            amount=Decimal("500.00"),
            status="cleared",
            created_by=user,
        )
        PaymentAllocation.objects.create(
            firm=firm,
            payment=payment2,
            invoice=invoice,
            amount=Decimal("500.00"),
            created_by=user,
        )

        invoice.refresh_from_db()
        assert invoice.amount_paid == Decimal("1100.00")
        assert invoice.status == "paid"

    def test_cannot_allocate_more_than_payment_amount(self, invoice, payment, user):
        """Test that allocation cannot exceed payment unallocated amount."""
        # Try to allocate more than payment amount
        with pytest.raises(ValidationError, match="exceeds unallocated"):
            allocation = PaymentAllocation(
                firm=payment.firm,
                payment=payment,
                invoice=invoice,
                amount=Decimal("1200.00"),  # Payment is only $1100
                created_by=user,
            )
            allocation.full_clean()

    def test_allocation_with_notes(self, invoice, payment, user):
        """Test allocation with descriptive notes."""
        notes = "Partial payment per customer agreement"
        allocation = PaymentAllocation.objects.create(
            firm=payment.firm,
            payment=payment,
            invoice=invoice,
            amount=Decimal("500.00"),
            notes=notes,
            created_by=user,
        )

        assert allocation.notes == notes

    def test_payment_status_cleared_check(self, invoice, firm, client, user):
        """Test that payment status affects allocation workflow."""
        pending_payment = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-PENDING",
            payment_date=date.today(),
            amount=Decimal("1100.00"),
            status="pending",  # Not yet cleared
            created_by=user,
        )

        # Check that payment can't allocate when not cleared
        can_allocate, reason = pending_payment.can_allocate(Decimal("1100.00"))
        assert can_allocate is False
        assert "cleared" in reason.lower()

    def test_payment_can_allocate_checks(self, payment, user):
        """Test payment.can_allocate() validation."""
        # Valid allocation
        can_allocate, reason = payment.can_allocate(Decimal("500.00"))
        assert can_allocate is True
        assert reason == ""

        # Zero or negative amount
        can_allocate, reason = payment.can_allocate(Decimal("0.00"))
        assert can_allocate is False
        assert "positive" in reason.lower()

        # Exceeds unallocated
        can_allocate, reason = payment.can_allocate(Decimal("2000.00"))
        assert can_allocate is False
        assert "exceeds" in reason.lower()

    def test_firm_consistency_validation(self, payment, user, firm):
        """Test that payment and invoice must belong to same firm."""
        # Create a different firm
        other_firm = Firm.objects.create(
            name="Other Firm",
            slug="other-firm",
            subdomain="other",
        )
        other_client = Client.objects.create(
            firm=other_firm,
            company_name="Other Client",
            email="other@example.com",
        )
        other_invoice = Invoice.objects.create(
            firm=other_firm,
            client=other_client,
            invoice_number="INV-OTHER",
            status="sent",
            subtotal=Decimal("1000.00"),
            tax_amount=Decimal("100.00"),
            total_amount=Decimal("1100.00"),
            issue_date=date.today(),
            due_date=date.today(),
            created_by=user,
        )

        # Try to allocate payment from one firm to invoice from another firm
        with pytest.raises(ValidationError, match="same firm"):
            allocation = PaymentAllocation(
                firm=payment.firm,
                payment=payment,
                invoice=other_invoice,  # Different firm!
                amount=Decimal("1100.00"),
                created_by=user,
            )
            allocation.full_clean()

    def test_allocation_sets_invoice_paid_date(self, invoice, payment, user):
        """Test that full payment sets invoice paid date."""
        assert invoice.paid_date is None

        PaymentAllocation.objects.create(
            firm=payment.firm,
            payment=payment,
            invoice=invoice,
            amount=Decimal("1100.00"),
            created_by=user,
        )

        invoice.refresh_from_db()
        assert invoice.paid_date == date.today()
        assert invoice.status == "paid"

    def test_partial_payment_does_not_set_paid_date(self, invoice, firm, client, user):
        """Test that partial payment doesn't set paid date."""
        partial_payment = Payment.objects.create(
            firm=firm,
            client=client,
            payment_number="PAY-PARTIAL",
            payment_date=date.today(),
            amount=Decimal("500.00"),
            status="cleared",
            created_by=user,
        )

        PaymentAllocation.objects.create(
            firm=firm,
            payment=partial_payment,
            invoice=invoice,
            amount=Decimal("500.00"),
            created_by=user,
        )

        invoice.refresh_from_db()
        assert invoice.paid_date is None
        assert invoice.status == "partial"
