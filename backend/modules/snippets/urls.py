"""URL configuration for snippets API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SnippetViewSet,
    SnippetUsageLogViewSet,
    SnippetFolderViewSet,
)

router = DefaultRouter()
router.register(r'snippets', SnippetViewSet, basename='snippet')
router.register(r'snippet-usage-logs', SnippetUsageLogViewSet, basename='snippet-usage-log')
router.register(r'snippet-folders', SnippetFolderViewSet, basename='snippet-folder')

urlpatterns = [
    path('', include(router.urls)),
]
