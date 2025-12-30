"""
Client Portal API URLs (TIER 0: Task 0.4, DOC-26.1).

This is the ONLY namespace that portal users can access.
All endpoints here are portal-specific and client-scoped.

TIER 0: Portal containment - explicit allowlist.
DOC-26.1: Implements primary navigation and core flows per docs/26.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.clients.views import (
    ClientChatThreadViewSet,
    ClientCommentViewSet,
    ClientContractViewSet,
    ClientEngagementHistoryViewSet,
    ClientInvoiceViewSet,
    ClientMessageViewSet,
    ClientProjectViewSet,
    ClientProposalViewSet,
)
from .views import (
    PortalHomeViewSet,
    PortalAccountSwitcherViewSet,
    PortalProfileViewSet,
    PortalDocumentViewSet,
    PortalFolderViewSet,
    PortalAppointmentViewSet,
)

# TIER 0: Portal router - ONLY portal-accessible endpoints
portal_router = DefaultRouter()

# DOC-26.1: Primary Navigation
# 1. Home
portal_router.register(r"home", PortalHomeViewSet, basename="portal-home")

# 2. Messages (existing)
portal_router.register(r"chat-threads", ClientChatThreadViewSet, basename="portal-chat-thread")
portal_router.register(r"messages", ClientMessageViewSet, basename="portal-message")

# 3. Documents
portal_router.register(r"documents", PortalDocumentViewSet, basename="portal-document")
portal_router.register(r"folders", PortalFolderViewSet, basename="portal-folder")

# 4. Appointments
portal_router.register(r"appointments", PortalAppointmentViewSet, basename="portal-appointment")

# 5. Billing (existing)
portal_router.register(r"invoices", ClientInvoiceViewSet, basename="portal-invoice")

# 6. Engagements (existing)
portal_router.register(r"projects", ClientProjectViewSet, basename="portal-project")
portal_router.register(r"contracts", ClientContractViewSet, basename="portal-contract")
portal_router.register(r"proposals", ClientProposalViewSet, basename="portal-proposal")
portal_router.register(r"engagement-history", ClientEngagementHistoryViewSet, basename="portal-engagement-history")

# 7. Profile
portal_router.register(r"profile", PortalProfileViewSet, basename="portal-profile")

# Account Switcher (DOC-26.1)
portal_router.register(r"accounts", PortalAccountSwitcherViewSet, basename="portal-account-switcher")

# Legacy endpoints (kept for backward compatibility)
portal_router.register(r"comments", ClientCommentViewSet, basename="portal-comment")

urlpatterns = [
    path("", include(portal_router.urls)),
]
