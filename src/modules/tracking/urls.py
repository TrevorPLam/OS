from django.urls import path
from rest_framework.routers import DefaultRouter

from modules.tracking.views import (
    SiteMessageViewSet,
    TrackingAnalyticsExportView,
    TrackingEventViewSet,
    TrackingIngestView,
    TrackingKeyViewSet,
    TrackingSessionViewSet,
    TrackingSummaryView,
)

router = DefaultRouter()
router.register(r"events", TrackingEventViewSet, basename="tracking-event")
router.register(r"sessions", TrackingSessionViewSet, basename="tracking-session")
router.register(r"keys", TrackingKeyViewSet, basename="tracking-key")
router.register(r"site-messages", SiteMessageViewSet, basename="site-message")

urlpatterns = [
    path("collect/", TrackingIngestView.as_view(), name="tracking-collect"),
    path("summary/", TrackingSummaryView.as_view(), name="tracking-summary"),
    path("analytics/export/", TrackingAnalyticsExportView.as_view(), name="tracking-analytics-export"),
]

urlpatterns += router.urls
