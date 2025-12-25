"""
URL Configuration for Firm Module.

Provides break-glass session management and firm-level operations.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from modules.firm.views import BreakGlassStatusViewSet

router = DefaultRouter()
router.register(r'break-glass', BreakGlassStatusViewSet, basename='break-glass')

urlpatterns = [
    path('', include(router.urls)),
]
