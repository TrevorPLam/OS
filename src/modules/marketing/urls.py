"""URL configuration for marketing API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TagViewSet,
    SegmentViewSet,
    EmailTemplateViewSet,
    CampaignExecutionViewSet,
    EntityTagViewSet,
)

router = DefaultRouter()
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"segments", SegmentViewSet, basename="segment")
router.register(r"email-templates", EmailTemplateViewSet, basename="email-template")
router.register(r"campaign-executions", CampaignExecutionViewSet, basename="campaign-execution")
router.register(r"entity-tags", EntityTagViewSet, basename="entity-tag")

urlpatterns = [
    path("", include(router.urls)),
]
