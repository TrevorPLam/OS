"""
Automation Workflow Analytics Service (AUTO-6).

Implements:
- Flow visualization with drop-off points
- Goal conversion rates
- Performance metrics per automation
- Aggregated analytics calculation

Should be run periodically to update analytics.
"""

from datetime import date, timedelta
from typing import Dict, List

from django.db.models import Avg, Count, F, Q
from django.db.models.functions import ExtractEpoch
from django.utils import timezone

from .models import (
    ContactFlowState,
    Workflow,
    WorkflowAnalytics,
    WorkflowExecution,
    WorkflowNode,
)


class AnalyticsCalculator:
    """Calculate workflow analytics."""

    @staticmethod
    def calculate_workflow_analytics(
        workflow: Workflow,
        period_start: date,
        period_end: date,
    ) -> WorkflowAnalytics:
        """
        Calculate analytics for workflow over time period.

        Args:
            workflow: Workflow to analyze
            period_start: Start date of period
            period_end: End date of period

        Returns:
            WorkflowAnalytics instance
        """
        # Get or create analytics record
        analytics, created = WorkflowAnalytics.objects.get_or_create(
            firm=workflow.firm,
            workflow=workflow,
            period_start=period_start,
            period_end=period_end,
        )

        # Get executions in period
        executions = WorkflowExecution.objects.filter(
            firm=workflow.firm,
            workflow=workflow,
            started_at__date__gte=period_start,
            started_at__date__lte=period_end,
        )

        # Calculate execution metrics
        total_executions = executions.count()
        completed_executions = executions.filter(
            status__in=["completed", "goal_reached"]
        ).count()
        failed_executions = executions.filter(status="failed").count()
        goal_reached_executions = executions.filter(goal_reached=True).count()

        analytics.total_executions = total_executions
        analytics.completed_executions = completed_executions
        analytics.failed_executions = failed_executions
        analytics.goal_reached_executions = goal_reached_executions

        # Calculate timing metrics
        completed_with_times = executions.filter(
            status__in=["completed", "goal_reached"],
            completed_at__isnull=False,
        )

        if completed_with_times.exists():
            # Calculate average completion time
            avg_time = completed_with_times.annotate(
                completion_seconds=ExtractEpoch(
                    F("completed_at") - F("started_at")
                )
            ).aggregate(
                avg=Avg("completion_seconds")
            )["avg"]

            analytics.avg_completion_time_seconds = int(avg_time or 0)

            # Calculate median (approximate using 50th percentile)
            times = list(
                completed_with_times.annotate(
                    completion_seconds=ExtractEpoch(
                        F("completed_at") - F("started_at")
                    )
                ).values_list("completion_seconds", flat=True).order_by("completion_seconds")
            )
            if times:
                median_idx = len(times) // 2
                analytics.median_completion_time_seconds = int(times[median_idx])

        # Calculate drop-off points
        analytics.drop_off_points = AnalyticsCalculator._calculate_drop_offs(
            workflow, executions
        )

        # Calculate node performance
        analytics.node_performance = AnalyticsCalculator._calculate_node_performance(
            workflow, executions
        )

        # Calculate goal conversion rate
        if total_executions > 0:
            analytics.goal_conversion_rate = (
                goal_reached_executions / total_executions
            ) * 100
        else:
            analytics.goal_conversion_rate = 0

        analytics.save()
        return analytics

    @staticmethod
    def _calculate_drop_offs(
        workflow: Workflow,
        executions,
    ) -> Dict[str, int]:
        """
        Calculate drop-off points in workflow.

        Returns dictionary of node_id -> count of contacts who dropped off.
        """
        drop_offs = {}

        # Get all nodes
        nodes = WorkflowNode.objects.filter(workflow=workflow)

        for node in nodes:
            # Count executions that reached this node
            reached = ContactFlowState.objects.filter(
                execution__in=executions,
                node=node,
            ).count()

            # Count executions that exited this node
            exited = ContactFlowState.objects.filter(
                execution__in=executions,
                node=node,
                exited_at__isnull=False,
            ).count()

            # Drop-off is difference
            drop_off_count = reached - exited
            if drop_off_count > 0:
                drop_offs[node.node_id] = drop_off_count

        return drop_offs

    @staticmethod
    def _calculate_node_performance(
        workflow: Workflow,
        executions,
    ) -> Dict[str, Dict]:
        """
        Calculate per-node performance metrics.

        Returns dictionary of node_id -> {
            "visits": count,
            "completions": count,
            "avg_time_seconds": float,
            "success_rate": float,
        }
        """
        performance = {}

        nodes = WorkflowNode.objects.filter(workflow=workflow)

        for node in nodes:
            flow_states = ContactFlowState.objects.filter(
                execution__in=executions,
                node=node,
            )

            visits = flow_states.count()
            completions = flow_states.filter(exited_at__isnull=False).count()

            # Calculate average time spent at node
            timed_states = flow_states.filter(
                exited_at__isnull=False
            )

            avg_time = 0
            if timed_states.exists():
                times = timed_states.annotate(
                    time_seconds=ExtractEpoch(
                        F("exited_at") - F("entered_at")
                    )
                ).aggregate(avg=Avg("time_seconds"))["avg"]
                avg_time = int(times or 0)

            # Calculate success rate
            success_rate = (completions / visits * 100) if visits > 0 else 0

            performance[node.node_id] = {
                "visits": visits,
                "completions": completions,
                "avg_time_seconds": avg_time,
                "success_rate": success_rate,
            }

        return performance

    @staticmethod
    def calculate_all_workflows(period_days: int = 30) -> None:
        """
        Calculate analytics for all active workflows.

        Args:
            period_days: Number of days to analyze (default 30)
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=period_days)

        # Get all active workflows
        workflows = Workflow.objects.filter(
            status__in=["active", "paused"]
        )

        for workflow in workflows:
            AnalyticsCalculator.calculate_workflow_analytics(
                workflow,
                start_date,
                end_date,
            )

    @staticmethod
    def get_flow_visualization_data(workflow: Workflow) -> Dict:
        """
        Get flow visualization data for workflow.

        Returns node and edge data with visit counts for visualization.
        """
        # Get all executions
        executions = WorkflowExecution.objects.filter(
            workflow=workflow
        )

        # Get nodes with visit counts
        nodes = []
        for node in workflow.nodes.all():
            visits = ContactFlowState.objects.filter(
                execution__in=executions,
                node=node,
            ).count()

            exits = ContactFlowState.objects.filter(
                execution__in=executions,
                node=node,
                exited_at__isnull=False,
            ).count()

            nodes.append({
                "id": node.node_id,
                "type": node.node_type,
                "label": node.label,
                "position": {"x": node.position_x, "y": node.position_y},
                "visits": visits,
                "exits": exits,
                "drop_off": visits - exits,
            })

        # Get edges with flow counts
        edges = []
        for edge in workflow.edges.all():
            # Count transitions through this edge
            # (approximated by visits to target node)
            transitions = ContactFlowState.objects.filter(
                execution__in=executions,
                node=edge.target_node,
            ).count()

            edges.append({
                "id": f"{edge.source_node.node_id}_{edge.target_node.node_id}",
                "source": edge.source_node.node_id,
                "target": edge.target_node.node_id,
                "label": edge.label,
                "transitions": transitions,
            })

        return {
            "nodes": nodes,
            "edges": edges,
        }


def run_daily_analytics() -> None:
    """
    Run daily analytics calculation.

    Should be scheduled to run daily via cron or job scheduler.
    """
    # Calculate last 30 days
    AnalyticsCalculator.calculate_all_workflows(period_days=30)

    # Calculate last 7 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)

    workflows = Workflow.objects.filter(
        status__in=["active", "paused"]
    )

    for workflow in workflows:
        AnalyticsCalculator.calculate_workflow_analytics(
            workflow,
            start_date,
            end_date,
        )
