"""
URL Configuration for Firm Module.

Provides break-glass session management, firm-level operations, and user profiles.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.firm.views import AuditEventViewSet, BreakGlassStatusViewSet, FirmOffboardingViewSet
from modules.firm.profile_views import UserProfileViewSet

router = DefaultRouter()
router.register(r"break-glass", BreakGlassStatusViewSet, basename="break-glass")
router.register(r"offboarding", FirmOffboardingViewSet, basename="firm-offboarding")
router.register(r"audit-events", AuditEventViewSet, basename="audit-events")
router.register(r"profiles", UserProfileViewSet, basename="user-profile")

urlpatterns = [
    path("", include(router.urls)),
]
