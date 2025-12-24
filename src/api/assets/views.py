"""
DRF ViewSets for Assets module.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from modules.assets.models import Asset, MaintenanceLog
from modules.firm.viewsets import FirmScopedViewSetMixin
from .serializers import AssetSerializer, MaintenanceLogSerializer


class AssetViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Asset model."""
    queryset = Asset.objects.select_related('assigned_to')
    serializer_class = AssetSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'assigned_to']
    search_fields = ['asset_tag', 'name', 'serial_number', 'manufacturer']
    ordering_fields = ['asset_tag', 'name', 'purchase_date']
    ordering = ['-created_at']


class MaintenanceLogViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for MaintenanceLog model."""
    queryset = MaintenanceLog.objects.select_related('asset', 'created_by')
    serializer_class = MaintenanceLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset', 'maintenance_type', 'status']
    search_fields = ['asset__asset_tag', 'asset__name', 'description']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['-scheduled_date', '-created_at']
