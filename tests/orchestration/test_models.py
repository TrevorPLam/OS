import pytest
import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from modules.orchestration.models import (
    OrchestrationDefinition,
    OrchestrationExecution,
    StepExecution,
)
from modules.firm.models import Firm

User = get_user_model()


@pytest.fixture
def firm(db):
    return Firm.objects.create(name="Test Firm", slug="test-firm", status="active")


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", email="test@example.com", ******)


@pytest.fixture
def orchestration_definition(db, firm, user):
    """Create a simple orchestration definition"""
    return OrchestrationDefinition.objects.create(
        firm=firm,
        name="Test Workflow",
        code="test_workflow",
        version=1,
        steps_json=[
            {"step_id": "step1", "action": "send_email", "params": {}},
            {"step_id": "step2", "action": "update_status", "params": {}},
        ],
        policies={"timeout_seconds": 300, "max_retries": 3},
        status="draft",
        created_by=user,
    )


@pytest.mark.django_db
class TestOrchestrationDefinition:
    """Test OrchestrationDefinition model functionality"""

    def test_definition_creation(self, firm, user):
        """Test basic orchestration definition creation"""
        definition = OrchestrationDefinition.objects.create(
            firm=firm,
            name="Onboarding Workflow",
            code="onboarding_v1",
            version=1,
            steps_json=[{"step_id": "step1", "action": "create_account"}],
            policies={"timeout_seconds": 600},
            status="draft",
            created_by=user,
        )

        assert definition.name == "Onboarding Workflow"
        assert definition.code == "onboarding_v1"
        assert definition.version == 1
        assert definition.status == "draft"
        assert definition.firm == firm

    def test_definition_status_choices(self, firm, user):
        """Test orchestration definition status choices"""
        statuses = ["draft", "published", "deprecated"]

        for status in statuses:
            definition = OrchestrationDefinition.objects.create(
                firm=firm, name=f"Workflow {status}", code=f"workflow_{status}", version=1, status=status, created_by=user
            )
            assert definition.status == status

    def test_definition_versioning(self, firm, user):
        """Test orchestration definition versioning"""
        # Create version 1
        v1 = OrchestrationDefinition.objects.create(
            firm=firm, name="Workflow", code="test_workflow", version=1, created_by=user
        )

        # Create version 2
        v2 = OrchestrationDefinition.objects.create(
            firm=firm, name="Workflow", code="test_workflow", version=2, created_by=user
        )

        assert v1.version == 1
        assert v2.version == 2
        assert v1.code == v2.code

    def test_definition_publish(self, orchestration_definition):
        """Test publishing an orchestration definition"""
        assert orchestration_definition.status == "draft"
        assert orchestration_definition.published_at is None

        # Publish definition
        orchestration_definition.publish()

        assert orchestration_definition.status == "published"
        assert orchestration_definition.published_at is not None

    def test_definition_publish_idempotent(self, orchestration_definition):
        """Test that publishing is idempotent"""
        orchestration_definition.publish()
        first_published_at = orchestration_definition.published_at

        # Publish again
        orchestration_definition.publish()

        assert orchestration_definition.published_at == first_published_at

    def test_definition_steps_json(self, firm, user):
        """Test orchestration steps JSON structure"""
        steps = [
            {"step_id": "fetch_data", "action": "api_call", "params": {"url": "https://example.com"}},
            {"step_id": "process_data", "action": "transform", "params": {"format": "json"}},
            {"step_id": "store_data", "action": "database_write", "params": {"table": "results"}},
        ]

        definition = OrchestrationDefinition.objects.create(
            firm=firm, name="ETL Workflow", code="etl_v1", version=1, steps_json=steps, created_by=user
        )

        assert len(definition.steps_json) == 3
        assert definition.steps_json[0]["step_id"] == "fetch_data"
        assert definition.steps_json[1]["action"] == "transform"

    def test_definition_policies(self, firm, user):
        """Test orchestration policies"""
        policies = {"timeout_seconds": 1800, "max_retries": 5, "retry_backoff": "exponential"}

        definition = OrchestrationDefinition.objects.create(
            firm=firm, name="Long Running Workflow", code="long_workflow", version=1, policies=policies, created_by=user
        )

        assert definition.policies["timeout_seconds"] == 1800
        assert definition.policies["max_retries"] == 5
        assert definition.policies["retry_backoff"] == "exponential"

    def test_definition_input_output_schemas(self, firm, user):
        """Test input/output schema validation"""
        input_schema = {"type": "object", "properties": {"user_id": {"type": "integer"}, "email": {"type": "string"}}}

        output_schema = {"type": "object", "properties": {"status": {"type": "string"}, "result_id": {"type": "integer"}}}

        definition = OrchestrationDefinition.objects.create(
            firm=firm,
            name="Validated Workflow",
            code="validated_wf",
            version=1,
            input_schema=input_schema,
            output_schema=output_schema,
            created_by=user,
        )

        assert definition.input_schema["properties"]["user_id"]["type"] == "integer"
        assert definition.output_schema["properties"]["status"]["type"] == "string"

    def test_definition_string_representation(self, orchestration_definition):
        """Test __str__ method"""
        expected = f"{orchestration_definition.name} v{orchestration_definition.version} ({orchestration_definition.status})"
        assert str(orchestration_definition) == expected

    def test_definition_firm_scoping(self, firm, user):
        """Test orchestration definition tenant isolation"""
        firm2 = Firm.objects.create(name="Firm 2", slug="firm-2", status="active")

        def1 = OrchestrationDefinition.objects.create(
            firm=firm, name="Def 1", code="def1", version=1, created_by=user
        )
        def2 = OrchestrationDefinition.objects.create(
            firm=firm2, name="Def 2", code="def2", version=1, created_by=user
        )

        assert def1.firm != def2.firm

    def test_definition_unique_together(self, firm, user):
        """Test firm + code + version uniqueness"""
        OrchestrationDefinition.objects.create(firm=firm, name="Test", code="test_code", version=1, created_by=user)

        # Creating duplicate should fail
        with pytest.raises(Exception):  # IntegrityError
            OrchestrationDefinition.objects.create(firm=firm, name="Test", code="test_code", version=1, created_by=user)


