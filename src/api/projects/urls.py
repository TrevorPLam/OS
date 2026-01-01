"""
URL routes for Projects API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet,
    ResourceAllocationViewSet,
    ResourceCapacityViewSet,
    TaskViewSet,
    TimeEntryViewSet,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"time-entries", TimeEntryViewSet, basename="timeentry")
router.register(r"resource-allocations", ResourceAllocationViewSet, basename="resource-allocation")
router.register(r"resource-capacities", ResourceCapacityViewSet, basename="resource-capacity")

urlpatterns = [
    path("", include(router.urls)),
]
