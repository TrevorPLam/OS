import pytest

from modules.clients.models import Client, Contact
from modules.clients.segmentation import GeographicSegmenter
from modules.firm.models import Firm


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Geo Firm", slug="geo-firm")


@pytest.fixture
def client(firm):
    return Client.objects.create(
        firm=firm,
        company_name="Geo Client",
        primary_contact_name="Geo Contact",
        primary_contact_email="geo@example.com",
        city="Seattle",
        state="WA",
        postal_code="98101",
        country="USA",
    )


@pytest.mark.django_db
def test_filter_by_country_prefers_contact_fields(firm, client):
    contact_us = Contact.objects.create(
        client=client,
        first_name="A",
        last_name="US",
        email="us@example.com",
        country="USA",
    )
    contact_ca = Contact.objects.create(
        client=client,
        first_name="B",
        last_name="CA",
        email="ca@example.com",
        country="Canada",
    )

    queryset = Contact.objects.filter(client=client)
    filtered = GeographicSegmenter.filter_by_country(queryset, ["USA"])

    assert contact_us in filtered
    assert contact_ca not in filtered


@pytest.mark.django_db
def test_filter_by_radius_uses_lat_lon(firm, client):
    contact_near = Contact.objects.create(
        client=client,
        first_name="Near",
        last_name="Contact",
        email="near@example.com",
        latitude=47.6062,
        longitude=-122.3321,
    )
    contact_far = Contact.objects.create(
        client=client,
        first_name="Far",
        last_name="Contact",
        email="far@example.com",
        latitude=34.0522,
        longitude=-118.2437,
    )

    queryset = Contact.objects.filter(client=client)
    filtered = GeographicSegmenter.filter_by_radius(queryset, 47.6062, -122.3321, 50)

    assert contact_near in filtered
    assert contact_far not in filtered
