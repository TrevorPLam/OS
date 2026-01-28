"""
Automation Workflow Execution Engine (AUTO-5).

Implements:
- Workflow execution scheduler
- Contact flow tracking
- Goal tracking and completion
- Error handling and retry logic
- Wait condition evaluation
- If/else branching logic

Integrates with job queue system for async execution.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from modules.firm.utils import firm_db_session
from modules.jobs.models import JobQueue

from .actions import get_action_executor
from .models import (
    ContactFlowState,
    WorkflowEdge,
    WorkflowExecution,
    WorkflowNode,
)


class WorkflowExecutor:
    """
    Main workflow execution engine.

    Handles node-by-node execution with branching, waits, and goals.

    Meta-commentary:
    - **Current Status:** Core execution flow implemented with node traversal and wait handling.
    - **Follow-up (T-066):** Add trigger indexing and compensation logic for failed nodes.
    - **Assumption:** Workflow graph is valid and nodes/edges are consistent at runtime.
    - **Missing:** Centralized retry policy enforcement and execution locking.
    - **Limitation:** Error handling is coarse-grained; no per-node retry metadata.
    """

    def __init__(self, execution: WorkflowExecution):
        """
        Initialize executor.

        Args:
            execution: WorkflowExecution instance
        """
        self.execution = execution
        self.workflow = execution.workflow
        self.contact = execution.contact
        self.firm = execution.firm

    @staticmethod
    def queue_execution(execution: WorkflowExecution) -> None:
        """
        Queue workflow execution in job system.

        Args:
            execution: WorkflowExecution to queue
        """
        JobQueue.objects.create(
            firm=execution.firm,
            category="orchestration",
            job_type="workflow_execution",
            idempotency_key=f"workflow_exec_{execution.id}",
            priority=2,  # Medium priority
            payload={
                "execution_id": execution.id,
                "firm_id": execution.firm_id,
            },
        )

    def execute(self) -> None:
        """
        Execute workflow from current state.

        Continues execution from current_node or starts from beginning.
        """
        try:
            # Get starting node
            current_node = self._get_starting_node()
            if not current_node:
                self._fail_execution("No starting node found")
                return

            # Execute nodes until completion or wait
            while current_node:
                # Execute node
                result = self._execute_node(current_node)

                if result["status"] == "wait":
                    # Node requires waiting
                    self._set_waiting(
                        current_node,
                        result.get("wait_until"),
                        result.get("wait_condition"),
                    )
                    return

                elif result["status"] == "goal":
                    # Goal reached
                    self._complete_with_goal(current_node)
                    return

                elif result["status"] == "failed":
                    # Node failed
                    self._handle_error(current_node, result.get("error"))
                    return

                # Move to next node
                current_node = self._get_next_node(current_node, result)

            # No more nodes - execution complete
            self._complete_execution()

        except Exception as e:
            self._fail_execution(str(e))

    def _get_starting_node(self) -> Optional[WorkflowNode]:
        """Get starting node for execution."""
        if self.execution.current_node:
            # Resume from current node
            return self.execution.current_node

        # Find first node (no incoming edges)
        nodes_with_incoming = WorkflowEdge.objects.filter(
            workflow=self.workflow
        ).values_list("target_node_id", flat=True)

        first_node = WorkflowNode.objects.filter(
            workflow=self.workflow
        ).exclude(
            id__in=nodes_with_incoming
        ).first()

        return first_node

    def _execute_node(self, node: WorkflowNode) -> Dict[str, Any]:
        """
        Execute a single node.

        Args:
            node: Node to execute

        Returns:
            Execution result dictionary
        """
        # Create flow state for tracking
        flow_state = ContactFlowState.objects.create(
            firm=self.firm,
            execution=self.execution,
            node=node,
        )

        # Update execution path
        if not self.execution.execution_path:
            self.execution.execution_path = []
        self.execution.execution_path.append(node.node_id)
        self.execution.current_node = node
        self.execution.save()

        try:
            # Execute based on node type
            if node.node_type == "goal":
                # Goal node
                return self._execute_goal(node, flow_state)

            elif node.node_type == "condition":
                # If/else condition
                return self._execute_condition(node, flow_state)

            elif node.node_type.startswith("wait_"):
                # Wait node
                return self._execute_wait(node, flow_state)

            elif node.node_type == "split":
                # A/B split
                return self._execute_split(node, flow_state)

            else:
                # Action node
                return self._execute_action(node, flow_state)

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }

    def _execute_action(self, node: WorkflowNode, flow_state: ContactFlowState) -> Dict[str, Any]:
        """Execute action node."""
        # Get action executor
        try:
            executor_class = get_action_executor(node.node_type)
            result = executor_class.execute(
                self.execution,
                node,
                node.configuration,
            )

            # Update flow state
            flow_state.action_status = result.get("status", "completed")
            flow_state.action_result = result
            flow_state.exited_at = timezone.now()
            flow_state.save()

            return result

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
            }

    def _execute_condition(self, node: WorkflowNode, flow_state: ContactFlowState) -> Dict[str, Any]:
        """
        Execute if/else condition node.

        Configuration:
        - condition_type: Type of condition (field_equals, field_gt, etc.)
        - field_name: Field to evaluate
        - operator: Comparison operator
        - value: Value to compare against
        """
        config = node.configuration
        condition_type = config.get("condition_type")
        field_name = config.get("field_name")
        operator = config.get("operator")
        value = config.get("value")

        # Evaluate condition
        result = self._evaluate_condition(
            condition_type,
            field_name,
            operator,
            value,
        )

        # Update flow state
        flow_state.action_status = "evaluated"
        flow_state.action_result = {"condition_met": result}
        flow_state.exited_at = timezone.now()
        flow_state.save()

        return {
            "status": "success",
            "condition_met": result,
        }

    def _evaluate_condition(
        self,
        condition_type: str,
        field_name: str,
        operator: str,
        value: Any,
    ) -> bool:
        """Evaluate condition against contact data."""
        # Get field value from contact
        if hasattr(self.contact, field_name):
            field_value = getattr(self.contact, field_name)
        elif field_name in self.execution.context_data:
            field_value = self.execution.context_data[field_name]
        else:
            return False

        # Evaluate based on operator
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "contains":
            return value in str(field_value)
        elif operator == "greater_than":
            return field_value > value
        elif operator == "less_than":
            return field_value < value
        elif operator == "is_empty":
            return not field_value
        elif operator == "is_not_empty":
            return bool(field_value)
        else:
            return False

    def _execute_wait(self, node: WorkflowNode, flow_state: ContactFlowState) -> Dict[str, Any]:
        """
        Execute wait node.

        Configuration:
        - wait_type: time, until_date, until_condition
        - wait_duration_hours: For time wait
        - wait_until_date: For date wait
        - wait_condition: For condition wait
        """
        config = node.configuration
        wait_type = config.get("wait_type", "time")

        if wait_type == "time":
            # Wait for duration
            duration_hours = config.get("wait_duration_hours", 24)
            wait_until = timezone.now() + timedelta(hours=duration_hours)

            return {
                "status": "wait",
                "wait_until": wait_until,
            }

        elif wait_type == "until_date":
            # Wait until specific date
            wait_until_date = config.get("wait_until_date")
            
            # Parse date string if it's a string (ISO 8601 format)
            if isinstance(wait_until_date, str):
                try:
                    # Parse ISO 8601 date string
                    parsed_date = parse_datetime(wait_until_date)
                    if parsed_date is None:
                        # If parse_datetime fails, try parsing as date only
                        date_only = parse_date(wait_until_date)
                        if date_only:
                            # Convert date to datetime at start of day in current timezone
                            parsed_date = timezone.make_aware(
                                datetime.combine(date_only, datetime.min.time())
                            )
                    
                    if parsed_date is None:
                        # Invalid date format, log error and continue
                        flow_state.status = "failed"
                        flow_state.error_message = f"Invalid date format: {wait_until_date}"
                        flow_state.save()
                        return {
                            "status": "failed",
                            "error": f"Invalid date format: {wait_until_date}",
                        }
                    
                    # Ensure timezone-aware datetime
                    if timezone.is_naive(parsed_date):
                        parsed_date = timezone.make_aware(parsed_date)
                    
                    wait_until_date = parsed_date
                except (ValueError, TypeError) as e:
                    # Handle parsing errors
                    flow_state.status = "failed"
                    flow_state.error_message = f"Error parsing date: {str(e)}"
                    flow_state.save()
                    return {
                        "status": "failed",
                        "error": f"Error parsing date: {str(e)}",
                    }

            return {
                "status": "wait",
                "wait_until": wait_until_date,
            }

        elif wait_type == "until_condition":
            # Wait for condition
            wait_condition = config.get("wait_condition", {})

            return {
                "status": "wait",
                "wait_condition": wait_condition,
            }

        return {"status": "success"}

    def _execute_split(self, node: WorkflowNode, flow_state: ContactFlowState) -> Dict[str, Any]:
        """
        Execute A/B split node.

        Configuration:
        - split_ratio: Percentage for variant A (0-100)
        """
        config = node.configuration
        split_ratio = config.get("split_ratio", 50)

        # Assign variant based on contact ID
        variant = "A" if (self.contact.id % 100) < split_ratio else "B"

        # Store variant in flow state
        flow_state.variant = variant
        flow_state.exited_at = timezone.now()
        flow_state.save()

        return {
            "status": "success",
            "variant": variant,
        }

    def _execute_goal(self, node: WorkflowNode, flow_state: ContactFlowState) -> Dict[str, Any]:
        """Execute goal node."""
        flow_state.action_status = "goal_reached"
        flow_state.exited_at = timezone.now()
        flow_state.save()

        return {
            "status": "goal",
            "goal_node_id": node.id,
        }

    def _get_next_node(self, current_node: WorkflowNode, result: Dict[str, Any]) -> Optional[WorkflowNode]:
        """
        Get next node to execute based on current node and result.

        Args:
            current_node: Current node
            result: Execution result

        Returns:
            Next node or None if no more nodes
        """
        # Get outgoing edges
        edges = WorkflowEdge.objects.filter(
            workflow=self.workflow,
            source_node=current_node,
        )

        if not edges.exists():
            return None

        # If condition node, follow appropriate edge
        if current_node.node_type == "condition":
            condition_met = result.get("condition_met", False)
            edge = edges.filter(
                condition_type="yes" if condition_met else "no"
            ).first()
            if edge:
                return edge.target_node

        # If split node, follow variant edge
        elif current_node.node_type == "split":
            variant = result.get("variant", "A")
            edge = edges.filter(condition_type=variant).first()
            if edge:
                return edge.target_node

        # Otherwise, follow first edge
        edge = edges.first()
        return edge.target_node if edge else None

    def _set_waiting(
        self,
        node: WorkflowNode,
        wait_until: timezone.datetime = None,
        wait_condition: Dict[str, Any] = None,
    ) -> None:
        """Set execution to waiting state."""
        self.execution.status = "waiting"
        self.execution.current_node = node
        self.execution.waiting_until = wait_until
        self.execution.waiting_for_condition = wait_condition or {}
        self.execution.save()

    def _complete_with_goal(self, goal_node: WorkflowNode) -> None:
        """Complete execution with goal reached."""
        self.execution.status = "goal_reached"
        self.execution.goal_reached = True
        self.execution.goal_node = goal_node
        self.execution.goal_reached_at = timezone.now()
        self.execution.completed_at = timezone.now()
        self.execution.save()

        # Update goal analytics
        from .models import WorkflowGoal
        goals = WorkflowGoal.objects.filter(
            workflow=self.workflow,
            goal_node=goal_node,
        )
        for goal in goals:
            goal.update_analytics()

    def _complete_execution(self) -> None:
        """Complete execution successfully."""
        self.execution.status = "completed"
        self.execution.completed_at = timezone.now()
        self.execution.save()

    def _handle_error(self, node: WorkflowNode, error: str) -> None:
        """Handle execution error."""
        self.execution.error_count += 1
        self.execution.last_error = error

        # Retry logic
        max_retries = 3
        if self.execution.error_count < max_retries:
            # Queue retry
            self.execution.status = "running"
            self.execution.save()
            WorkflowExecutor.queue_execution(self.execution)
        else:
            # Max retries exceeded
            self._fail_execution(f"Max retries exceeded: {error}")

    def _fail_execution(self, error: str) -> None:
        """Fail execution."""
        self.execution.status = "failed"
        self.execution.last_error = error
        self.execution.completed_at = timezone.now()
        self.execution.save()


def process_waiting_executions() -> None:
    """
    Process executions in waiting state.

    Should be called periodically by scheduler to resume waiting workflows.
    """
    now = timezone.now()

    # Find executions ready to resume
    executions = WorkflowExecution.objects.filter(
        status="waiting",
        waiting_until__lte=now,
    )

    for execution in executions:
        # Queue execution
        WorkflowExecutor.queue_execution(execution)


def process_workflow_execution_job(job_payload: Dict[str, Any]) -> None:
    """
    Job handler for workflow execution.

    Args:
        job_payload: Job payload with execution_id
    """
    execution_id = job_payload.get("execution_id")
    firm_id = job_payload.get("firm_id")
    if not execution_id or not firm_id:
        return

    with firm_db_session(firm_id):
        try:
            execution = WorkflowExecution.objects.get(id=execution_id)
            executor = WorkflowExecutor(execution)
            executor.execute()
        except WorkflowExecution.DoesNotExist:
            pass
