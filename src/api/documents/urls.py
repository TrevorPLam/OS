"""
URL routes for Documents API.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentViewSet,
    ExternalShareViewSet,
    FolderViewSet,
    ShareAccessViewSet,
    SharePermissionViewSet,
    VersionViewSet,
)

router = DefaultRouter()
router.register(r"folders", FolderViewSet, basename="folder")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"versions", VersionViewSet, basename="version")
router.register(r"external-shares", ExternalShareViewSet, basename="external-share")
router.register(r"share-permissions", SharePermissionViewSet, basename="share-permission")
router.register(r"share-accesses", ShareAccessViewSet, basename="share-access")

urlpatterns = [
    path("", include(router.urls)),
]
