"""
URL routes for Clients API (Post-Sale).

Clients module handles all post-sale client management,
including portal access and engagements.
"""

from django.urls import include, path

# Use the Clients module's URL configuration
urlpatterns = [
    path("", include("modules.clients.urls")),
]
