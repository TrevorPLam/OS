from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from modules.calendar.models import AppointmentType
from modules.clients.models import Client, ClientPortalUser
from modules.firm.models import Firm, FirmMembership
from modules.firm.utils import firm_db_session
from modules.finance.models import Invoice


User = get_user_model()


@pytest.mark.django_db
def test_payment_intent_rejects_cross_firm_invoice():
    api_client = APIClient()

    firm_a = Firm.objects.create(name="Firm A", slug="firma", status="active")
    firm_b = Firm.objects.create(name="Firm B", slug="firmb", status="active")

    user_a = User.objects.create_user(username="user-a", email="user-a@example.com", password="pass1234!")
    with firm_db_session(firm_a):
        FirmMembership.objects.create(firm=firm_a, user=user_a, role="admin")

    with firm_db_session(firm_b):
        client_b = Client.objects.create(
            firm=firm_b,
            company_name="Client B",
            primary_contact_name="Contact B",
            primary_contact_email="contactb@example.com",
        )
        invoice_b = Invoice.objects.create(
            firm=firm_b,
            client=client_b,
            invoice_number="INV-B-001",
            status="sent",
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            amount_paid=Decimal("0.00"),
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
        )

    api_client.force_authenticate(user=user_a)
    response = api_client.post(
        "/api/v1/finance/stripe-payment/create_payment_intent/",
        {"invoice_id": invoice_b.id, "customer_email": "payer@example.com"},
        format="json",
        HTTP_HOST=f"{firm_a.slug}.example.com",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_portal_booking_scoped_to_firm():
    api_client = APIClient()

    firm_a = Firm.objects.create(name="Firm A", slug="firma", status="active")
    firm_b = Firm.objects.create(name="Firm B", slug="firmb", status="active")

    portal_user = User.objects.create_user(username="portal-user", email="portal@example.com", password="pass1234!")

    with firm_db_session(firm_a):
        client_a = Client.objects.create(
            firm=firm_a,
            company_name="Client A",
            primary_contact_name="Contact A",
            primary_contact_email="contacta@example.com",
        )
        ClientPortalUser.objects.create(client=client_a, user=portal_user, role="admin")

    with firm_db_session(firm_b):
        appointment_type = AppointmentType.objects.create(
            firm=firm_b,
            name="Consultation",
            duration_minutes=30,
        )

    api_client.force_authenticate(user=portal_user)
    response = api_client.post(
        "/api/v1/portal/appointments/available-slots/",
        {
            "appointment_type_id": appointment_type.pk,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=7)).isoformat(),
        },
        format="json",
        HTTP_HOST=f"{firm_a.slug}.example.com",
    )

    assert response.status_code == 404
