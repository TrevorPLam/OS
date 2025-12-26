import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model

from modules.firm.export import export_firm_data
from modules.firm.models import Firm
from modules.firm.audit import AuditEvent
from modules.clients.models import Client
from modules.projects.models import Project, Task, TimeEntry
from modules.finance.models import Invoice


@pytest.mark.django_db
def test_offboarding_export_isolated_and_complete():
    user = get_user_model().objects.create_user(username='exporter', password='pass1234')
    firm = Firm.objects.create(name='Alpha Firm', slug='alpha-firm')
    other_firm = Firm.objects.create(name='Beta Firm', slug='beta-firm')

    client = Client.objects.create(
        firm=firm,
        company_name='ACME Alpha',
        primary_contact_name='Jane Roe',
        primary_contact_email='jane@example.com',
        client_since=date.today(),
        account_manager=user,
        status='active',
    )
    Client.objects.create(
        firm=other_firm,
        company_name='ACME Beta',
        primary_contact_name='John Doe',
        primary_contact_email='john@example.com',
        client_since=date.today(),
        account_manager=user,
        status='active',
    )

    project = Project.objects.create(
        firm=firm,
        client=client,
        project_code='ALPHA-001',
        name='Alpha Launch',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        status='planning',
    )
    task = Task.objects.create(
        project=project,
        title='Kickoff',
        description='Start project',
        status='todo',
        priority='medium',
    )
    TimeEntry.objects.create(
        project=project,
        task=task,
        user=user,
        date=date.today(),
        hours=Decimal('2.00'),
        description='Initial planning',
        is_billable=True,
        hourly_rate=Decimal('150.00'),
        billed_amount=Decimal('300.00'),
        approved=False,
        invoiced=False,
    )

    Invoice.objects.create(
        firm=firm,
        client=client,
        invoice_number='INV-100',
        status='sent',
        subtotal=Decimal('500.00'),
        total_amount=Decimal('500.00'),
        issue_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        line_items=[],
    )

    AuditEvent.objects.create(
        firm=firm,
        category=AuditEvent.CATEGORY_SYSTEM,
        action='offboarding_export_requested',
        severity=AuditEvent.SEVERITY_INFO,
    )

    payload = export_firm_data(firm=firm, requested_by=user)

    assert payload['integrity']['status'] == 'ok'
    assert payload['manifest']['counts']['clients']['clients'] == 1
    assert payload['manifest']['counts']['projects']['projects'] == 1
    assert payload['manifest']['counts']['projects']['tasks'] == 1
    assert payload['manifest']['counts']['billing']['invoices'] == 1
    assert payload['manifest']['counts']['audit']['events'] == 1

    assert all(record['firm_id'] == firm.id for record in payload['domains']['clients']['clients'])
    assert all(record['firm_id'] == firm.id for record in payload['domains']['projects']['projects'])
    assert all(record['firm_id'] == firm.id for record in payload['domains']['billing']['invoices'])
