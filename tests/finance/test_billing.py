import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model

from modules.clients.models import Client, ClientEngagement
from modules.finance.billing import (
    create_package_invoice,
    execute_autopay_for_invoice,
    generate_package_invoices,
    handle_dispute_closed,
    handle_dispute_opened,
    handle_payment_failure,
    should_generate_package_invoice,
)
from modules.finance.models import Chargeback, Invoice, LedgerEntry, PaymentFailure
from modules.crm.models import Contract
from modules.firm.models import Firm


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='billing-user', password='pass1234')


@pytest.fixture
def firm(db):
    return Firm.objects.create(name='Billing Firm', slug='billing-firm')


@pytest.fixture
def client(firm, user):
    return Client.objects.create(
        company_name='ACME Corp',
        primary_contact_name='Jane Roe',
        primary_contact_email='jane@example.com',
        firm=firm,
        client_since=date.today(),
        account_manager=user,
        status='active',
    )


@pytest.fixture
def contract(firm, client, user):
    return Contract.objects.create(
        firm=firm,
        client=client,
        contract_number='C-001',
        title='Strategy Retainer',
        description='Monthly strategy support',
        status='active',
        total_value=Decimal('12000.00'),
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        payment_terms='net_30',
        signed_by=user,
    )


@pytest.fixture
def engagement(client, contract):
    return ClientEngagement.objects.create(
        firm=client.firm,
        client=client,
        contract=contract,
        pricing_mode='package',
        package_fee=Decimal('1000.00'),
        package_fee_schedule='Monthly',
        allow_hourly_billing=False,
        hourly_rate_default=Decimal('150.00'),
        start_date=date.today().replace(day=1),
        end_date=date.today() + timedelta(days=365),
        contracted_value=Decimal('12000.00'),
    )


@pytest.mark.django_db
def test_package_invoice_generation_and_duplicate_prevention(engagement):
    assert should_generate_package_invoice(engagement)
    invoice = create_package_invoice(engagement)
    assert invoice.is_auto_generated
    assert invoice.period_start == date.today().replace(day=1)

    # Duplicate prevention: second call does not create a new invoice
    invoice_again = create_package_invoice(engagement)
    assert Invoice.objects.count() == 1
    assert invoice_again.id == invoice.id


@pytest.mark.django_db
def test_package_invoices_survive_renewal_without_touching_old_invoice(engagement):
    first_invoice = create_package_invoice(engagement)

    renewal = engagement.renew(
        renewal_start_date=engagement.end_date + timedelta(days=1),
        renewal_end_date=engagement.end_date + timedelta(days=365),
    )

    created = generate_package_invoices(reference_date=renewal.start_date)
    assert len(created) == 1
    renewal_invoice = created[0]

    assert renewal_invoice.engagement == renewal
    assert renewal_invoice.period_start == renewal.start_date.replace(day=1)
    assert first_invoice.engagement == engagement


@pytest.mark.django_db
def test_autopay_execution_pays_invoice_without_duplication(client):
    client.autopay_enabled = True
    client.autopay_payment_method_id = 'pm_123'
    client.save()

    invoice = Invoice.objects.create(
        firm=client.firm,
        client=client,
        invoice_number='INV-AUTO-1',
        status='sent',
        subtotal=Decimal('500.00'),
        total_amount=Decimal('500.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[],
    )

    execute_autopay_for_invoice(invoice)

    assert Invoice.objects.count() == 1
    invoice.refresh_from_db()
    assert invoice.status == 'paid'
    assert invoice.amount_paid == Decimal('500.00')


@pytest.mark.django_db
def test_payment_failure_and_retry_metadata(client):
    invoice = Invoice.objects.create(
        firm=client.firm,
        client=client,
        invoice_number='INV-FAIL-1',
        status='sent',
        subtotal=Decimal('200.00'),
        total_amount=Decimal('200.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[],
    )

    handle_payment_failure(invoice, failure_reason='card_declined', failure_code='card_declined')
    invoice.refresh_from_db()
    assert invoice.status == 'failed'
    assert invoice.payment_retry_count == 1
    assert invoice.payment_failure_reason == 'card_declined'

    failure_record = PaymentFailure.objects.get(invoice=invoice)
    assert failure_record.failure_code == 'card_declined'
    assert failure_record.amount_attempted == Decimal('200.00')

    # Second attempt triggers escalation to inactive client
    handle_payment_failure(invoice, failure_reason='insufficient_funds', failure_code='insufficient_funds')
    invoice.refresh_from_db()
    client.refresh_from_db()
    assert client.status == 'inactive'


@pytest.mark.django_db
def test_dispute_open_and_close_workflow(client):
    invoice = Invoice.objects.create(
        firm=client.firm,
        client=client,
        invoice_number='INV-DISPUTE-1',
        status='paid',
        subtotal=Decimal('300.00'),
        total_amount=Decimal('300.00'),
        amount_paid=Decimal('300.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[],
        stripe_invoice_id='in_123',
    )

    dispute = handle_dispute_opened(
        {
            'id': 'dp_123',
            'invoice_id': 'in_123',
            'charge_id': 'ch_123',
            'reason': 'fraudulent',
            'amount': '300.00',
            'respond_by': None,
        }
    )

    invoice.refresh_from_db()
    assert invoice.status == 'disputed'
    assert dispute.invoice == invoice

    handle_dispute_closed({'id': 'dp_123', 'status': 'lost', 'reason': 'evidence_insufficient'})
    invoice.refresh_from_db()
    assert invoice.status == 'charged_back'
    assert invoice.amount_paid == Decimal('0.00')

    # Ledger reversals and client portal messaging recorded
    ledger_entries = LedgerEntry.objects.filter(invoice=invoice)
    assert ledger_entries.count() == 2
    accounts = set(ledger_entries.values_list('account', flat=True))
    assert accounts == {'cash', 'accounts_receivable'}

    chargeback = Chargeback.objects.get(invoice=invoice)
    assert chargeback.funds_reversed
    assert 'paused' in invoice.notes
