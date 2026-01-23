"""
API Views for Automation Workflow module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2.5: Portal users are explicitly denied access to automation endpoints.
"""

from django.db.models import Count, Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.firm.utils import FirmScopedMixin

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
from .serializers import (
    ContactFlowStateSerializer,
    WorkflowAnalyticsSerializer,
    WorkflowEdgeSerializer,
    WorkflowExecutionListSerializer,
    WorkflowExecutionSerializer,
    WorkflowGoalSerializer,
    WorkflowListSerializer,
    WorkflowNodeSerializer,
    WorkflowSerializer,
    WorkflowTriggerSerializer,
)


class WorkflowViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Workflow management (AUTO-1, AUTO-4).

    Workflows represent visual automation workflows with triggers, nodes, and actions.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Workflow
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at", "activated_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Use lightweight serializer for list views."""
        if self.action == "list":
            return WorkflowListSerializer
        return WorkflowSerializer

    def get_queryset(self):
        """Annotate queryset with counts for list views."""
        queryset = super().get_queryset()

        if self.action == "list":
            queryset = queryset.annotate(
                trigger_count=Count("triggers", distinct=True),
                node_count=Count("nodes", distinct=True),
                execution_count=Count("executions", distinct=True),
            )
        elif self.action == "retrieve":
            # Prefetch related objects for detail view
            edge_prefetch = Prefetch(
                "edges",
                queryset=WorkflowEdge.objects.select_related("source_node", "target_node"),
            )
            goal_prefetch = Prefetch(
                "goals",
                queryset=WorkflowGoal.objects.select_related("goal_node"),
            )
            queryset = queryset.prefetch_related(
                "triggers",
                "nodes",
                edge_prefetch,
                goal_prefetch,
            )

        return queryset

    def perform_create(self, serializer):
        """Set firm and created_by on creation."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """
        Activate this workflow.

        Validates workflow configuration and sets status to active.
        """
        workflow = self.get_object()

        try:
            workflow.activate(user=request.user)
            serializer = self.get_serializer(workflow)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        """Pause this workflow."""
        workflow = self.get_object()
        workflow.pause(user=request.user)
        serializer = self.get_serializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """
        Create a duplicate of this workflow.

        Creates a new draft workflow with copied configuration.
        """
        workflow = self.get_object()

        # Create new workflow
        new_workflow = Workflow.objects.create(
            firm=workflow.firm,
            name=f"{workflow.name} (Copy)",
            description=workflow.description,
            status="draft",
            version=1,
            canvas_data=workflow.canvas_data,
            created_by=request.user,
            updated_by=request.user,
        )

        # Copy triggers
        for trigger in workflow.triggers.all():
            WorkflowTrigger.objects.create(
                firm=trigger.firm,
                workflow=new_workflow,
                trigger_type=trigger.trigger_type,
                configuration=trigger.configuration,
                filter_conditions=trigger.filter_conditions,
                is_active=False,  # Start inactive
            )

        # Copy nodes
        node_mapping = {}
        for node in workflow.nodes.all():
            new_node = WorkflowNode.objects.create(
                firm=node.firm,
                workflow=new_workflow,
                node_id=node.node_id,
                node_type=node.node_type,
                label=node.label,
                position_x=node.position_x,
                position_y=node.position_y,
                configuration=node.configuration,
            )
            node_mapping[node.id] = new_node

        # Copy edges
        for edge in workflow.edges.all():
            WorkflowEdge.objects.create(
                firm=edge.firm,
                workflow=new_workflow,
                source_node=node_mapping[edge.source_node_id],
                target_node=node_mapping[edge.target_node_id],
                condition_type=edge.condition_type,
                condition_config=edge.condition_config,
                label=edge.label,
            )

        # Copy goals
        for goal in workflow.goals.all():
            WorkflowGoal.objects.create(
                firm=goal.firm,
                workflow=new_workflow,
                name=goal.name,
                description=goal.description,
                goal_node=node_mapping[goal.goal_node_id],
                goal_value=goal.goal_value,
                tracking_window_days=goal.tracking_window_days,
            )

        serializer = self.get_serializer(new_workflow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        """
        Get analytics for this workflow.

        Returns latest analytics or generates on-demand.
        """
        workflow = self.get_object()

        # Get latest analytics
        analytics = WorkflowAnalytics.objects.filter(
            firm=workflow.firm,
            workflow=workflow,
        ).order_by("-period_end").first()

        if analytics:
            serializer = WorkflowAnalyticsSerializer(analytics)
            return Response(serializer.data)
        else:
            return Response(
                {"message": "No analytics available yet"},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(detail=True, methods=["get"])
    def executions(self, request, pk=None):
        """Get recent executions for this workflow."""
        workflow = self.get_object()

        executions = WorkflowExecution.objects.filter(
            firm=workflow.firm,
            workflow=workflow,
        ).order_by("-started_at")[:100]

        serializer = WorkflowExecutionListSerializer(executions, many=True)
        return Response(serializer.data)


class WorkflowTriggerViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WorkflowTrigger management (AUTO-2).

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = WorkflowTrigger
    serializer_class = WorkflowTriggerSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["workflow", "trigger_type", "is_active"]
    ordering_fields = ["created_at"]
    ordering = ["workflow", "trigger_type"]

    def perform_create(self, serializer):
        """Set firm on creation."""
        serializer.save(firm=self.request.firm)


class WorkflowNodeViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WorkflowNode management (AUTO-3, AUTO-4).

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = WorkflowNode
    serializer_class = WorkflowNodeSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["workflow", "node_type"]
    ordering_fields = ["position_x", "position_y"]
    ordering = ["workflow", "position_y", "position_x"]

    def perform_create(self, serializer):
        """Set firm on creation."""
        serializer.save(firm=self.request.firm)


class WorkflowEdgeViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WorkflowEdge management (AUTO-4).

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = WorkflowEdge
    serializer_class = WorkflowEdgeSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["workflow", "source_node", "target_node"]
    ordering = ["workflow", "source_node"]

    def perform_create(self, serializer):
        """Set firm on creation."""
        serializer.save(firm=self.request.firm)


class WorkflowExecutionViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WorkflowExecution management (AUTO-5).

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = WorkflowExecution
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["workflow", "contact", "status", "goal_reached"]
    ordering_fields = ["started_at", "completed_at"]
    ordering = ["-started_at"]

    def get_serializer_class(self):
        """Use lightweight serializer for list views."""
        if self.action == "list":
            return WorkflowExecutionListSerializer
        return WorkflowExecutionSerializer

    def get_queryset(self):
        """Prefetch related objects for detail view."""
        queryset = super().get_queryset()

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "flow_states",
                "flow_states__node",
            )

        return queryset

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel this execution."""
        execution = self.get_object()

        if execution.status in ["completed", "goal_reached", "canceled"]:
            return Response(
                {"error": "Cannot cancel completed or already canceled execution"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution.status = "canceled"
        execution.completed_at = timezone.now()
        execution.save()

        serializer = self.get_serializer(execution)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        """
        Retry a failed execution.

        Creates a new execution with same configuration.
        """
        execution = self.get_object()

        if execution.status != "failed":
            return Response(
                {"error": "Can only retry failed executions"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create new execution
        new_execution = WorkflowExecution.objects.create(
            firm=execution.firm,
            workflow=execution.workflow,
            workflow_version=execution.workflow.version,
            contact=execution.contact,
            trigger_type=execution.trigger_type,
            trigger_data=execution.trigger_data,
            context_data=execution.context_data,
            idempotency_key=WorkflowExecution.compute_idempotency_key(
                execution.firm_id,
                execution.workflow_id,
                execution.contact_id,
                execution.trigger_type,
                discriminator=f"retry-{timezone.now().timestamp()}",
            ),
        )

        serializer = self.get_serializer(new_execution)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def flow_visualization(self, request, pk=None):
        """
        Get flow visualization data for this execution.

        Returns node visit information for visualization.
        """
        execution = self.get_object()

        flow_states = ContactFlowState.objects.filter(
            firm=execution.firm,
            execution=execution,
        ).select_related("node")

        serializer = ContactFlowStateSerializer(flow_states, many=True)
        return Response(serializer.data)


class WorkflowGoalViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WorkflowGoal management (AUTO-6).

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = WorkflowGoal
    serializer_class = WorkflowGoalSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["workflow"]
    ordering_fields = ["name", "total_conversions", "conversion_rate"]
    ordering = ["workflow", "name"]

    def perform_create(self, serializer):
        """Set firm on creation."""
        serializer.save(firm=self.request.firm)

    @action(detail=True, methods=["post"])
    def update_analytics(self, request, pk=None):
        """Recalculate analytics for this goal."""
        goal = self.get_object()
        goal.update_analytics()
        serializer = self.get_serializer(goal)
        return Response(serializer.data)


class WorkflowAnalyticsViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for WorkflowAnalytics (AUTO-6).

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = WorkflowAnalytics
    serializer_class = WorkflowAnalyticsSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["workflow"]
    ordering_fields = ["period_start", "period_end", "calculated_at"]
    ordering = ["-period_end"]

    http_method_names = ["get", "head", "options"]  # Read-only

    def get_queryset(self):
        """Prefetch workflow details."""
        queryset = super().get_queryset()
        return queryset.select_related("workflow")
