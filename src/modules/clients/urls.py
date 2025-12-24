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

management_router = DefaultRouter()
management_router.register(r'clients', ClientViewSet, basename='client')
management_router.register(r'portal-users', ClientPortalUserViewSet, basename='portaluser')
management_router.register(r'notes', ClientNoteViewSet, basename='clientnote')
management_router.register(r'engagements', ClientEngagementViewSet, basename='engagement')

portal_router = DefaultRouter()
portal_router.register(r'projects', ClientProjectViewSet, basename='client-project')
portal_router.register(r'comments', ClientCommentViewSet, basename='client-comment')
portal_router.register(r'invoices', ClientInvoiceViewSet, basename='client-invoice')
portal_router.register(r'chat-threads', ClientChatThreadViewSet, basename='client-chat-thread')
portal_router.register(r'messages', ClientMessageViewSet, basename='client-message')
portal_router.register(r'proposals', ClientProposalViewSet, basename='client-proposal')
portal_router.register(r'contracts', ClientContractViewSet, basename='client-contract')
portal_router.register(r'engagement-history', ClientEngagementHistoryViewSet, basename='client-engagement-history')

urlpatterns = [
    path('', include(management_router.urls)),
    path('portal/', include(portal_router.urls)),
]
