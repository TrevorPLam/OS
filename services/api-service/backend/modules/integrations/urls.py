from django.urls import path
from rest_framework.routers import DefaultRouter

from modules.integrations.views import (
    GoogleAnalyticsConfigViewSet,
    IntegrationHealthView,
    SalesforceConnectionViewSet,
    SlackIntegrationViewSet,
)

router = DefaultRouter()
router.register(r"salesforce", SalesforceConnectionViewSet, basename="salesforce-connection")
router.register(r"slack", SlackIntegrationViewSet, basename="slack-integration")
router.register(r"google-analytics", GoogleAnalyticsConfigViewSet, basename="google-analytics")

urlpatterns = [
    path("health/", IntegrationHealthView.as_view(), name="integration-health"),
]

urlpatterns += router.urls
