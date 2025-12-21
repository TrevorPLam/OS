"""
URL routes for Clients module API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from modules.clients.views import (
    ClientViewSet,
    ClientPortalUserViewSet,
    ClientNoteViewSet,
    ClientEngagementViewSet,
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'portal-users', ClientPortalUserViewSet, basename='portaluser')
router.register(r'notes', ClientNoteViewSet, basename='clientnote')
router.register(r'engagements', ClientEngagementViewSet, basename='engagement')

urlpatterns = [
    path('', include(router.urls)),
]
