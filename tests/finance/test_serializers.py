import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from api.finance.serializers import BillSerializer, InvoiceSerializer
from modules.clients.models import Client
from modules.finance.models import Bill, Invoice
from modules.firm.models import Firm
from modules.projects.models import Project


@pytest.fixture
def user(db):
    """Create test user."""
    User = get_user_model()
    return User.objects.create_user(username='testuser', password='testpass123')


@pytest.fixture
def firm(db):
    """Create test firm."""
    return Firm.objects.create(name='Finance Firm', slug='finance-firm')


@pytest.fixture
def client_obj(db, user, firm):
    """Create test client."""
    return Client.objects.create(
        company_name='Test Company',
        primary_contact_name='John Doe',
        primary_contact_email='john@test.com',
        firm=firm,
        client_since=date.today(),
        account_manager=user,
        status='active'
    )


@pytest.fixture
def project(db, client_obj, user, firm):
    """Create test project."""
    return Project.objects.create(
        firm=firm,
        client=client_obj,
        project_manager=user,
        project_code='PRJ-001',
        name='Test Project',
        status='in_progress',
        billing_type='time_and_materials',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90)
    )


@pytest.mark.unit
@pytest.mark.django_db
class TestInvoiceSerializer:
    """Test InvoiceSerializer validation logic."""

    def test_valid_invoice_data(self, client_obj, user):
        """Test serializer accepts valid invoice data."""
        data = {
            'firm': client_obj.firm_id,
            'client': client_obj.id,
            'created_by': user.id,
            'invoice_number': 'INV-001',
            'status': 'draft',
            'subtotal': '1000.00',
            'tax_amount': '100.00',
            'total_amount': '1100.00',
            'issue_date': date.today().isoformat(),
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'line_items': [
                {'description': 'Consulting', 'quantity': 10, 'rate': 100, 'amount': 1000}
            ]
        }
        serializer = InvoiceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_subtotal_validation_positive(self):
        """Test subtotal must be positive."""
        serializer = InvoiceSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_subtotal(Decimal('-100.00'))
        assert 'greater than 0' in str(exc_info.value)

    def test_total_amount_validation_positive(self):
        """Test total amount must be positive."""
        serializer = InvoiceSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_total_amount(Decimal('0.00'))
        assert 'greater than 0' in str(exc_info.value)

    def test_due_date_validation(self, client_obj, user):
        """Test due date must be after issue date."""
        data = {
            'firm': client_obj.firm_id,
            'client': client_obj.id,
            'created_by': user.id,
            'invoice_number': 'INV-001',
            'subtotal': '1000.00',
            'total_amount': '1000.00',
            'issue_date': date.today().isoformat(),
            'due_date': (date.today() - timedelta(days=1)).isoformat(),
        }
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()
        assert 'due_date' in serializer.errors

    def test_amount_paid_validation(self):
        """Test amount paid cannot be negative."""
        serializer = InvoiceSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_amount_paid(Decimal('-50.00'))
        assert 'negative' in str(exc_info.value).lower()

    def test_amount_paid_exceeds_total(self, client_obj, user):
        """Test amount paid cannot exceed total amount."""
        invoice = Invoice.objects.create(
            firm=client_obj.firm,
            client=client_obj,
            created_by=user,
            invoice_number='INV-001',
            subtotal=Decimal('1000.00'),
            total_amount=Decimal('1000.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30)
        )
        data = {'amount_paid': '1500.00'}
        serializer = InvoiceSerializer(invoice, data=data, partial=True)
        assert not serializer.is_valid()
        assert 'amount_paid' in serializer.errors

    def test_line_items_validation(self, client_obj, user):
        """Test line items must be a list."""
        data = {
            'firm': client_obj.firm_id,
            'client': client_obj.id,
            'created_by': user.id,
            'invoice_number': 'INV-001',
            'subtotal': '1000.00',
            'total_amount': '1000.00',
            'issue_date': date.today().isoformat(),
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'line_items': 'not a list'
        }
        serializer = InvoiceSerializer(data=data)
        assert not serializer.is_valid()


@pytest.mark.unit
@pytest.mark.django_db
class TestBillSerializer:
    """Test BillSerializer validation logic."""

    def test_valid_bill_data(self, firm):
        """Test serializer accepts valid bill data."""
        data = {
            'firm': firm.id,
            'vendor_name': 'Test Vendor',
            'bill_number': 'BILL-001',
            'reference_number': 'REF-001',
            'status': 'received',
            'subtotal': '500.00',
            'tax_amount': '50.00',
            'total_amount': '550.00',
            'bill_date': date.today().isoformat(),
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
            'expense_category': 'Software'
        }
        serializer = BillSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_total_amount_positive(self):
        """Test total amount must be positive."""
        serializer = BillSerializer()
        with pytest.raises(ValidationError) as exc_info:
            serializer.validate_total_amount(Decimal('-100.00'))
        assert 'greater than 0' in str(exc_info.value)

    def test_due_date_after_bill_date(self, firm):
        """Test due date must be after bill date."""
        data = {
            'firm': firm.id,
            'vendor_name': 'Test Vendor',
            'bill_number': 'BILL-001',
            'reference_number': 'REF-002',
            'subtotal': '500.00',
            'total_amount': '500.00',
            'bill_date': date.today().isoformat(),
            'due_date': (date.today() - timedelta(days=1)).isoformat(),
            'expense_category': 'Software'
        }
        serializer = BillSerializer(data=data)
        assert not serializer.is_valid()
        assert 'due_date' in serializer.errors


@pytest.mark.integration
@pytest.mark.django_db
class TestInvoiceWorkflow:
    """Test complete invoice workflow integration."""

    def test_invoice_payment_workflow(self, client_obj, user):
        """Test invoice payment tracking."""
        invoice = Invoice.objects.create(
            firm=client_obj.firm,
            client=client_obj,
            created_by=user,
            invoice_number='INV-WORKFLOW',
            subtotal=Decimal('1000.00'),
            total_amount=Decimal('1000.00'),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='sent'
        )

        # Make partial payment
        data = {
            'amount_paid': '500.00',
            'status': 'partial'
        }
        serializer = InvoiceSerializer(invoice, data=data, partial=True)
        assert serializer.is_valid()
        updated_invoice = serializer.save()
        assert updated_invoice.status == 'partial'
        assert updated_invoice.amount_paid == Decimal('500.00')

        # Complete payment
        data = {
            'amount_paid': '1000.00',
            'status': 'paid',
            'paid_date': date.today().isoformat()
        }
        serializer = InvoiceSerializer(updated_invoice, data=data, partial=True)
        assert serializer.is_valid()
        paid_invoice = serializer.save()
        assert paid_invoice.status == 'paid'
        assert paid_invoice.amount_paid == Decimal('1000.00')
