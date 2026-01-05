from django.urls import path
from rest_framework.routers import DefaultRouter

from modules.tracking.views import TrackingEventViewSet, TrackingIngestView, TrackingSessionViewSet, TrackingSummaryView

router = DefaultRouter()
router.register(r"events", TrackingEventViewSet, basename="tracking-event")
router.register(r"sessions", TrackingSessionViewSet, basename="tracking-session")

urlpatterns = [
    path("collect/", TrackingIngestView.as_view(), name="tracking-collect"),
    path("summary/", TrackingSummaryView.as_view(), name="tracking-summary"),
]

urlpatterns += router.urls