@pytest.mark.django_db
class TestOrchestrationExecution:
    """Test OrchestrationExecution model functionality"""

    def test_execution_creation(self, orchestration_definition):
        """Test basic orchestration execution creation"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-001",
            correlation_id=uuid.uuid4(),
            input_data={"user_id": 123},
            status="pending",
        )

        assert execution.definition == orchestration_definition
        assert execution.status == "pending"
        assert execution.input_data["user_id"] == 123

    def test_execution_status_transitions(self, orchestration_definition):
        """Test execution status transitions"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-002",
            correlation_id=uuid.uuid4(),
            status="pending",
        )

        # Start execution
        execution.status = "running"
        execution.started_at = timezone.now()
        execution.save()

        assert execution.status == "running"
        assert execution.started_at is not None

        # Complete execution
        execution.status = "completed"
        execution.completed_at = timezone.now()
        execution.save()

        assert execution.status == "completed"
        assert execution.completed_at is not None

    def test_execution_idempotency(self, orchestration_definition):
        """Test execution idempotency key"""
        idempotency_key = "unique-exec-123"

        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key=idempotency_key,
            correlation_id=uuid.uuid4(),
        )

        assert execution.idempotency_key == idempotency_key

    def test_execution_correlation_tracking(self, orchestration_definition):
        """Test execution correlation ID for tracing"""
        correlation_id = uuid.uuid4()

        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-003",
            correlation_id=correlation_id,
        )

        assert str(execution.correlation_id) == str(correlation_id)

    def test_execution_input_output_data(self, orchestration_definition):
        """Test execution input/output data storage"""
        input_data = {"user_id": 456, "action": "create_account", "params": {"email": "test@example.com"}}

        output_data = {"status": "success", "account_id": 789, "created_at": "2024-01-01T00:00:00Z"}

        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-004",
            correlation_id=uuid.uuid4(),
            input_data=input_data,
            output_data=output_data,
        )

        assert execution.input_data["user_id"] == 456
        assert execution.output_data["account_id"] == 789

    def test_execution_error_handling(self, orchestration_definition):
        """Test execution error tracking"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-005",
            correlation_id=uuid.uuid4(),
            status="failed",
        )

        execution.error_message = "Step 2 failed: Timeout waiting for API response"
        execution.error_class = "retryable"
        execution.save()

        assert execution.status == "failed"
        assert execution.error_class == "retryable"
        assert "Timeout" in execution.error_message


@pytest.mark.django_db
class TestStepExecution:
    """Test StepExecution model functionality"""

    def test_step_execution_creation(self, orchestration_definition):
        """Test basic step execution creation"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-006",
            correlation_id=uuid.uuid4(),
        )

        step_exec = StepExecution.objects.create(
            execution=execution, step_id="step1", status="pending", attempt_count=0
        )

        assert step_exec.execution == execution
        assert step_exec.step_id == "step1"
        assert step_exec.status == "pending"
        assert step_exec.attempt_count == 0

    def test_step_execution_status_transitions(self, orchestration_definition):
        """Test step execution status transitions"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-007",
            correlation_id=uuid.uuid4(),
        )

        step_exec = StepExecution.objects.create(execution=execution, step_id="step1", status="pending")

        # Start step
        step_exec.status = "running"
        step_exec.started_at = timezone.now()
        step_exec.save()

        assert step_exec.status == "running"
        assert step_exec.started_at is not None

        # Complete step
        step_exec.status = "completed"
        step_exec.completed_at = timezone.now()
        step_exec.save()

        assert step_exec.status == "completed"

    def test_step_execution_retry_logic(self, orchestration_definition):
        """Test step execution retry tracking"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-008",
            correlation_id=uuid.uuid4(),
        )

        step_exec = StepExecution.objects.create(execution=execution, step_id="step1", status="failed", attempt_count=0)

        # First retry
        step_exec.attempt_count = 1
        step_exec.next_retry_at = timezone.now() + timedelta(seconds=60)
        step_exec.save()

        assert step_exec.attempt_count == 1
        assert step_exec.next_retry_at is not None

        # Second retry
        step_exec.attempt_count = 2
        step_exec.save()

        assert step_exec.attempt_count == 2

    def test_step_execution_error_classification(self, orchestration_definition):
        """Test step execution error classification"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-009",
            correlation_id=uuid.uuid4(),
        )

        step_exec = StepExecution.objects.create(
            execution=execution, step_id="step1", status="failed", error_class="transient", error_message="Connection timeout"
        )

        assert step_exec.error_class == "transient"
        assert step_exec.error_message == "Connection timeout"

    def test_step_execution_output_data(self, orchestration_definition):
        """Test step execution output data storage"""
        execution = OrchestrationExecution.objects.create(
            firm=orchestration_definition.firm,
            definition=orchestration_definition,
            idempotency_key="exec-010",
            correlation_id=uuid.uuid4(),
        )

        output_data = {"result": "success", "data_processed": 100, "timestamp": "2024-01-01T00:00:00Z"}

        step_exec = StepExecution.objects.create(
            execution=execution, step_id="step1", status="completed", output_data=output_data
        )

        assert step_exec.output_data["result"] == "success"
        assert step_exec.output_data["data_processed"] == 100


@pytest.mark.django_db
class TestOrchestrationWorkflow:
    """Test complete orchestration workflow scenarios"""

    def test_complete_orchestration_execution(self, firm, user):
        """Test complete orchestration execution workflow"""
        # Create definition
        definition = OrchestrationDefinition.objects.create(
            firm=firm,
            name="Complete Workflow",
            code="complete_wf",
            version=1,
            steps_json=[
                {"step_id": "step1", "action": "validate_input"},
                {"step_id": "step2", "action": "process_data"},
                {"step_id": "step3", "action": "send_notification"},
            ],
            status="published",
            created_by=user,
        )

        # Create execution
        execution = OrchestrationExecution.objects.create(
            firm=firm,
            definition=definition,
            idempotency_key="complete-exec-001",
            correlation_id=uuid.uuid4(),
            input_data={"user_id": 123},
            status="pending",
        )

        # Execute steps
        for step_data in definition.steps_json:
            step_exec = StepExecution.objects.create(
                execution=execution, step_id=step_data["step_id"], status="completed"
            )
            assert step_exec.step_id == step_data["step_id"]

        # Complete execution
        execution.status = "completed"
        execution.completed_at = timezone.now()
        execution.save()

        assert execution.status == "completed"
        assert StepExecution.objects.filter(execution=execution).count() == 3

    def test_orchestration_with_retry(self, firm, user):
        """Test orchestration with step retry"""
        definition = OrchestrationDefinition.objects.create(
            firm=firm,
            name="Retry Workflow",
            code="retry_wf",
            version=1,
            steps_json=[{"step_id": "unreliable_step", "action": "api_call"}],
            policies={"max_retries": 3},
            created_by=user,
        )

        execution = OrchestrationExecution.objects.create(
            firm=firm, definition=definition, idempotency_key="retry-exec-001", correlation_id=uuid.uuid4()
        )

        # Step fails initially
        step_exec = StepExecution.objects.create(
            execution=execution, step_id="unreliable_step", status="failed", attempt_count=1, error_class="transient"
        )

        # Retry succeeds
        step_exec.attempt_count = 2
        step_exec.status = "completed"
        step_exec.save()

        assert step_exec.status == "completed"
        assert step_exec.attempt_count == 2
