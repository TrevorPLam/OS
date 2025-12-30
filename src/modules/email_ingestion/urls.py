"""URL configuration for email ingestion API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"connections", views.EmailConnectionViewSet, basename="email-connection")
router.register(r"artifacts", views.EmailArtifactViewSet, basename="email-artifact")
router.register(r"attempts", views.IngestionAttemptViewSet, basename="ingestion-attempt")

urlpatterns = [
    path("", include(router.urls)),
]
