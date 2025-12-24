"""
Platform API URLs (TIER 0.6).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import BreakGlassViewSet, AuditEventViewSet


router = DefaultRouter()
router.register(r'break-glass', BreakGlassViewSet, basename='break-glass')
router.register(r'audit-events', AuditEventViewSet, basename='audit-events')

urlpatterns = [
    path('', include(router.urls)),
]
