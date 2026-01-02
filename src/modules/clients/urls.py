"""
URL routes for Clients module API.

TIER 2.6: Added Organization ViewSet for cross-client collaboration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.clients.portal_views import (
    DomainVerificationRecordViewSet,
    PortalBrandingViewSet,
)
from modules.clients.views import (
    ClientChatThreadViewSet,
    ClientCommentViewSet,
    ClientContractViewSet,
    ClientEngagementHistoryViewSet,
    ClientEngagementViewSet,
    ClientInvoiceViewSet,
    ClientMessageViewSet,
    ClientNoteViewSet,
    ClientPortalUserViewSet,
    ClientProjectViewSet,
    ClientProposalViewSet,
    ClientViewSet,
    OrganizationViewSet,
)

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")  # TIER 2.6
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"portal-users", ClientPortalUserViewSet, basename="portaluser")
router.register(r"notes", ClientNoteViewSet, basename="clientnote")
router.register(r"engagements", ClientEngagementViewSet, basename="engagement")
router.register(r"projects", ClientProjectViewSet, basename="client-project")
router.register(r"comments", ClientCommentViewSet, basename="client-comment")
router.register(r"invoices", ClientInvoiceViewSet, basename="client-invoice")
router.register(r"chat-threads", ClientChatThreadViewSet, basename="client-chat-thread")
router.register(r"messages", ClientMessageViewSet, basename="client-message")
router.register(r"proposals", ClientProposalViewSet, basename="client-proposal")
router.register(r"contracts", ClientContractViewSet, basename="client-contract")
router.register(r"engagement-history", ClientEngagementHistoryViewSet, basename="client-engagement-history")
# Portal Branding (PORTAL-1 through PORTAL-4)
router.register(r"portal-branding", PortalBrandingViewSet, basename="portal-branding")
router.register(r"domain-verification", DomainVerificationRecordViewSet, basename="domain-verification")

urlpatterns = [
    path("", include(router.urls)),
]
