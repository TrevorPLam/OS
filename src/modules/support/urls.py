"""URL configuration for support API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SLAPolicyViewSet,
    TicketViewSet,
    TicketCommentViewSet,
    SurveyViewSet,
    SurveyResponseViewSet,
)

router = DefaultRouter()
router.register(r"sla-policies", SLAPolicyViewSet, basename="sla-policy")
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"ticket-comments", TicketCommentViewSet, basename="ticket-comment")
router.register(r"surveys", SurveyViewSet, basename="survey")
router.register(r"survey-responses", SurveyResponseViewSet, basename="survey-response")

urlpatterns = [
    path("", include(router.urls)),
]
