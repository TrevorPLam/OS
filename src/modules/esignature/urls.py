"""URL configuration for e-signature module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.esignature import views

router = DefaultRouter()
router.register(r"connections", views.DocuSignConnectionViewSet, basename="docusign-connection")
router.register(r"envelopes", views.EnvelopeViewSet, basename="envelope")
router.register(r"webhook-events", views.WebhookEventViewSet, basename="webhook-event")

urlpatterns = [
    # OAuth flow (in API v1)
    path("docusign/connect/", views.docusign_connect, name="docusign-connect"),
    path("docusign/callback/", views.docusign_callback, name="docusign-callback"),
    
    # Webhook endpoint (accessed directly at /webhooks/docusign/)
    path("webhook/", views.docusign_webhook, name="docusign-webhook"),
    
    # ViewSets (in API v1)
    path("", include(router.urls)),
]
