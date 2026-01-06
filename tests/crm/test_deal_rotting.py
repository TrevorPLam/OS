import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from modules.crm.deal_rotting_alerts import check_and_mark_stale_deals, get_stale_deal_report
from modules.crm.models import Deal, Pipeline, PipelineStage
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Rotting Firm", slug="rotting-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="rotting-user", email="rotting@example.com", password="pass1234")


@pytest.fixture
def pipeline(db, firm, user):
    return Pipeline.objects.create(firm=firm, name="Rotting Pipeline", is_default=True, created_by=user)


@pytest.fixture
def stage(db, pipeline):
    return PipelineStage.objects.create(pipeline=pipeline, name="Rotting Stage", probability=15, display_order=1)


@pytest.mark.django_db
def test_check_and_mark_stale_deals_marks_inactive(firm, pipeline, stage, user):
    stale_activity = timezone.now().date() - timedelta(days=45)
    Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Aging Deal",
        value=Decimal("1000.00"),
        probability=15,
        expected_close_date=date.today(),
        last_activity_date=stale_activity,
        stale_days_threshold=30,
        created_by=user,
    )

    marked = check_and_mark_stale_deals()
    deal = Deal.objects.get(name="Aging Deal")

    assert marked == 1
    assert deal.is_stale is True


@pytest.mark.django_db
def test_get_stale_deal_report_returns_expected_fields(firm, pipeline, stage, user):
    stale_activity = timezone.now().date() - timedelta(days=50)
    Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Report Deal",
        value=Decimal("2500.00"),
        probability=25,
        expected_close_date=date.today(),
        last_activity_date=stale_activity,
        stale_days_threshold=30,
        is_stale=True,
        created_by=user,
    )

    report = get_stale_deal_report(firm_id=firm.id)

    assert report["total_stale_deals"] == 1
    assert report["total_value_at_risk"] == 2500.0
    assert report["age_distribution"]["30-60 days"] >= 1
    assert any(owner["deal_count"] == 1 for owner in report["by_owner"])
