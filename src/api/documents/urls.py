"""
URL routes for Documents API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, FolderViewSet, VersionViewSet

router = DefaultRouter()
router.register(r"folders", FolderViewSet, basename="folder")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"versions", VersionViewSet, basename="version")

urlpatterns = [
    path("", include(router.urls)),
]
