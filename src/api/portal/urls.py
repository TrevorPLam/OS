"""
Client Portal API URLs (TIER 0: Task 0.4).

This is the ONLY namespace that portal users can access.
All endpoints here are portal-specific and client-scoped.

TIER 0: Portal containment - explicit allowlist.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from modules.clients.views import (
    ClientProjectViewSet,
    ClientCommentViewSet,
    ClientInvoiceViewSet,
    ClientChatThreadViewSet,
    ClientMessageViewSet,
    ClientProposalViewSet,
    ClientContractViewSet,
    ClientEngagementHistoryViewSet,
)

# TIER 0: Portal router - ONLY portal-accessible endpoints
portal_router = DefaultRouter()

# Client Portal Endpoints (Read-only for most)
portal_router.register(r'projects', ClientProjectViewSet, basename='portal-project')
portal_router.register(r'comments', ClientCommentViewSet, basename='portal-comment')
portal_router.register(r'invoices', ClientInvoiceViewSet, basename='portal-invoice')
portal_router.register(r'chat-threads', ClientChatThreadViewSet, basename='portal-chat-thread')
portal_router.register(r'messages', ClientMessageViewSet, basename='portal-message')
portal_router.register(r'proposals', ClientProposalViewSet, basename='portal-proposal')
portal_router.register(r'contracts', ClientContractViewSet, basename='portal-contract')
portal_router.register(r'engagement-history', ClientEngagementHistoryViewSet, basename='portal-engagement-history')

urlpatterns = [
    path('', include(portal_router.urls)),
]
