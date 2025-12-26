"""
URL Configuration for ConsultantPro.

Organized by business domain modules.
"""

from api.finance.webhooks import stripe_webhook
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Webhooks
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
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
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
