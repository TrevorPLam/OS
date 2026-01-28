"""URL configuration for automation workflows."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    WorkflowAnalyticsViewSet,
    WorkflowEdgeViewSet,
    WorkflowExecutionViewSet,
    WorkflowGoalViewSet,
    WorkflowNodeViewSet,
    WorkflowTriggerViewSet,
    WorkflowViewSet,
)

router = DefaultRouter()
router.register(r"workflows", WorkflowViewSet, basename="workflow")
router.register(r"triggers", WorkflowTriggerViewSet, basename="workflow-trigger")
router.register(r"nodes", WorkflowNodeViewSet, basename="workflow-node")
router.register(r"edges", WorkflowEdgeViewSet, basename="workflow-edge")
router.register(r"executions", WorkflowExecutionViewSet, basename="workflow-execution")
router.register(r"goals", WorkflowGoalViewSet, basename="workflow-goal")
router.register(r"analytics", WorkflowAnalyticsViewSet, basename="workflow-analytics")

urlpatterns = [
    path("", include(router.urls)),
]
