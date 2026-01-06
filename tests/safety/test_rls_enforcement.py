import pytest
from django.db import DatabaseError, connection, transaction

from modules.clients.models import Client
from modules.firm.models import Firm
from modules.firm.utils import firm_db_session


pytestmark = [pytest.mark.django_db]


@pytest.mark.skipif(connection.vendor != "postgresql", reason="RLS enforcement requires PostgreSQL")
def test_rls_blocks_cross_firm_selects():
    firm_a = Firm.objects.create(name="Firm A", slug="firma", status="active")
    firm_b = Firm.objects.create(name="Firm B", slug="firmb", status="active")

    with firm_db_session(firm_a):
        Client.objects.create(
            firm=firm_a,
            company_name="Client A",
            primary_contact_name="Contact A",
            primary_contact_email="contacta@example.com",
        )

    with firm_db_session(firm_b):
        Client.objects.create(
            firm=firm_b,
            company_name="Client B",
            primary_contact_name="Contact B",
            primary_contact_email="contactb@example.com",
        )

    with firm_db_session(firm_a):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM clients_client WHERE firm_id = %s", [firm_b.id])
            rows = cursor.fetchall()

    assert rows == []


@pytest.mark.skipif(connection.vendor != "postgresql", reason="RLS enforcement requires PostgreSQL")
def test_rls_blocks_cross_firm_inserts():
    firm_a = Firm.objects.create(name="Firm A", slug="firma", status="active")
    firm_b = Firm.objects.create(name="Firm B", slug="firmb", status="active")

    with firm_db_session(firm_a):
        with pytest.raises(DatabaseError):
            Client.objects.create(
                firm=firm_b,
                company_name="Blocked Client",
                primary_contact_name="Blocked",
                primary_contact_email="blocked@example.com",
            )
        transaction.set_rollback(True)
