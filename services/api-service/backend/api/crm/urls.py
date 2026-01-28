"""
URL routes for CRM API (Pre-Sale: Marketing & Sales).

UPDATED: Clients moved to /api/clients/ (Post-Sale module)
CRM now handles: Leads, Prospects, Campaigns, Proposals, Contracts
"""

from django.urls import include, path

# Use the CRM module's URL configuration
urlpatterns = [
    path("", include("modules.crm.urls")),
]
