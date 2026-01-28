"""Django admin configuration for automation workflows."""

from django.contrib import admin

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


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """Admin interface for Workflow model."""

    list_display = [
        "name",
        "firm",
        "status",
        "version",
        "created_at",
        "activated_at",
    ]
    list_filter = ["status", "created_at", "activated_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "created_by", "updated_by"]
    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "firm",
                    "name",
                    "description",
                    "status",
                    "version",
                ]
            },
        ),
        (
            "Canvas",
            {
                "fields": ["canvas_data"],
            },
        ),
        (
            "Audit",
            {
                "fields": [
                    "created_at",
                    "created_by",
                    "updated_at",
                    "updated_by",
                    "activated_at",
                ]
            },
        ),
    ]


@admin.register(WorkflowTrigger)
class WorkflowTriggerAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowTrigger model."""

    list_display = [
        "workflow",
        "trigger_type",
        "is_active",
        "created_at",
    ]
    list_filter = ["trigger_type", "is_active", "created_at"]
    search_fields = ["workflow__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WorkflowNode)
class WorkflowNodeAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowNode model."""

    list_display = [
        "workflow",
        "node_id",
        "node_type",
        "label",
        "position_x",
        "position_y",
    ]
    list_filter = ["node_type", "created_at"]
    search_fields = ["workflow__name", "label", "node_id"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WorkflowEdge)
class WorkflowEdgeAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowEdge model."""

    list_display = [
        "workflow",
        "source_node",
        "target_node",
        "condition_type",
        "label",
    ]
    list_filter = ["condition_type", "created_at"]
    search_fields = ["workflow__name", "label"]
    readonly_fields = ["created_at"]


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowExecution model."""

    list_display = [
        "id",
        "workflow",
        "contact",
        "status",
        "goal_reached",
        "started_at",
        "completed_at",
    ]
    list_filter = ["status", "goal_reached", "started_at"]
    search_fields = [
        "workflow__name",
        "contact__first_name",
        "contact__last_name",
        "contact__email",
    ]
    readonly_fields = [
        "started_at",
        "completed_at",
        "idempotency_key",
        "execution_path",
        "context_data",
    ]


@admin.register(ContactFlowState)
class ContactFlowStateAdmin(admin.ModelAdmin):
    """Admin interface for ContactFlowState model."""

    list_display = [
        "execution",
        "node",
        "action_status",
        "variant",
        "entered_at",
        "exited_at",
    ]
    list_filter = ["action_status", "entered_at"]
    search_fields = ["execution__workflow__name", "node__label"]
    readonly_fields = ["entered_at", "exited_at"]


@admin.register(WorkflowGoal)
class WorkflowGoalAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowGoal model."""

    list_display = [
        "workflow",
        "name",
        "goal_value",
        "total_conversions",
        "conversion_rate",
        "total_value",
    ]
    list_filter = ["created_at"]
    search_fields = ["workflow__name", "name"]
    readonly_fields = [
        "total_conversions",
        "conversion_rate",
        "total_value",
        "created_at",
        "updated_at",
    ]


@admin.register(WorkflowAnalytics)
class WorkflowAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for WorkflowAnalytics model."""

    list_display = [
        "workflow",
        "period_start",
        "period_end",
        "total_executions",
        "goal_conversion_rate",
        "calculated_at",
    ]
    list_filter = ["period_start", "period_end", "calculated_at"]
    search_fields = ["workflow__name"]
    readonly_fields = [
        "calculated_at",
        "total_executions",
        "completed_executions",
        "failed_executions",
        "goal_reached_executions",
        "avg_completion_time_seconds",
        "median_completion_time_seconds",
        "drop_off_points",
        "node_performance",
        "goal_conversion_rate",
    ]
