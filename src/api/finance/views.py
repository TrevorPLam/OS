"""
DRF ViewSets for Finance module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.finance.models import Bill, Invoice, LedgerEntry, Payment, PaymentAllocation, ProjectProfitability, ServiceLineProfitability
from modules.firm.utils import FirmScopedMixin

from .serializers import (
    BillSerializer,
    InvoiceSerializer,
    LedgerEntrySerializer,
    PaymentSerializer,
    PaymentAllocationSerializer,
    ProjectProfitabilitySerializer,
    ServiceLineProfitabilitySerializer,
)


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


class PaymentViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Payment model (Medium Feature 2.10).
    
    Supports cash application matching with partial/over/under payments.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    
    model = Payment
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["client", "status", "payment_method"]
    search_fields = ["payment_number", "reference_number"]
    ordering_fields = ["payment_number", "payment_date", "amount"]
    ordering = ["-payment_date", "-created_at"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("client", "created_by")
    
    @action(detail=True, methods=["post"])
    def allocate(self, request, pk=None):
        """
        Allocate payment to invoice(s) (Medium Feature 2.10).
        
        POST /api/finance/payments/{id}/allocate/
        Body: {
            "invoice_id": 123,
            "amount": "100.00",
            "notes": "Partial payment"
        }
        
        Supports:
        - Partial payments (amount < invoice balance)
        - Full payments (amount = invoice balance)
        - Overpayments (creates unallocated amount for future use)
        """
        try:
            payment = self.get_object()
            invoice_id = request.data.get("invoice_id")
            amount = Decimal(str(request.data.get("amount", "0.00")))
            notes = request.data.get("notes", "")
            
            if not invoice_id:
                return Response(
                    {"error": "invoice_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate amount
            can_allocate, reason = payment.can_allocate(amount)
            if not can_allocate:
                return Response(
                    {"error": reason},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get invoice
            try:
                invoice = Invoice.firm_scoped.get_for_firm(request.firm, id=invoice_id)
            except Invoice.DoesNotExist:
                return Response(
                    {"error": f"Invoice {invoice_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create allocation
            allocation = PaymentAllocation.objects.create(
                firm=payment.firm,
                payment=payment,
                invoice=invoice,
                amount=amount,
                notes=notes,
                created_by=request.user,
            )
            
            # Refresh payment to get updated amounts
            payment.refresh_from_db()
            
            return Response({
                "success": True,
                "allocation_id": allocation.id,
                "payment": PaymentSerializer(payment, context={"request": request}).data,
                "invoice": InvoiceSerializer(invoice, context={"request": request}).data,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentAllocationViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for PaymentAllocation model (Medium Feature 2.10).
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    
    model = PaymentAllocation
    serializer_class = PaymentAllocationSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["payment", "invoice"]
    search_fields = []
    ordering_fields = ["allocation_date", "amount"]
    ordering = ["-allocation_date", "-created_at"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("payment", "invoice", "created_by")


class ProjectProfitabilityViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Project Profitability (Task 3.3).
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Provides profitability analysis for individual projects.
    """
    
    model = ProjectProfitability
    serializer_class = ProjectProfitabilitySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["project"]
    search_fields = ["project__name", "project__client__company_name"]
    ordering_fields = ["gross_margin_percentage", "net_margin_percentage", "total_revenue", "last_calculated_at"]
    ordering = ["-last_calculated_at"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("project", "project__client", "firm")
    
    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        """Recalculate profitability for this project."""
        profitability = self.get_object()
        profitability.calculate_profitability()
        serializer = self.get_serializer(profitability)
        return Response(serializer.data)
    
    @action(detail=False, methods=["post"])
    def recalculate_all(self, request):
        """Recalculate profitability for all projects."""
        queryset = self.get_queryset()
        count = 0
        for record in queryset:
            record.calculate_profitability()
            count += 1
        return Response({"message": f"Recalculated profitability for {count} project(s)."})


class ServiceLineProfitabilityViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Service Line Profitability (Task 3.3).
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Provides aggregated profitability analysis across service lines.
    """
    
    model = ServiceLineProfitability
    serializer_class = ServiceLineProfitabilitySerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["name", "period_start", "period_end"]
    search_fields = ["name", "description"]
    ordering_fields = ["margin_percentage", "total_revenue", "period_start"]
    ordering = ["-period_start", "-period_end"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("firm")
