"""DRF serializers for automation workflows."""

from rest_framework import serializers

from .models import (
    ContactFlowState,
    Workflow,
    WorkflowAnalytics,
    WorkflowEdge,
    WorkflowExecution,
    WorkflowGoal,
    WorkflowNode,
    WorkflowTrigger,
)


class WorkflowTriggerSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTrigger model."""

    trigger_type_display = serializers.CharField(
        source="get_trigger_type_display",
        read_only=True,
    )

    class Meta:
        model = WorkflowTrigger
        fields = [
            "id",
            "workflow",
            "trigger_type",
            "trigger_type_display",
            "configuration",
            "filter_conditions",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowNodeSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowNode model."""

    node_type_display = serializers.CharField(
        source="get_node_type_display",
        read_only=True,
    )

    class Meta:
        model = WorkflowNode
        fields = [
            "id",
            "workflow",
            "node_id",
            "node_type",
            "node_type_display",
            "label",
            "position_x",
            "position_y",
            "configuration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowEdgeSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowEdge model."""

    source_node_details = WorkflowNodeSerializer(source="source_node", read_only=True)
    target_node_details = WorkflowNodeSerializer(source="target_node", read_only=True)

    class Meta:
        model = WorkflowEdge
        fields = [
            "id",
            "workflow",
            "source_node",
            "target_node",
            "source_node_details",
            "target_node_details",
            "condition_type",
            "condition_config",
            "label",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class WorkflowGoalSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowGoal model."""

    class Meta:
        model = WorkflowGoal
        fields = [
            "id",
            "workflow",
            "name",
            "description",
            "goal_node",
            "goal_value",
            "tracking_window_days",
            "total_conversions",
            "conversion_rate",
            "total_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_conversions",
            "conversion_rate",
            "total_value",
            "created_at",
            "updated_at",
        ]


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow model."""

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    triggers = WorkflowTriggerSerializer(many=True, read_only=True)
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    edges = WorkflowEdgeSerializer(many=True, read_only=True)
    goals = WorkflowGoalSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = [
            "id",
            "name",
            "description",
            "status",
            "status_display",
            "version",
            "canvas_data",
            "triggers",
            "nodes",
            "edges",
            "goals",
            "activated_at",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "version",
            "activated_at",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]


class WorkflowListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for workflow list views."""

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    trigger_count = serializers.IntegerField(read_only=True)
    node_count = serializers.IntegerField(read_only=True)
    execution_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workflow
        fields = [
            "id",
            "name",
            "description",
            "status",
            "status_display",
            "version",
            "trigger_count",
            "node_count",
            "execution_count",
            "activated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "version",
            "activated_at",
            "created_at",
            "updated_at",
        ]


class ContactFlowStateSerializer(serializers.ModelSerializer):
    """Serializer for ContactFlowState model."""

    node_details = WorkflowNodeSerializer(source="node", read_only=True)

    class Meta:
        model = ContactFlowState
        fields = [
            "id",
            "execution",
            "node",
            "node_details",
            "entered_at",
            "exited_at",
            "action_status",
            "action_result",
            "variant",
        ]
        read_only_fields = ["id", "entered_at", "exited_at"]


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowExecution model."""

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    workflow_details = WorkflowListSerializer(source="workflow", read_only=True)
    flow_states = ContactFlowStateSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "workflow",
            "workflow_details",
            "workflow_version",
            "contact",
            "status",
            "status_display",
            "current_node",
            "execution_path",
            "context_data",
            "trigger_type",
            "trigger_data",
            "goal_reached",
            "goal_node",
            "goal_reached_at",
            "error_count",
            "last_error",
            "started_at",
            "completed_at",
            "waiting_until",
            "waiting_for_condition",
            "flow_states",
        ]
        read_only_fields = [
            "id",
            "workflow_version",
            "execution_path",
            "goal_reached",
            "goal_reached_at",
            "error_count",
            "last_error",
            "started_at",
            "completed_at",
        ]


class WorkflowExecutionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for execution list views."""

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "workflow",
            "contact",
            "status",
            "status_display",
            "trigger_type",
            "goal_reached",
            "started_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "goal_reached",
            "started_at",
            "completed_at",
        ]


class WorkflowAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowAnalytics model."""

    workflow_details = WorkflowListSerializer(source="workflow", read_only=True)

    class Meta:
        model = WorkflowAnalytics
        fields = [
            "id",
            "workflow",
            "workflow_details",
            "period_start",
            "period_end",
            "total_executions",
            "completed_executions",
            "failed_executions",
            "goal_reached_executions",
            "avg_completion_time_seconds",
            "median_completion_time_seconds",
            "drop_off_points",
            "node_performance",
            "goal_conversion_rate",
            "calculated_at",
        ]
        read_only_fields = [
            "id",
            "total_executions",
            "completed_executions",
            "failed_executions",
            "goal_reached_executions",
            "avg_completion_time_seconds",
            "median_completion_time_seconds",
            "drop_off_points",
            "node_performance",
            "goal_conversion_rate",
            "calculated_at",
        ]
