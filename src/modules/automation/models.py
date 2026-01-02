"""
Automation Workflow Models (AUTO-1 through AUTO-6).

Implements:
- Workflow: Visual automation workflows with nodes and edges
- WorkflowTrigger: Event-based workflow triggers
- WorkflowAction: Executable actions within workflows
- WorkflowExecution: Execution tracking with contact flow
- WorkflowNode: Individual nodes in workflow canvas
- WorkflowEdge: Connections between nodes
- ContactFlowState: Per-contact execution tracking
- WorkflowGoal: Conversion goals and analytics

TIER 0: All automation records belong to exactly one Firm for tenant isolation.
Extends orchestration engine with visual workflow builder capabilities.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class Workflow(models.Model):
    """
    Visual automation workflow with drag-and-drop canvas.

    A workflow consists of:
    - Trigger configuration (what starts the workflow)
    - Nodes (actions, conditions, waits)
    - Edges (connections between nodes)
    - Goals (conversion tracking)

    Invariants:
    - Published workflows are immutable
    - Active workflows must have valid trigger configuration
    - Node graph must be acyclic and have exactly one start node
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="automation_workflows",
        help_text="Firm (workspace) this workflow belongs to",
    )

    # Identity
    name = models.CharField(
        max_length=255,
        help_text="Human-readable workflow name",
    )
    description = models.TextField(
        blank=True,
        help_text="Workflow description and purpose",
    )

    # Status and lifecycle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )
    activated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When workflow was first activated",
    )

    # Version tracking
    version = models.IntegerField(
        default=1,
        help_text="Workflow version number",
    )

    # Workflow canvas data (visual representation)
    canvas_data = models.JSONField(
        default=dict,
        help_text="Visual canvas state (zoom, pan, etc.)",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="updated_workflows",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="auto_wf_firm_status_idx"),
            models.Index(fields=["firm", "-created_at"], name="auto_wf_firm_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.status})"

    def activate(self, user=None) -> "Workflow":
        """Activate this workflow."""
        if self.status == "active":
            return self

        # Validate workflow before activation
        self.validate_workflow()

        self.status = "active"
        if not self.activated_at:
            self.activated_at = timezone.now()
        self.updated_by = user
        self.save()
        return self

    def pause(self, user=None) -> "Workflow":
        """Pause this workflow."""
        self.status = "paused"
        self.updated_by = user
        self.save()
        return self

    def validate_workflow(self) -> None:
        """Validate workflow configuration before activation."""
        errors = {}

        # Must have at least one trigger
        if not self.triggers.exists():
            errors["triggers"] = "Workflow must have at least one trigger"

        # Must have at least one node
        if not self.nodes.exists():
            errors["nodes"] = "Workflow must have at least one node"

        # Validate no cycles in node graph
        if self._has_cycles():
            errors["nodes"] = "Workflow cannot contain cycles"

        if errors:
            raise ValidationError(errors)

    def _has_cycles(self) -> bool:
        """Check if workflow has cycles using DFS."""
        # Build adjacency list
        edges = self.edges.all()
        graph = {}
        for edge in edges:
            if edge.source_node_id not in graph:
                graph[edge.source_node_id] = []
            graph[edge.source_node_id].append(edge.target_node_id)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in graph.keys():
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False


class WorkflowTrigger(models.Model):
    """
    Trigger configuration for workflows (AUTO-2).

    Defines what event starts a workflow execution:
    - Form submission
    - Email actions (open, click, reply)
    - Site tracking
    - Deal changes
    - Score thresholds
    - Date/time based
    - Manual triggers

    Invariants:
    - Trigger configuration must match trigger type schema
    - Active triggers are evaluated in real-time
    """

    TRIGGER_TYPE_CHOICES = [
        # Form triggers
        ("form_submitted", "Form Submitted"),

        # Email triggers
        ("email_opened", "Email Opened"),
        ("email_clicked", "Email Link Clicked"),
        ("email_replied", "Email Replied"),
        ("email_bounced", "Email Bounced"),
        ("email_unsubscribed", "Email Unsubscribed"),

        # Site tracking triggers
        ("page_visited", "Page Visited"),
        ("site_activity", "Site Activity Detected"),

        # CRM triggers
        ("contact_created", "Contact Created"),
        ("contact_updated", "Contact Updated"),
        ("contact_tag_added", "Contact Tag Added"),
        ("contact_tag_removed", "Contact Tag Removed"),
        ("contact_list_added", "Added to List"),
        ("contact_list_removed", "Removed from List"),

        # Deal triggers
        ("deal_created", "Deal Created"),
        ("deal_stage_changed", "Deal Stage Changed"),
        ("deal_value_changed", "Deal Value Changed"),
        ("deal_won", "Deal Won"),
        ("deal_lost", "Deal Lost"),

        # Score triggers
        ("score_threshold_reached", "Score Threshold Reached"),
        ("score_threshold_dropped", "Score Dropped Below Threshold"),

        # Date/time triggers
        ("date_reached", "Specific Date Reached"),
        ("date_field_reached", "Date Field Reached"),
        ("time_delay", "Time Delay Elapsed"),
        ("anniversary", "Anniversary"),

        # Manual triggers
        ("manual", "Manual Trigger"),
        ("api", "API Trigger"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="workflow_triggers",
    )

    # Parent workflow
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="triggers",
    )

    # Trigger configuration
    trigger_type = models.CharField(
        max_length=50,
        choices=TRIGGER_TYPE_CHOICES,
        help_text="Type of trigger event",
    )

    # Trigger-specific configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Trigger-specific settings (form_id, tag_id, threshold, etc.)",
    )

    # Filter criteria
    filter_conditions = models.JSONField(
        default=dict,
        help_text="Additional conditions to evaluate (field comparisons, segments, etc.)",
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this trigger is actively monitoring",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow_trigger"
        ordering = ["workflow", "trigger_type"]
        indexes = [
            models.Index(fields=["firm", "trigger_type", "is_active"], name="auto_trg_firm_type_act_idx"),
            models.Index(fields=["workflow"], name="auto_trg_workflow_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name}: {self.get_trigger_type_display()}"

    def evaluate(self, event_data: Dict[str, Any]) -> bool:
        """
        Evaluate if this trigger matches the given event.

        Args:
            event_data: Event context data

        Returns:
            True if trigger conditions are met
        """
        # Check configuration matches
        config_match = self._check_configuration(event_data)
        if not config_match:
            return False

        # Check filter conditions
        filter_match = self._check_filters(event_data)
        return filter_match

    def _check_configuration(self, event_data: Dict[str, Any]) -> bool:
        """Check if event matches trigger configuration."""
        # Implementation depends on trigger type
        if self.trigger_type == "form_submitted":
            form_id = self.configuration.get("form_id")
            return str(event_data.get("form_id")) == str(form_id)

        elif self.trigger_type == "contact_tag_added":
            tag_id = self.configuration.get("tag_id")
            return str(event_data.get("tag_id")) == str(tag_id)

        elif self.trigger_type == "score_threshold_reached":
            threshold = self.configuration.get("threshold", 0)
            score = event_data.get("score", 0)
            return score >= threshold

        # Default: configuration match
        return True

    def _check_filters(self, event_data: Dict[str, Any]) -> bool:
        """Check if event passes filter conditions."""
        if not self.filter_conditions:
            return True

        # Evaluate filter conditions
        # This would integrate with segment/filtering logic
        return True


class WorkflowNode(models.Model):
    """
    Individual node in workflow canvas (AUTO-4).

    Node types:
    - Action: Execute an action (send email, create task, etc.)
    - Condition: If/else branching
    - Wait: Time delay or wait for condition
    - Goal: Conversion goal tracking

    Invariants:
    - Node configuration must match node type schema
    - Position must be within canvas bounds
    """

    NODE_TYPE_CHOICES = [
        # Action nodes (AUTO-3)
        ("send_email", "Send Email"),
        ("send_sms", "Send SMS"),
        ("create_task", "Create Task"),
        ("create_deal", "Create Deal"),
        ("update_deal", "Update Deal"),
        ("update_contact", "Update Contact Field"),
        ("add_tag", "Add Tag"),
        ("remove_tag", "Remove Tag"),
        ("add_to_list", "Add to List"),
        ("remove_from_list", "Remove from List"),
        ("webhook", "Send Webhook"),
        ("internal_notification", "Send Internal Notification"),

        # Control flow nodes
        ("condition", "If/Else Condition"),
        ("wait_time", "Wait for Time"),
        ("wait_until", "Wait Until Date"),
        ("wait_condition", "Wait for Condition"),
        ("split", "A/B Split Test"),

        # Goal nodes
        ("goal", "Goal Reached"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="workflow_nodes",
    )

    # Parent workflow
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="nodes",
    )

    # Node identity
    node_id = models.CharField(
        max_length=100,
        help_text="Unique node identifier within workflow",
    )
    node_type = models.CharField(
        max_length=50,
        choices=NODE_TYPE_CHOICES,
        help_text="Type of node",
    )
    label = models.CharField(
        max_length=255,
        help_text="Human-readable node label",
    )

    # Visual position on canvas
    position_x = models.IntegerField(
        default=0,
        help_text="X coordinate on canvas",
    )
    position_y = models.IntegerField(
        default=0,
        help_text="Y coordinate on canvas",
    )

    # Node configuration
    configuration = models.JSONField(
        default=dict,
        help_text="Node-specific configuration",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow_node"
        ordering = ["workflow", "position_y", "position_x"]
        indexes = [
            models.Index(fields=["firm", "workflow"], name="auto_node_firm_wf_idx"),
        ]
        unique_together = [["workflow", "node_id"]]

    def __str__(self) -> str:
        return f"{self.workflow.name}: {self.label}"


class WorkflowEdge(models.Model):
    """
    Connection between workflow nodes (AUTO-4).

    Represents directional flow from source to target node.
    May include conditional logic for branching.

    Invariants:
    - Source and target must belong to same workflow
    - Cannot create cycles
    - Conditional edges must have valid condition configuration
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="workflow_edges",
    )

    # Parent workflow
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="edges",
    )

    # Connection
    source_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.CASCADE,
        related_name="outgoing_edges",
    )
    target_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.CASCADE,
        related_name="incoming_edges",
    )

    # Conditional logic
    condition_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Condition type (yes/no for if/else, etc.)",
    )
    condition_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Condition configuration",
    )

    # Visual styling
    label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Edge label (Yes, No, etc.)",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow_edge"
        ordering = ["workflow", "source_node"]
        indexes = [
            models.Index(fields=["firm", "workflow"], name="auto_edge_firm_wf_idx"),
            models.Index(fields=["source_node"], name="auto_edge_source_idx"),
            models.Index(fields=["target_node"], name="auto_edge_target_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.source_node.label} → {self.target_node.label}"


class WorkflowExecution(models.Model):
    """
    Execution instance of a workflow for a specific contact (AUTO-5).

    Tracks:
    - Current state of execution
    - Which nodes have been executed
    - Execution path taken
    - Goals reached
    - Errors and retries

    Invariants:
    - One execution per contact per workflow at a time
    - Idempotent creation
    - Complete audit trail of execution path
    """

    STATUS_CHOICES = [
        ("running", "Running"),
        ("waiting", "Waiting"),
        ("completed", "Completed"),
        ("goal_reached", "Goal Reached"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="workflow_executions",
    )

    # Workflow reference
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    workflow_version = models.IntegerField(
        help_text="Workflow version at execution time",
    )

    # Target contact
    contact = models.ForeignKey(
        "crm.Contact",
        on_delete=models.CASCADE,
        related_name="workflow_executions",
        help_text="Contact being processed through workflow",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="running",
    )

    # Execution state
    current_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_executions",
        help_text="Current node being executed or waited on",
    )

    # Execution path (ordered list of node IDs)
    execution_path = models.JSONField(
        default=list,
        help_text="Ordered list of nodes executed",
    )

    # Execution context
    context_data = models.JSONField(
        default=dict,
        help_text="Execution context and variables",
    )

    # Trigger information
    trigger_type = models.CharField(
        max_length=50,
        help_text="What triggered this execution",
    )
    trigger_data = models.JSONField(
        default=dict,
        help_text="Trigger event data",
    )

    # Goal tracking
    goal_reached = models.BooleanField(
        default=False,
        help_text="Whether execution reached a goal",
    )
    goal_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goal_executions",
        help_text="Goal node that was reached",
    )
    goal_reached_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Error tracking
    error_count = models.IntegerField(
        default=0,
        help_text="Number of errors encountered",
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message",
    )

    # Idempotency
    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="Execution idempotency key",
    )

    # Lifecycle
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Wait scheduling
    waiting_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Resume execution at this time",
    )
    waiting_for_condition = models.JSONField(
        default=dict,
        blank=True,
        help_text="Condition to wait for",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow_execution"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="auto_exec_firm_status_idx"),
            models.Index(fields=["workflow", "-started_at"], name="auto_exec_wf_started_idx"),
            models.Index(fields=["contact", "-started_at"], name="auto_exec_contact_idx"),
            models.Index(fields=["idempotency_key"], name="auto_exec_idem_idx"),
            models.Index(fields=["waiting_until"], name="auto_exec_waiting_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name} for {self.contact} ({self.status})"

    @staticmethod
    def compute_idempotency_key(
        firm_id: int,
        workflow_id: int,
        contact_id: int,
        trigger_type: str,
        discriminator: str = "",
    ) -> str:
        """Compute execution idempotency key."""
        components = f"{firm_id}:{workflow_id}:{contact_id}:{trigger_type}:{discriminator}"
        return hashlib.sha256(components.encode()).hexdigest()


class ContactFlowState(models.Model):
    """
    Per-contact flow state tracking (AUTO-5).

    Tracks individual contact's journey through workflow:
    - Which nodes have been visited
    - When each action was taken
    - A/B test variant assigned
    - Drop-off points

    Used for analytics and flow visualization (AUTO-6).
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="contact_flow_states",
    )

    # Execution reference
    execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="flow_states",
    )

    # Node reference
    node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.CASCADE,
        related_name="flow_states",
    )

    # State
    entered_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When contact entered this node",
    )
    exited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When contact exited this node",
    )

    # Action result
    action_status = models.CharField(
        max_length=20,
        blank=True,
        help_text="Status of action execution (sent, delivered, clicked, etc.)",
    )
    action_result = models.JSONField(
        default=dict,
        blank=True,
        help_text="Action execution result data",
    )

    # A/B test tracking
    variant = models.CharField(
        max_length=50,
        blank=True,
        help_text="A/B test variant assigned",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_contact_flow_state"
        ordering = ["execution", "entered_at"]
        indexes = [
            models.Index(fields=["firm", "node", "-entered_at"], name="auto_flow_firm_node_idx"),
            models.Index(fields=["execution", "entered_at"], name="auto_flow_exec_entered_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.execution.contact} at {self.node.label}"


class WorkflowGoal(models.Model):
    """
    Conversion goal tracking (AUTO-6).

    Defines success metrics for workflows:
    - What constitutes a conversion
    - Goal value (revenue, etc.)
    - Tracking window

    Used for analytics and reporting.
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="workflow_goals",
    )

    # Parent workflow
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="goals",
    )

    # Goal definition
    name = models.CharField(
        max_length=255,
        help_text="Goal name",
    )
    description = models.TextField(
        blank=True,
        help_text="Goal description",
    )

    # Goal node reference
    goal_node = models.ForeignKey(
        WorkflowNode,
        on_delete=models.CASCADE,
        related_name="goals",
        help_text="Node that represents goal completion",
    )

    # Goal value
    goal_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Revenue or value assigned to this goal",
    )

    # Tracking window
    tracking_window_days = models.IntegerField(
        default=30,
        help_text="Days to track conversions",
    )

    # Analytics
    total_conversions = models.IntegerField(
        default=0,
        help_text="Total number of conversions",
    )
    conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Conversion rate percentage",
    )
    total_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total value from conversions",
    )

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow_goal"
        ordering = ["workflow", "name"]
        indexes = [
            models.Index(fields=["firm", "workflow"], name="auto_goal_firm_wf_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.workflow.name}: {self.name}"

    def update_analytics(self) -> None:
        """Update goal analytics from executions."""
        # Count total conversions
        conversions = WorkflowExecution.objects.filter(
            firm=self.firm,
            workflow=self.workflow,
            goal_reached=True,
            goal_node=self.goal_node,
        ).count()

        # Count total executions
        total_executions = WorkflowExecution.objects.filter(
            firm=self.firm,
            workflow=self.workflow,
        ).count()

        # Calculate conversion rate
        if total_executions > 0:
            self.conversion_rate = (conversions / total_executions) * 100
        else:
            self.conversion_rate = 0

        self.total_conversions = conversions
        self.total_value = self.goal_value * conversions
        self.save()


class WorkflowAnalytics(models.Model):
    """
    Workflow performance analytics (AUTO-6).

    Aggregated metrics for workflow performance:
    - Total executions
    - Completion rate
    - Drop-off analysis
    - Average time to completion
    - Goal conversion rates

    Updated periodically for dashboard display.
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="workflow_analytics",
    )

    # Workflow reference
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name="analytics",
    )

    # Time period
    period_start = models.DateField(
        help_text="Analytics period start date",
    )
    period_end = models.DateField(
        help_text="Analytics period end date",
    )

    # Execution metrics
    total_executions = models.IntegerField(
        default=0,
        help_text="Total executions started",
    )
    completed_executions = models.IntegerField(
        default=0,
        help_text="Executions that completed",
    )
    failed_executions = models.IntegerField(
        default=0,
        help_text="Executions that failed",
    )
    goal_reached_executions = models.IntegerField(
        default=0,
        help_text="Executions that reached goal",
    )

    # Timing metrics
    avg_completion_time_seconds = models.IntegerField(
        default=0,
        help_text="Average time to completion in seconds",
    )
    median_completion_time_seconds = models.IntegerField(
        default=0,
        help_text="Median time to completion in seconds",
    )

    # Drop-off analysis (node_id -> count)
    drop_off_points = models.JSONField(
        default=dict,
        help_text="Map of node IDs to drop-off counts",
    )

    # Node performance (node_id -> metrics)
    node_performance = models.JSONField(
        default=dict,
        help_text="Per-node performance metrics",
    )

    # Goal metrics
    goal_conversion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Overall goal conversion rate",
    )

    # Audit fields
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="When these analytics were last calculated",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "automation_workflow_analytics"
        ordering = ["-period_end", "workflow"]
        indexes = [
            models.Index(fields=["firm", "workflow", "-period_end"], name="auto_analytics_firm_wf_idx"),
        ]
        unique_together = [["workflow", "period_start", "period_end"]]

    def __str__(self) -> str:
        return f"{self.workflow.name} analytics ({self.period_start} to {self.period_end})"
