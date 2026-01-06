import pytest
from datetime import date

from django.contrib.auth import get_user_model

from modules.crm.assignment_automation import StageAutomation
from modules.crm.models import Deal, DealTask, Pipeline, PipelineStage
from modules.firm.models import Firm, FirmMembership

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Automation Firm", slug="automation-firm", status="active")


@pytest.fixture
def users(db, firm):
    primary = User.objects.create_user(username="automation-owner", email="owner@example.com", password="pass1234")
    secondary = User.objects.create_user(username="automation-assignee", email="assignee@example.com", password="pass1234")
    FirmMembership.objects.create(firm=firm, user=primary, role="firm_admin")
    FirmMembership.objects.create(firm=firm, user=secondary, role="firm_admin")
    return primary, secondary


@pytest.fixture
def pipeline(db, firm, users):
    return Pipeline.objects.create(firm=firm, name="Automation Pipeline", is_default=True, created_by=users[0])


@pytest.fixture
def stage(db, pipeline):
    return PipelineStage.objects.create(pipeline=pipeline, name="Automation Stage", probability=30, display_order=1)


@pytest.mark.django_db
def test_stage_automation_assigns_user(firm, pipeline, stage, users):
    owner, target_user = users
    deal = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Assignment Automation Deal",
        value="400.00",
        probability=30,
        expected_close_date=date.today(),
        owner=owner,
        created_by=owner,
    )

    automation = StageAutomation.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Assign Owner",
        description="Assign to specific user",
        action_type="assign_user",
        action_config={"user_id": target_user.id},
    )

    executed = automation.execute(deal)
    deal.refresh_from_db()

    assert executed is True
    assert deal.owner == target_user


@pytest.mark.django_db
def test_stage_automation_creates_task(firm, pipeline, stage, users):
    owner, _ = users
    deal = Deal.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Task Automation Deal",
        value="150.00",
        probability=25,
        expected_close_date=date.today(),
        owner=owner,
        created_by=owner,
    )

    automation = StageAutomation.objects.create(
        firm=firm,
        pipeline=pipeline,
        stage=stage,
        name="Create Task",
        description="Create follow-up task",
        action_type="create_task",
        action_config={
            "task_template": {"title": "Follow Up", "description": "Call the prospect", "priority": "high"}
        },
    )

    executed = automation.execute(deal)

    assert executed is True
    assert DealTask.objects.filter(deal=deal, title="Follow Up").exists()
