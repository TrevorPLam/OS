"""URL configuration for e-signature module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.esignature import views

router = DefaultRouter()
router.register(r"connections", views.DocuSignConnectionViewSet, basename="docusign-connection")
router.register(r"envelopes", views.EnvelopeViewSet, basename="envelope")
router.register(r"webhook-events", views.WebhookEventViewSet, basename="webhook-event")

urlpatterns = [
    # OAuth flow
    path("docusign/connect/", views.docusign_connect, name="docusign-connect"),
    path("docusign/callback/", views.docusign_callback, name="docusign-callback"),
    
    # Webhook endpoint
    path("docusign/webhook/", views.docusign_webhook, name="docusign-webhook"),
    
    # ViewSets
    path("", include(router.urls)),
]
