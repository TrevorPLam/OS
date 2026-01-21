"""Tests for automation workflow view query efficiency."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from modules.automation.models import Workflow, WorkflowEdge, WorkflowGoal, WorkflowNode, WorkflowTrigger
from modules.automation.serializers import WorkflowSerializer
from modules.automation.views import WorkflowViewSet
from modules.firm.models import Firm
from modules.firm.utils import FirmScopingError
from tests.utils.query_budget import assert_max_queries

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="staffer", email="staffer@example.com", password="pass1234")


@pytest.fixture
def workflow(db, firm, user):
    return Workflow.objects.create(
        firm=firm,
        name="Prefetch Workflow",
        description="Workflow for query tests",
        status="draft",
        created_by=user,
    )


def build_viewset(firm, user, action):
    viewset = WorkflowViewSet()
    request = APIRequestFactory().get("/api/v1/automation/workflows/")
    request.user = user
    request.firm = firm
    viewset.request = request
    viewset.action = action
    return viewset


def build_workflow_nodes(firm, workflow, count):
    nodes = [
        WorkflowNode(
            firm=firm,
            workflow=workflow,
            node_id=f"node-{index}",
            node_type="send_email",
            label=f"Node {index}",
            position_x=index,
            position_y=index,
            configuration={},
        )
        for index in range(count)
    ]
    WorkflowNode.objects.bulk_create(nodes)
    return list(WorkflowNode.objects.filter(workflow=workflow).order_by("id"))


def build_linear_edges(firm, workflow, nodes):
    edges = [
        WorkflowEdge(
            firm=firm,
            workflow=workflow,
            source_node=nodes[index],
            target_node=nodes[index + 1],
            condition_type="",
            condition_config={},
            label="",
        )
        for index in range(len(nodes) - 1)
    ]
    WorkflowEdge.objects.bulk_create(edges)


def create_goal(firm, workflow, node):
    return WorkflowGoal.objects.create(
        firm=firm,
        workflow=workflow,
        name="Completion",
        description="Goal for finishing",
        goal_node=node,
        goal_value=100,
        tracking_window_days=14,
    )


@pytest.mark.django_db
def test_workflow_detail_prefetches_edges_and_goals(firm, user, workflow):
    WorkflowTrigger.objects.create(
        firm=firm,
        workflow=workflow,
        trigger_type="manual",
        configuration={},
        filter_conditions={},
        is_active=True,
    )
    nodes = build_workflow_nodes(firm, workflow, 2)
    build_linear_edges(firm, workflow, nodes)
    create_goal(firm, workflow, nodes[1])

    viewset = build_viewset(firm, user, action="retrieve")

    with assert_max_queries(6):
        instance = viewset.get_queryset().get(pk=workflow.id)
        data = WorkflowSerializer(instance).data

    assert len(data["edges"]) == 1
    assert data["edges"][0]["source_node_details"]["id"] == nodes[0].id
    assert data["goals"][0]["goal_node"] == nodes[1].id


@pytest.mark.django_db
def test_workflow_detail_handles_empty_relations(firm, user, workflow):
    viewset = build_viewset(firm, user, action="retrieve")

    with assert_max_queries(5):
        instance = viewset.get_queryset().get(pk=workflow.id)
        data = WorkflowSerializer(instance).data

    assert data["triggers"] == []
    assert data["nodes"] == []
    assert data["edges"] == []
    assert data["goals"] == []


@pytest.mark.django_db
def test_workflow_detail_prefetches_large_workflows(firm, user, workflow):
    nodes = build_workflow_nodes(firm, workflow, 1000)
    build_linear_edges(firm, workflow, nodes)

    viewset = build_viewset(firm, user, action="retrieve")

    with assert_max_queries(6):
        instance = viewset.get_queryset().get(pk=workflow.id)
        data = WorkflowSerializer(instance).data

    assert len(data["nodes"]) == 1000
    assert len(data["edges"]) == 999


@pytest.mark.django_db
def test_workflow_viewset_requires_firm(user):
    viewset = WorkflowViewSet()
    request = APIRequestFactory().get("/api/v1/automation/workflows/")
    request.user = user
    viewset.request = request
    viewset.action = "retrieve"

    with pytest.raises(FirmScopingError):
        viewset.get_queryset()
