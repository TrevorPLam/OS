"""
URL Configuration for ConsultantPro.

Organized by business domain modules.
"""

from api.finance.webhooks import stripe_webhook
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .health import health_check, readiness_check

urlpatterns = [
    # Root: redirect to API docs for a friendly default landing
    path("", RedirectView.as_view(url="/api/docs/", permanent=False), name="root"),
    # Health check endpoints (for load balancers and Kubernetes probes)
    path("health/", health_check, name="health_check"),
    path("health/ready/", readiness_check, name="readiness_check"),
    # Django Admin
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Webhooks
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    path("webhooks/sms/", include("modules.sms.webhooks")),  # Twilio SMS webhooks (no auth)
    # API Endpoints (REST Framework)
    path("api/auth/", include("modules.auth.urls")),
    path("api/firm/", include("modules.firm.urls")),
    # TIER 0: Client Portal (portal users ONLY - default-deny)
    path("api/portal/", include("api.portal.urls")),
    # Firm Admin Endpoints (portal users BLOCKED)
    path("api/crm/", include("api.crm.urls")),  # Pre-sale: Leads, Prospects, Campaigns, Proposals
    path("api/clients/", include("api.clients.urls")),  # Post-sale: Client management & firm-only views
    path("api/projects/", include("api.projects.urls")),
    path("api/finance/", include("api.finance.urls")),
    path("api/documents/", include("api.documents.urls")),
    path("api/assets/", include("api.assets.urls")),
    path("api/pricing/", include("modules.pricing.urls")),  # DOC-09.2: Pricing engine endpoints
    path("api/calendar/", include("modules.calendar.urls")),  # DOC-16.1, DOC-34.1: Calendar and booking
    path("api/email-ingestion/", include("modules.email_ingestion.urls")),  # DOC-15.1: Email ingestion admin
    path("api/communications/", include("modules.communications.urls")),  # DOC-33.1: Conversations and messages
    path("api/knowledge/", include("modules.knowledge.urls")),  # DOC-35.1: Knowledge system
    path("api/support/", include("modules.support.urls")),  # Support/ticketing system (SLA, surveys, NPS)
    path("api/onboarding/", include("modules.onboarding.urls")),  # Client onboarding workflows
    path("api/marketing/", include("modules.marketing.urls")),  # Marketing automation (tags, segments, templates)
    path("api/snippets/", include("modules.snippets.urls")),  # Quick text insertion (HubSpot-style snippets)
    path("api/sms/", include("modules.sms.urls")),  # SMS messaging (Twilio integration, campaigns, conversations)
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
