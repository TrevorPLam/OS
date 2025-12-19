"""
DRF ViewSets for Documents module.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from modules.documents.models import Folder, Document, Version
from .serializers import FolderSerializer, DocumentSerializer, VersionSerializer


class FolderViewSet(viewsets.ModelViewSet):
    """ViewSet for Folder model."""
    queryset = Folder.objects.select_related('client', 'project', 'parent', 'created_by')
    serializer_class = FolderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'project', 'parent', 'visibility']
    search_fields = ['name', 'client__company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for Document model."""
    queryset = Document.objects.select_related('folder', 'client', 'project', 'uploaded_by')
    serializer_class = DocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'folder', 'project', 'visibility', 'file_type']
    search_fields = ['name', 'client__company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']


class VersionViewSet(viewsets.ModelViewSet):
    """ViewSet for Version model."""
    queryset = Version.objects.select_related('document', 'uploaded_by')
    serializer_class = VersionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document']
    search_fields = ['document__name', 'change_summary']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']
