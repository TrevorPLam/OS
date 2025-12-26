import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from modules.clients.models import Client, ClientEngagement, ClientPortalUser
from modules.clients.views import ClientInvoiceViewSet
from modules.finance.billing import (
    create_package_invoice,
    execute_autopay_for_invoice,
    generate_package_invoices,
    handle_dispute_closed,
    handle_dispute_opened,
    handle_payment_failure,
    should_generate_package_invoice,
)
from modules.finance.models import Invoice
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


@pytest.mark.django_db
def test_create_package_invoice_enforces_firm_and_line_items(engagement):
    invoice = create_package_invoice(engagement)

    assert invoice.firm == engagement.client.firm
    assert invoice.client == engagement.client
    assert any(item.get('type') == 'package_fee' for item in invoice.line_items)


@pytest.mark.django_db
def test_generate_package_invoices_scopes_by_firm(engagement, user):
    other_firm = Firm.objects.create(name='Other Billing Firm', slug='other-firm')
    other_client = Client.objects.create(
        company_name='Other Corp',
        primary_contact_name='Sam Example',
        primary_contact_email='sam@example.com',
        firm=other_firm,
        client_since=engagement.start_date,
        account_manager=user,
        status='active',
    )
    other_contract = Contract.objects.create(
        firm=other_firm,
        client=other_client,
        contract_number='C-002',
        title='Other Package',
        description='Quarterly package',
        status='active',
        total_value=Decimal('9000.00'),
        start_date=engagement.start_date,
        end_date=engagement.start_date + timedelta(days=180),
        payment_terms='net_30',
        signed_by=user,
    )
    ClientEngagement.objects.create(
        firm=other_firm,
        client=other_client,
        contract=other_contract,
        pricing_mode='package',
        package_fee=Decimal('750.00'),
        package_fee_schedule='Monthly',
        allow_hourly_billing=False,
        hourly_rate_default=Decimal('0.00'),
        start_date=engagement.start_date,
        end_date=other_contract.end_date,
        contracted_value=Decimal('9000.00'),
    )

    created = generate_package_invoices(
        reference_date=engagement.start_date, firm=engagement.firm
    )

    assert len(created) == 1
    assert created[0].firm == engagement.firm
    assert not Invoice.objects.filter(firm=other_firm).exists()


@pytest.mark.django_db
def test_portal_invoice_visibility_respects_permissions(firm, user):
    portal_user = get_user_model().objects.create_user(
        username='portal-user', password='pass1234'
    )
    client = Client.objects.create(
        company_name='Portal Corp',
        primary_contact_name='Paula Portal',
        primary_contact_email='paula@example.com',
        firm=firm,
        client_since=date.today(),
        account_manager=user,
        status='active',
    )
    ClientPortalUser.objects.create(
        client=client, user=portal_user, can_view_billing=True
    )
    other_client = Client.objects.create(
        company_name='Hidden Corp',
        primary_contact_name='Hank Hidden',
        primary_contact_email='hidden@example.com',
        firm=firm,
        client_since=date.today(),
        account_manager=user,
        status='active',
    )

    visible_invoice = Invoice.objects.create(
        firm=firm,
        client=client,
        invoice_number='INV-P-1',
        status='sent',
        subtotal=Decimal('500.00'),
        total_amount=Decimal('500.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[{'type': 'package_fee', 'amount': '500.00'}],
    )
    Invoice.objects.create(
        firm=firm,
        client=other_client,
        invoice_number='INV-P-2',
        status='sent',
        subtotal=Decimal('400.00'),
        total_amount=Decimal('400.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[{'type': 'package_fee', 'amount': '400.00'}],
    )

    request = APIRequestFactory().get('/')
    request.user = portal_user
    request.firm = firm

    view = ClientInvoiceViewSet()
    view.request = request

    queryset = view.get_queryset()

    assert list(queryset) == [visible_invoice]

    # Now revoke billing visibility and ensure access is blocked
    portal_link = ClientPortalUser.objects.get(client=client, user=portal_user)
    portal_link.can_view_billing = False
    portal_link.save()

    with pytest.raises(PermissionDenied):
        view.get_queryset()
