from django.urls import path
from rest_framework.routers import DefaultRouter

from modules.integrations.views import (
    GoogleAnalyticsConfigViewSet,
    SalesforceConnectionViewSet,
    SlackIntegrationViewSet,
)

router = DefaultRouter()
router.register(r"salesforce", SalesforceConnectionViewSet, basename="salesforce-connection")
router.register(r"slack", SlackIntegrationViewSet, basename="slack-integration")
router.register(r"google-analytics", GoogleAnalyticsConfigViewSet, basename="google-analytics")

urlpatterns = [] + router.urls
