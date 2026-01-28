"""
URL routes for Projects API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectTimelineViewSet,
    ProjectViewSet,
    ResourceAllocationViewSet,
    ResourceCapacityViewSet,
    TaskDependencyViewSet,
    TaskScheduleViewSet,
    TaskViewSet,
    TimeEntryViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"time-entries", TimeEntryViewSet, basename="timeentry")
router.register(r"resource-allocations", ResourceAllocationViewSet, basename="resource-allocation")
router.register(r"resource-capacities", ResourceCapacityViewSet, basename="resource-capacity")
router.register(r"project-timelines", ProjectTimelineViewSet, basename="project-timeline")
router.register(r"task-schedules", TaskScheduleViewSet, basename="task-schedule")
router.register(r"task-dependencies", TaskDependencyViewSet, basename="task-dependency")

urlpatterns = [
    path("", include(router.urls)),
]
