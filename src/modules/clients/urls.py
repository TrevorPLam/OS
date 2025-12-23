"""
URL routes for Clients module API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from modules.clients.views import (
    ClientViewSet,
    ClientPortalUserViewSet,
    ClientNoteViewSet,
    ClientEngagementViewSet,
    ClientProjectViewSet,
    ClientCommentViewSet,
    ClientInvoiceViewSet,
    ClientChatThreadViewSet,
    ClientMessageViewSet,
    ClientProposalViewSet,
    ClientContractViewSet,
    ClientEngagementHistoryViewSet,
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'portal-users', ClientPortalUserViewSet, basename='portaluser')
router.register(r'notes', ClientNoteViewSet, basename='clientnote')
router.register(r'engagements', ClientEngagementViewSet, basename='engagement')
router.register(r'projects', ClientProjectViewSet, basename='client-project')
router.register(r'comments', ClientCommentViewSet, basename='client-comment')
router.register(r'invoices', ClientInvoiceViewSet, basename='client-invoice')
router.register(r'chat-threads', ClientChatThreadViewSet, basename='client-chat-thread')
router.register(r'messages', ClientMessageViewSet, basename='client-message')
router.register(r'proposals', ClientProposalViewSet, basename='client-proposal')
router.register(r'contracts', ClientContractViewSet, basename='client-contract')
router.register(r'engagement-history', ClientEngagementHistoryViewSet, basename='client-engagement-history')

urlpatterns = [
    path('', include(router.urls)),
]
