import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.automation.models import (
    Workflow,
    WorkflowTrigger,
    WorkflowAction,
    WorkflowExecution,
    WorkflowNode,
    WorkflowEdge,
    ContactFlowState,
    WorkflowGoal,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", password="pass1234")


@pytest.fixture
def workflow(db, firm, user):
    return Workflow.objects.create(
        firm=firm, name="Test Workflow", description="Test workflow description", status="draft", created_by=user
    )


@pytest.mark.django_db
class TestWorkflow:
    """Test Workflow model functionality"""

    def test_workflow_creation(self, firm, user):
        """Test basic workflow creation"""
        workflow = Workflow.objects.create(
            firm=firm, name="New Workflow", description="Workflow description", status="draft", created_by=user
        )

        assert workflow.name == "New Workflow"
        assert workflow.firm == firm
        assert workflow.status == "draft"
        assert workflow.version == 1
        assert workflow.created_by == user

    def test_workflow_status_choices(self, firm, user):
        """Test workflow status field choices"""
        statuses = ["draft", "active", "paused", "archived"]

        for status in statuses:
            workflow = Workflow.objects.create(firm=firm, name=f"Workflow {status}", status=status, created_by=user)
            assert workflow.status == status

    def test_workflow_version_tracking(self, workflow):
        """Test workflow version tracking"""
        assert workflow.version == 1

        # Version should increment (in actual implementation)
        workflow.version = 2
        workflow.save()
        assert workflow.version == 2

    def test_workflow_activation_timestamp(self, workflow):
        """Test workflow activation timestamp"""
        assert workflow.activated_at is None

        # Activate workflow
        workflow.status = "active"
        workflow.activated_at = timezone.now()
        workflow.save()

        assert workflow.activated_at is not None
        assert workflow.status == "active"

    def test_workflow_canvas_data(self, workflow):
        """Test workflow canvas data storage"""
        canvas_data = {"zoom": 1.0, "pan": {"x": 0, "y": 0}, "nodes": [], "edges": []}

        workflow.canvas_data = canvas_data
        workflow.save()

        workflow.refresh_from_db()
        assert workflow.canvas_data == canvas_data

    def test_workflow_firm_scoping(self, firm, user):
        """Test that workflows are properly scoped to firm"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        workflow1 = Workflow.objects.create(firm=firm, name="Workflow 1", created_by=user)
        workflow2 = Workflow.objects.create(firm=firm2, name="Workflow 2", created_by=user)

        all_workflows = Workflow.objects.all()
        assert workflow1 in all_workflows
        assert workflow2 in all_workflows


@pytest.mark.django_db
class TestWorkflowTrigger:
    """Test WorkflowTrigger model functionality"""

    def test_trigger_creation(self, workflow):
        """Test basic trigger creation"""
        trigger = WorkflowTrigger.objects.create(
            workflow=workflow, trigger_type="event", trigger_config={"event": "contact_created"}, is_active=True
        )

        assert trigger.workflow == workflow
        assert trigger.trigger_type == "event"
        assert trigger.is_active is True

    def test_trigger_types(self, workflow):
        """Test different trigger types"""
        trigger_types = ["event", "scheduled", "webhook", "manual"]

        for trigger_type in trigger_types:
            trigger = WorkflowTrigger.objects.create(
                workflow=workflow, trigger_type=trigger_type, trigger_config={}, is_active=True
            )
            assert trigger.trigger_type == trigger_type


@pytest.mark.django_db
class TestWorkflowAction:
    """Test WorkflowAction model functionality"""

    def test_action_creation(self, workflow):
        """Test basic action creation"""
        action = WorkflowAction.objects.create(
            workflow=workflow,
            action_type="send_email",
            action_config={"template": "welcome", "subject": "Welcome!"},
            order=1,
        )

        assert action.workflow == workflow
        assert action.action_type == "send_email"
        assert action.order == 1

    def test_action_ordering(self, workflow):
        """Test action ordering"""
        action1 = WorkflowAction.objects.create(workflow=workflow, action_type="send_email", order=1)
        action2 = WorkflowAction.objects.create(workflow=workflow, action_type="wait", order=2)
        action3 = WorkflowAction.objects.create(workflow=workflow, action_type="update_field", order=3)

        actions = WorkflowAction.objects.filter(workflow=workflow).order_by("order")
        assert list(actions) == [action1, action2, action3]


@pytest.mark.django_db
class TestWorkflowExecution:
    """Test WorkflowExecution model functionality"""

    def test_execution_creation(self, workflow):
        """Test basic execution creation"""
        execution = WorkflowExecution.objects.create(
            workflow=workflow, status="running", started_at=timezone.now(), trigger_data={"source": "manual"}
        )

        assert execution.workflow == workflow
        assert execution.status == "running"
        assert execution.started_at is not None

    def test_execution_status_tracking(self, workflow):
        """Test execution status tracking"""
        execution = WorkflowExecution.objects.create(workflow=workflow, status="running", started_at=timezone.now())

        # Complete execution
        execution.status = "completed"
        execution.completed_at = timezone.now()
        execution.save()

        assert execution.status == "completed"
        assert execution.completed_at is not None

    def test_execution_error_handling(self, workflow):
        """Test execution error tracking"""
        execution = WorkflowExecution.objects.create(workflow=workflow, status="failed", started_at=timezone.now())

        execution.error_message = "Action failed: email send timeout"
        execution.save()

        assert execution.status == "failed"
        assert execution.error_message == "Action failed: email send timeout"


@pytest.mark.django_db
class TestWorkflowNode:
    """Test WorkflowNode model functionality"""

    def test_node_creation(self, workflow):
        """Test basic node creation"""
        node = WorkflowNode.objects.create(
            workflow=workflow,
            node_type="action",
            node_config={"action": "send_email", "template": "welcome"},
            position_x=100,
            position_y=200,
        )

        assert node.workflow == workflow
        assert node.node_type == "action"
        assert node.position_x == 100
        assert node.position_y == 200

    def test_node_types(self, workflow):
        """Test different node types"""
        node_types = ["action", "condition", "wait", "split", "merge"]

        for i, node_type in enumerate(node_types):
            node = WorkflowNode.objects.create(
                workflow=workflow, node_type=node_type, position_x=100 * i, position_y=200
            )
            assert node.node_type == node_type


@pytest.mark.django_db
class TestWorkflowEdge:
    """Test WorkflowEdge model functionality"""

    def test_edge_creation(self, workflow):
        """Test basic edge creation"""
        node1 = WorkflowNode.objects.create(workflow=workflow, node_type="action", position_x=100, position_y=200)
        node2 = WorkflowNode.objects.create(workflow=workflow, node_type="action", position_x=300, position_y=200)

        edge = WorkflowEdge.objects.create(workflow=workflow, source_node=node1, target_node=node2, edge_type="next")

        assert edge.source_node == node1
        assert edge.target_node == node2
        assert edge.edge_type == "next"

    def test_conditional_edge(self, workflow):
        """Test conditional edge"""
        node1 = WorkflowNode.objects.create(workflow=workflow, node_type="condition", position_x=100, position_y=200)
        node2 = WorkflowNode.objects.create(workflow=workflow, node_type="action", position_x=300, position_y=200)

        edge = WorkflowEdge.objects.create(
            workflow=workflow, source_node=node1, target_node=node2, edge_type="conditional", condition={"if": "true"}
        )

        assert edge.edge_type == "conditional"
        assert edge.condition == {"if": "true"}


@pytest.mark.django_db
class TestContactFlowState:
    """Test ContactFlowState model functionality"""

    def test_contact_flow_state_creation(self, workflow):
        """Test basic contact flow state creation"""
        from modules.clients.models import Contact, Client

        client = Client.objects.create(
            firm=workflow.firm, company_name="Test Client", primary_contact_name="Test", primary_contact_email="test@example.com"
        )
        contact = Contact.objects.create(
            client=client, first_name="John", last_name="Doe", email="john@example.com"
        )

        flow_state = ContactFlowState.objects.create(workflow=workflow, contact=contact, status="active", entered_at=timezone.now())

        assert flow_state.workflow == workflow
        assert flow_state.contact == contact
        assert flow_state.status == "active"

    def test_contact_flow_progression(self, workflow):
        """Test contact flow progression through nodes"""
        from modules.clients.models import Contact, Client

        client = Client.objects.create(
            firm=workflow.firm, company_name="Test Client", primary_contact_name="Test", primary_contact_email="test@example.com"
        )
        contact = Contact.objects.create(
            client=client, first_name="John", last_name="Doe", email="john@example.com"
        )
        node1 = WorkflowNode.objects.create(workflow=workflow, node_type="action", position_x=100, position_y=200)

        flow_state = ContactFlowState.objects.create(workflow=workflow, contact=contact, status="active", entered_at=timezone.now())

        flow_state.current_node = node1
        flow_state.save()

        assert flow_state.current_node == node1


@pytest.mark.django_db
class TestWorkflowGoal:
    """Test WorkflowGoal model functionality"""

    def test_goal_creation(self, workflow):
        """Test basic goal creation"""
        goal = WorkflowGoal.objects.create(workflow=workflow, name="Conversion Goal", goal_type="conversion")

        assert goal.workflow == workflow
        assert goal.name == "Conversion Goal"
        assert goal.goal_type == "conversion"

    def test_goal_completion_tracking(self, workflow):
        """Test goal completion tracking"""
        goal = WorkflowGoal.objects.create(workflow=workflow, name="Click Goal", goal_type="engagement")

        goal.completion_count = 10
        goal.save()

        assert goal.completion_count == 10
