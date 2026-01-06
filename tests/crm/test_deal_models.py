import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.crm.models import Deal, Pipeline, PipelineStage
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Deal Firm", slug="deal-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="deal-owner", email="owner@example.com", password="pass1234")


@pytest.fixture
def pipeline(db, firm, user):
    return Pipeline.objects.create(firm=firm, name="Sales", is_default=True, created_by=user)


@pytest.fixture
def open_stage(db, pipeline):
    return PipelineStage.objects.create(pipeline=pipeline, name="Discovery", probability=25, display_order=1)


@pytest.fixture
def closed_won_stage(db, pipeline):
    return PipelineStage.objects.create(
        pipeline=pipeline,
        name="Closed Won",
        probability=100,
        is_closed_won=True,
        display_order=2,
    )


@pytest.mark.django_db
def test_deal_save_updates_weighted_value_and_won_state(firm, pipeline, closed_won_stage, user):
    deal = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=closed_won_stage,
        name="Won Deal",
        value=Decimal("1000.00"),
        probability=60,
        expected_close_date=date.today(),
        owner=user,
        created_by=user,
    )

    assert deal.weighted_value == Decimal("600.00")
    assert deal.is_won is True
    assert deal.is_active is False
    assert deal.actual_close_date is not None


@pytest.mark.django_db
def test_deal_save_marks_stale_when_last_activity_exceeds_threshold(firm, pipeline, open_stage, user):
    last_activity = timezone.now().date() - timedelta(days=45)

    deal = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=open_stage,
        name="Stale Deal",
        value=Decimal("500.00"),
        probability=40,
        expected_close_date=date.today(),
        owner=user,
        created_by=user,
        last_activity_date=last_activity,
        stale_days_threshold=30,
    )

    assert deal.is_stale is True


@pytest.mark.django_db
def test_update_last_activity_resets_stale_flag(firm, pipeline, open_stage, user):
    last_activity = timezone.now().date() - timedelta(days=60)

    deal = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=open_stage,
        name="Reactivated Deal",
        value=Decimal("750.00"),
        probability=50,
        expected_close_date=date.today(),
        owner=user,
        created_by=user,
        last_activity_date=last_activity,
        stale_days_threshold=30,
    )

    assert deal.is_stale is True

    deal.update_last_activity()
    deal.refresh_from_db()

    assert deal.is_stale is False
    assert deal.last_activity_date > last_activity
