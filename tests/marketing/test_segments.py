import pytest
from datetime import date

from django.contrib.auth import get_user_model

from modules.clients.models import Client
from modules.crm.models import Lead, Prospect
from modules.firm.models import Firm
from modules.marketing.models import EntityTag, Segment, Tag


@pytest.mark.django_db
def test_refresh_membership_applies_filters_and_tags():
    user = get_user_model().objects.create_user(username="owner", password="pass1234")
    firm = Firm.objects.create(name="Segment Firm", slug="segment-firm", created_by=user)

    tag = Tag.objects.create(firm=firm, name="High Intent", slug="high-intent", created_by=user)

    lead_included = Lead.objects.create(
        firm=firm,
        company_name="Qualified Lead",
        contact_name="Lead One",
        contact_email="lead1@example.com",
        status="qualified",
        lead_score=80,
    )
    Lead.objects.create(
        firm=firm,
        company_name="New Lead",
        contact_name="Lead Two",
        contact_email="lead2@example.com",
        status="new",
        lead_score=10,
    )
    EntityTag.objects.create(tag=tag, entity_type="lead", entity_id=lead_included.id)

    prospect = Prospect.objects.create(
        firm=firm,
        company_name="Proposal Prospect",
        primary_contact_name="Prospect One",
        primary_contact_email="prospect1@example.com",
        stage="proposal",
        estimated_value=100000,
        close_date_estimate=date.today(),
        assigned_to=user,
    )
    EntityTag.objects.create(tag=tag, entity_type="prospect", entity_id=prospect.id)

    segment = Segment.objects.create(
        firm=firm,
        name="Qualified & Tagged",
        criteria={
            "entity_types": ["lead", "prospect"],
            "lead_status": ["qualified"],
            "lead_score": {"min": 50},
            "prospect_stages": ["proposal"],
            "tags": [tag.slug],
        },
        created_by=user,
    )

    segment.refresh_membership()

    assert segment.member_count == 2
    assert segment.last_refreshed_at is not None


@pytest.mark.django_db
def test_refresh_membership_respects_entity_types_and_tenancy():
    user = get_user_model().objects.create_user(username="owner2", password="pass1234")
    firm = Firm.objects.create(name="Primary Firm", slug="primary-firm", created_by=user)
    other_firm = Firm.objects.create(name="Other Firm", slug="other-firm")

    tag = Tag.objects.create(firm=firm, name="Active", slug="active", created_by=user)
    other_tag = Tag.objects.create(firm=other_firm, name="Active", slug="active")

    lead = Lead.objects.create(
        firm=firm,
        company_name="Tagged Lead",
        contact_name="Lead Three",
        contact_email="lead3@example.com",
        status="qualified",
        lead_score=70,
    )
    EntityTag.objects.create(tag=tag, entity_type="lead", entity_id=lead.id)

    Prospect.objects.create(
        firm=firm,
        company_name="Negotiation Prospect",
        primary_contact_name="Prospect Two",
        primary_contact_email="prospect2@example.com",
        stage="negotiation",
        estimated_value=50000,
        close_date_estimate=date.today(),
    )

    Client.objects.create(
        firm=firm,
        company_name="Client Co",
        primary_contact_name="Client Owner",
        primary_contact_email="client@example.com",
        client_since=date.today(),
        status="active",
        account_manager=user,
    )

    other_lead = Lead.objects.create(
        firm=other_firm,
        company_name="Other Lead",
        contact_name="Outside Tenant",
        contact_email="other@example.com",
        status="qualified",
        lead_score=90,
    )
    EntityTag.objects.create(tag=other_tag, entity_type="lead", entity_id=other_lead.id)

    segment = Segment.objects.create(
        firm=firm,
        name="Leads Only",
        criteria={"entity_types": ["lead"], "tags": [tag.slug]},
        created_by=user,
    )

    segment.refresh_membership()

    assert segment.member_count == 1
    assert segment.last_refreshed_at is not None
