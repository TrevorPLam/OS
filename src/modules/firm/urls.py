"""
URL Configuration for Firm Module.

Provides break-glass session management and firm-level operations.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.firm.views import BreakGlassStatusViewSet, FirmOffboardingViewSet

router = DefaultRouter()
router.register(r"break-glass", BreakGlassStatusViewSet, basename="break-glass")
router.register(r"offboarding", FirmOffboardingViewSet, basename="firm-offboarding")

urlpatterns = [
    path("", include(router.urls)),
]
