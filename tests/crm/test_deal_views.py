import pytest
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.crm.models import Deal, Pipeline, PipelineStage
from modules.crm.views import DealViewSet
from modules.firm.models import Firm, FirmMembership
from tests.utils.query_assertions import assert_max_queries

User = get_user_model()


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="View Firm", slug="view-firm", status="active")


@pytest.fixture
def user(db, firm):
    user = User.objects.create_user(username="view-user", email="user@example.com", password="pass1234")
    FirmMembership.objects.create(firm=firm, user=user, role="firm_admin")
    # Attach firm directly for serializers that expect request.user.firm
    user.firm = firm
    return user


@pytest.fixture
def pipeline(db, firm, user):
    return Pipeline.objects.create(firm=firm, name="View Pipeline", is_default=True, created_by=user)


@pytest.fixture
def stages(db, pipeline):
    initial = PipelineStage.objects.create(pipeline=pipeline, name="Initial", probability=10, display_order=1)
    follow_up = PipelineStage.objects.create(
        pipeline=pipeline, name="Follow Up", probability=40, display_order=2
    )
    return initial, follow_up


@pytest.mark.django_db
@pytest.mark.performance
def test_deal_list_is_firm_scoped(factory, firm, pipeline, stages, user):
    other_firm = Firm.objects.create(name="Other Firm", slug="other-firm", status="active")
    other_user = User.objects.create_user(username="other-user", email="other@example.com", password="pass1234")
    other_pipeline = Pipeline.objects.create(firm=other_firm, name="Other Pipeline", is_default=True)
    other_stage = PipelineStage.objects.create(
        pipeline=other_pipeline, name="Other Initial", probability=20, display_order=1
    )

    Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stages[0],
        name="Firm Deal",
        value=Decimal("100.00"),
        probability=20,
        expected_close_date=date.today(),
        owner=user,
        created_by=user,
    )
    Deal.objects.create(
        firm=other_firm,
        pipeline=other_pipeline,
        stage=other_stage,
        name="Other Firm Deal",
        value="200.00",
        probability=30,
        expected_close_date=date.today(),
        owner=other_user,
        created_by=other_user,
    )

    request = factory.get("/api/v1/crm/deals/")
    request.firm = firm
    force_authenticate(request, user=user)

    # Query budget guard: list endpoint should remain stable as data grows.
    with assert_max_queries(12):
        response = DealViewSet.as_view({"get": "list"})(request)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Firm Deal"


@pytest.mark.django_db
def test_move_stage_updates_deal(factory, firm, pipeline, stages, user):
    initial_stage, follow_up_stage = stages
    deal = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=initial_stage,
        name="Stage Move Deal",
        value="500.00",
        probability=initial_stage.probability,
        expected_close_date=date.today(),
        owner=user,
        created_by=user,
    )

    request = factory.post(
        f"/api/v1/crm/deals/{deal.id}/move-stage/",
        {"stage_id": follow_up_stage.id},
        format="json",
    )
    request.firm = firm
    force_authenticate(request, user=user)

    response = DealViewSet.as_view({"post": "move_stage"})(request, pk=deal.id)
    deal.refresh_from_db()

    assert response.status_code == 200
    assert deal.stage_id == follow_up_stage.id
    assert deal.probability == follow_up_stage.probability
