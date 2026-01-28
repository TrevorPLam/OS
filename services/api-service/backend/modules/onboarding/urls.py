"""URL configuration for onboarding API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OnboardingTemplateViewSet,
    OnboardingProcessViewSet,
    OnboardingTaskViewSet,
    OnboardingDocumentViewSet,
)

router = DefaultRouter()
router.register(r"templates", OnboardingTemplateViewSet, basename="onboarding-template")
router.register(r"processes", OnboardingProcessViewSet, basename="onboarding-process")
router.register(r"tasks", OnboardingTaskViewSet, basename="onboarding-task")
router.register(r"documents", OnboardingDocumentViewSet, basename="onboarding-document")

urlpatterns = [
    path("", include(router.urls)),
]
