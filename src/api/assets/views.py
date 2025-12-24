"""
DRF ViewSets for Assets module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes. for automatic tenant isolation.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from modules.assets.models import Asset, MaintenanceLog
from modules.firm.utils import FirmScopedMixin
from .serializers import AssetSerializer, MaintenanceLogSerializer


class AssetViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Asset model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Asset
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]  # TIER 2: Explicit permissions
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'assigned_to']
    search_fields = ['asset_tag', 'name', 'serial_number', 'manufacturer']
    ordering_fields = ['asset_tag', 'name', 'purchase_date']
    ordering = ['-created_at']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('assigned_to')


class MaintenanceLogViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for MaintenanceLog model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = MaintenanceLog
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsAuthenticated]  # TIER 2: Explicit permissions
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset', 'maintenance_type', 'status']
    search_fields = ['description']
    ordering_fields = ['scheduled_date', 'created_at']
    ordering = ['-scheduled_date', '-created_at']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('asset', 'created_by')
