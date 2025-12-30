"""SMS module URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SMSPhoneNumberViewSet,
    SMSTemplateViewSet,
    SMSMessageViewSet,
    SMSCampaignViewSet,
    SMSConversationViewSet,
    SMSOptOutViewSet,
)
from .webhooks import twilio_status_webhook, twilio_inbound_webhook

# Create router and register viewsets
router = DefaultRouter()
router.register(r'phone-numbers', SMSPhoneNumberViewSet, basename='sms-phone-number')
router.register(r'templates', SMSTemplateViewSet, basename='sms-template')
router.register(r'messages', SMSMessageViewSet, basename='sms-message')
router.register(r'campaigns', SMSCampaignViewSet, basename='sms-campaign')
router.register(r'conversations', SMSConversationViewSet, basename='sms-conversation')
router.register(r'opt-outs', SMSOptOutViewSet, basename='sms-optout')

# URL patterns
urlpatterns = [
    # API endpoints (mounted at /api/sms/ in main urls.py)
    path('', include(router.urls)),

    # Webhooks (no authentication required - Twilio callbacks)
    # These will be at /api/sms/webhooks/...
    path('webhooks/status/', twilio_status_webhook, name='twilio-status-webhook'),
    path('webhooks/inbound/', twilio_inbound_webhook, name='twilio-inbound-webhook'),
]
