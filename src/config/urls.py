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

# ASSESS-I5.1: API Versioning - All API endpoints use /api/v1/ prefix
# Version support policy: See docs/API_VERSIONING_POLICY.md

# API v1 endpoints (current stable version)
api_v1_patterns = [
    # API Endpoints (REST Framework)
    path("auth/", include("modules.auth.urls")),
    path("firm/", include("modules.firm.urls")),
    # TIER 0: Client Portal (portal users ONLY - default-deny)
    path("portal/", include("api.portal.urls")),
    # Firm Admin Endpoints (portal users BLOCKED)
    path("crm/", include("api.crm.urls")),  # Pre-sale: Leads, Prospects, Campaigns, Proposals
    path("clients/", include("api.clients.urls")),  # Post-sale: Client management & firm-only views
    path("projects/", include("api.projects.urls")),
    path("finance/", include("api.finance.urls")),
    path("documents/", include("api.documents.urls")),
    path("assets/", include("api.assets.urls")),
    path("pricing/", include("modules.pricing.urls")),  # DOC-09.2: Pricing engine endpoints
    path("calendar/", include("modules.calendar.urls")),  # DOC-16.1, DOC-34.1: Calendar and booking
    path("email-ingestion/", include("modules.email_ingestion.urls")),  # DOC-15.1: Email ingestion admin
    path("communications/", include("modules.communications.urls")),  # DOC-33.1: Conversations and messages
    path("knowledge/", include("modules.knowledge.urls")),  # DOC-35.1: Knowledge system
    path("support/", include("modules.support.urls")),  # Support/ticketing system (SLA, surveys, NPS)
    path("onboarding/", include("modules.onboarding.urls")),  # Client onboarding workflows
    path("marketing/", include("modules.marketing.urls")),  # Marketing automation (tags, segments, templates)
    path("snippets/", include("modules.snippets.urls")),  # Quick text insertion (HubSpot-style snippets)
    path("sms/", include("modules.sms.urls")),  # SMS messaging (Twilio integration, campaigns, conversations)
    path("webhooks/", include("api.webhooks.urls")),  # General webhook platform (Task 3.7)
    path("accounting/", include("modules.accounting_integrations.urls")),  # Sprint 3: QuickBooks/Xero integrations
]

urlpatterns = [
    # Root: redirect to API docs for a friendly default landing
    path("", RedirectView.as_view(url="/api/docs/", permanent=False), name="root"),
    # Health check endpoints (for load balancers and Kubernetes probes)
    path("health/", health_check, name="health_check"),
    path("health/ready/", readiness_check, name="readiness_check"),
    # Django Admin
    path("admin/", admin.site.urls),
    # API Documentation (versioned)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Webhooks (not versioned - webhook URLs should remain stable)
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    # API v1 (current stable version)
    path("api/v1/", include(api_v1_patterns)),
    # Legacy API endpoints (redirect to v1 for backward compatibility during transition)
    # TODO: Remove legacy endpoints after frontend migration (ASSESS-I5.9)
    path("api/auth/", RedirectView.as_view(url="/api/v1/auth/", permanent=False)),
    path("api/firm/", RedirectView.as_view(url="/api/v1/firm/", permanent=False)),
    path("api/portal/", RedirectView.as_view(url="/api/v1/portal/", permanent=False)),
    path("api/crm/", RedirectView.as_view(url="/api/v1/crm/", permanent=False)),
    path("api/clients/", RedirectView.as_view(url="/api/v1/clients/", permanent=False)),
    path("api/projects/", RedirectView.as_view(url="/api/v1/projects/", permanent=False)),
    path("api/finance/", RedirectView.as_view(url="/api/v1/finance/", permanent=False)),
    path("api/documents/", RedirectView.as_view(url="/api/v1/documents/", permanent=False)),
    path("api/assets/", RedirectView.as_view(url="/api/v1/assets/", permanent=False)),
    path("api/pricing/", RedirectView.as_view(url="/api/v1/pricing/", permanent=False)),
    path("api/calendar/", RedirectView.as_view(url="/api/v1/calendar/", permanent=False)),
    path("api/email-ingestion/", RedirectView.as_view(url="/api/v1/email-ingestion/", permanent=False)),
    path("api/communications/", RedirectView.as_view(url="/api/v1/communications/", permanent=False)),
    path("api/knowledge/", RedirectView.as_view(url="/api/v1/knowledge/", permanent=False)),
    path("api/support/", RedirectView.as_view(url="/api/v1/support/", permanent=False)),
    path("api/onboarding/", RedirectView.as_view(url="/api/v1/onboarding/", permanent=False)),
    path("api/marketing/", RedirectView.as_view(url="/api/v1/marketing/", permanent=False)),
    path("api/snippets/", RedirectView.as_view(url="/api/v1/snippets/", permanent=False)),
    path("api/sms/", RedirectView.as_view(url="/api/v1/sms/", permanent=False)),
    path("api/webhooks/", RedirectView.as_view(url="/api/v1/webhooks/", permanent=False)),
    path("api/accounting/", RedirectView.as_view(url="/api/v1/accounting/", permanent=False)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
