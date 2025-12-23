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

urlpatterns = [
    path('', include(router.urls)),
]
