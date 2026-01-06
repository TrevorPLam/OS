import pytest
from datetime import date

from django.contrib.auth import get_user_model

from modules.crm.assignment_automation import AssignmentRule, auto_assign_deal
from modules.crm.models import Deal, Pipeline, PipelineStage
from modules.firm.models import Firm, FirmMembership

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Assignment Firm", slug="assignment-firm", status="active")


@pytest.fixture
def users(db, firm):
    user_a = User.objects.create_user(username="assignee-a", email="a@example.com", password="pass1234")
    user_b = User.objects.create_user(username="assignee-b", email="b@example.com", password="pass1234")
    FirmMembership.objects.create(firm=firm, user=user_a, role="firm_admin")
    FirmMembership.objects.create(firm=firm, user=user_b, role="firm_admin")
    return user_a, user_b


@pytest.fixture
def pipeline(db, firm, users):
    return Pipeline.objects.create(firm=firm, name="Assignment Pipeline", is_default=True, created_by=users[0])


@pytest.fixture
def stage(db, pipeline):
    return PipelineStage.objects.create(pipeline=pipeline, name="Assign", probability=20, display_order=1)


@pytest.mark.django_db
def test_auto_assign_deal_round_robin(firm, pipeline, stage, users):
    user_a, user_b = users
    rule = AssignmentRule.objects.create(
        firm=firm,
        name="Round Robin",
        rule_type="round_robin",
        priority=0,
        is_active=True,
    )
    rule.assignees.set([user_a, user_b])
    rule.pipelines.add(pipeline)
    rule.stages.add(stage)

    deal_one = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="First Deal",
        value="100.00",
        probability=20,
        expected_close_date=date.today(),
        created_by=user_a,
    )
    deal_two = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Second Deal",
        value="200.00",
        probability=30,
        expected_close_date=date.today(),
        created_by=user_a,
    )

    first_assignee = auto_assign_deal(deal_one)
    second_assignee = auto_assign_deal(deal_two)

    assert first_assignee == user_a
    assert deal_one.owner == user_a
    assert second_assignee == user_b
    assert deal_two.owner == user_b
