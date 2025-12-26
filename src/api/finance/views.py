"""
DRF ViewSets for Finance module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.finance.models import Bill, Invoice, LedgerEntry
from modules.firm.utils import FirmScopedMixin

from .serializers import BillSerializer, InvoiceSerializer, LedgerEntrySerializer


class InvoiceViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Invoice model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Invoice
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["client", "project", "status"]
    search_fields = ["invoice_number"]
    ordering_fields = ["invoice_number", "issue_date", "due_date"]
    ordering = ["-issue_date", "-created_at"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("client", "project", "created_by")


class BillViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Bill model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Bill
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "expense_category", "project"]
    search_fields = ["reference_number", "bill_number", "vendor_name"]
    ordering_fields = ["reference_number", "bill_date", "due_date"]
    ordering = ["-bill_date", "-created_at"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("project", "approved_by")


class LedgerEntryViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for LedgerEntry model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = LedgerEntry
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["entry_type", "account", "transaction_group_id"]
    search_fields = ["description", "transaction_group_id"]
    ordering_fields = ["transaction_date", "created_at"]
    ordering = ["-transaction_date", "-created_at"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("invoice", "bill", "created_by")
