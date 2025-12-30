"""Knowledge System URLs (DOC-35.1)."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    KnowledgeItemViewSet,
    KnowledgeVersionViewSet,
    KnowledgeReviewViewSet,
    KnowledgeAttachmentViewSet,
)

router = DefaultRouter()
router.register(r"items", KnowledgeItemViewSet, basename="knowledge-item")
router.register(r"versions", KnowledgeVersionViewSet, basename="knowledge-version")
router.register(r"reviews", KnowledgeReviewViewSet, basename="knowledge-review")
router.register(r"attachments", KnowledgeAttachmentViewSet, basename="knowledge-attachment")

urlpatterns = [
    path("", include(router.urls)),
]
