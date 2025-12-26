import pytest
from datetime import date, timedelta
from decimal import Decimal

from modules.clients.models import Client
from modules.finance.billing import process_recurring_invoices, schedule_autopay
from modules.finance.models import Invoice
from modules.firm.models import Firm


class _FakePaymentService:
    def __init__(self, fail=False):
        self.fail = fail

    def create_payment_intent(self, amount, currency='usd', customer_id=None, metadata=None, payment_method=None):
        if self.fail:
            raise Exception('card_declined')
        return {'id': 'pi_test_success'}


@pytest.fixture
def firm(db):
    return Firm.objects.create(name='Autopay Firm', slug='auto-firm')


@pytest.fixture
def client(db, firm):
    return Client.objects.create(
        company_name='Recurring Corp',
        primary_contact_name='Jane Smith',
        primary_contact_email='jane@recurring.com',
        firm=firm,
        client_since=date.today(),
        status='active',
        account_manager=None,
        autopay_enabled=True,
        autopay_payment_method_id='pm_test_123',
    )


@pytest.fixture
def invoice(client):
    return Invoice.objects.create(
        firm=client.firm,
        client=client,
        invoice_number='INV-REC-1',
        status='sent',
        subtotal=Decimal('250.00'),
        total_amount=Decimal('250.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=1),
        line_items=[],
        autopay_opt_in=True,
    )


@pytest.mark.django_db
def test_successful_recurring_charge(invoice):
    schedule_autopay(invoice)
    processed = process_recurring_invoices(payment_service=_FakePaymentService())

    invoice.refresh_from_db()
    assert len(processed) == 1
    assert invoice.status == 'paid'
    assert invoice.amount_paid == Decimal('250.00')
    assert invoice.autopay_status == 'succeeded'


@pytest.mark.django_db
def test_retry_on_failure(invoice):
    schedule_autopay(invoice)
    process_recurring_invoices(payment_service=_FakePaymentService(fail=True))

    invoice.refresh_from_db()
    assert invoice.status == 'failed'
    assert invoice.autopay_status == 'failed'
    assert invoice.payment_retry_count == 1
    assert invoice.autopay_next_charge_at is not None


@pytest.mark.django_db
def test_autopay_cancelled_when_client_disabled(invoice, client):
    client.autopay_enabled = False
    client.save()

    schedule_autopay(invoice)
    process_recurring_invoices(payment_service=_FakePaymentService())

    invoice.refresh_from_db()
    assert invoice.autopay_opt_in is False
    assert invoice.autopay_status == 'cancelled'
