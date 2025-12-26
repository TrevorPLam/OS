"""
URL routes for Assets API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, MaintenanceLogViewSet

router = DefaultRouter()
router.register(r"assets", AssetViewSet, basename="asset")
router.register(r"maintenance-logs", MaintenanceLogViewSet, basename="maintenancelog")

urlpatterns = [
    path("", include(router.urls)),
]
