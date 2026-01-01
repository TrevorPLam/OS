"""
DRF ViewSets for Finance module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from decimal import Decimal

from django.db import models
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.finance.models import (
    Bill,
    Invoice,
    LedgerEntry,
    MVRefreshLog,
    Payment,
    PaymentAllocation,
    ProjectProfitability,
    RevenueByProjectMonthMV,
    ServiceLineProfitability,
)
from modules.firm.utils import FirmScopedMixin

from .serializers import (
    BillSerializer,
    InvoiceSerializer,
    LedgerEntrySerializer,
    MVRefreshLogSerializer,
    PaymentAllocationSerializer,
    PaymentSerializer,
    ProjectProfitabilitySerializer,
    RevenueByProjectMonthMVSerializer,
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


class RevenueByProjectMonthMVViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Revenue by Project Month Materialized View (Sprint 5.2).
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    
    Provides fast, pre-aggregated revenue reporting data.
    This is READ-ONLY as it's backed by a materialized view.
    
    Use Cases:
    - Revenue dashboards by month/quarter/year
    - Project profitability analysis
    - Client revenue analysis
    - Service line revenue reporting (via grouping)
    
    Data Freshness:
    - Refreshed daily at 2 AM (scheduled)
    - Can be refreshed on-demand via /refresh/ endpoint
    - Check 'data_age_minutes' field for staleness
    """
    
    model = RevenueByProjectMonthMV
    serializer_class = RevenueByProjectMonthMVSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["project_id", "client_id", "month"]
    search_fields = ["project_name", "project_code"]
    ordering_fields = ["month", "total_revenue", "gross_margin", "net_margin", "utilization_rate"]
    ordering = ["-month", "project_name"]
    
    def get_queryset(self):
        """
        Override to optimize queryset.
        
        Note: No select_related needed - MV is denormalized.
        """
        return super().get_queryset()
    
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, DenyPortalAccess])
    def refresh(self, request):
        """
        Manually refresh the materialized view.
        
        Triggers an on-demand refresh of all revenue data.
        Use sparingly - scheduled refresh is preferred.
        
        Request body (optional):
        - concurrently: bool (default: True) - Use CONCURRENT refresh
        
        Response:
        - status: "success" or "failed"
        - duration_seconds: Time taken to refresh
        - rows_affected: Number of rows in refreshed view
        """
        concurrently = request.data.get("concurrently", True)
        result = RevenueByProjectMonthMV.refresh(concurrently=concurrently)
        
        if result["status"] == "success":
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=["get"])
    def freshness(self, request):
        """
        Check data freshness of the materialized view.
        
        Returns:
        - last_refresh: When MV was last refreshed
        - data_age_minutes: How old the data is
        - refresh_count_24h: Number of refreshes in last 24 hours
        - last_refresh_status: Status of last refresh attempt
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Get most recent refresh from any row (they all have same refreshed_at)
        queryset = self.get_queryset()
        if queryset.exists():
            latest_record = queryset.first()
            last_refresh = latest_record.refreshed_at
            data_age_minutes = latest_record.data_age_minutes
        else:
            last_refresh = None
            data_age_minutes = None
        
        # Get refresh logs for last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        recent_refreshes = MVRefreshLog.objects.filter(
            view_name="mv_revenue_by_project_month",
            refresh_started_at__gte=last_24h,
        ).order_by("-refresh_started_at")
        
        refresh_count_24h = recent_refreshes.count()
        last_refresh_log = recent_refreshes.first()
        
        return Response({
            "view_name": "mv_revenue_by_project_month",
            "last_refresh": last_refresh.isoformat() if last_refresh else None,
            "data_age_minutes": data_age_minutes,
            "refresh_count_24h": refresh_count_24h,
            "last_refresh_status": last_refresh_log.refresh_status if last_refresh_log else None,
            "last_refresh_duration_seconds": last_refresh_log.duration_seconds if last_refresh_log else None,
        })
    
    @action(detail=False, methods=["get"])
    def aggregate_by_quarter(self, request):
        """
        Aggregate revenue by quarter for the current year.
        
        Query params:
        - year: int (default: current year)
        
        Returns quarterly aggregates:
        - Q1: Jan-Mar
        - Q2: Apr-Jun
        - Q3: Jul-Sep
        - Q4: Oct-Dec
        """
        from django.db.models import Sum, Avg, Count
        from datetime import date
        
        year = int(request.query_params.get("year", date.today().year))
        
        queryset = self.get_queryset().filter(month__year=year)
        
        # Group by quarter
        results = []
        for quarter in range(1, 5):
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            
            q_data = queryset.filter(
                month__month__gte=start_month,
                month__month__lte=end_month,
            ).aggregate(
                total_revenue=Sum("total_revenue"),
                total_labor_cost=Sum("labor_cost"),
                total_expense_cost=Sum("expense_cost"),
                total_overhead_cost=Sum("overhead_cost"),
                total_hours=Sum("total_hours"),
                total_billable_hours=Sum("billable_hours"),
                avg_team_size=Avg("team_members"),
                project_count=Count("project_id", distinct=True),
            )
            
            # Calculate derived metrics
            total_revenue = q_data["total_revenue"] or Decimal("0.00")
            total_costs = (
                (q_data["total_labor_cost"] or Decimal("0.00")) +
                (q_data["total_expense_cost"] or Decimal("0.00")) +
                (q_data["total_overhead_cost"] or Decimal("0.00"))
            )
            gross_margin = total_revenue - total_costs
            margin_pct = (gross_margin / total_revenue * 100) if total_revenue > 0 else Decimal("0.00")
            
            total_hours = q_data["total_hours"] or Decimal("0.00")
            billable_hours = q_data["total_billable_hours"] or Decimal("0.00")
            utilization = (billable_hours / total_hours * 100) if total_hours > 0 else Decimal("0.00")
            
            results.append({
                "quarter": f"Q{quarter}",
                "year": year,
                "total_revenue": float(total_revenue),
                "total_costs": float(total_costs),
                "gross_margin": float(gross_margin),
                "margin_percentage": float(margin_pct),
                "total_hours": float(total_hours),
                "billable_hours": float(billable_hours),
                "utilization_rate": float(utilization),
                "avg_team_size": float(q_data["avg_team_size"] or 0),
                "project_count": q_data["project_count"],
            })
        
        return Response({
            "year": year,
            "quarters": results,
            "metadata": {
                "source": "mv_revenue_by_project_month",
                "non_authoritative": True,
            }
        })


class MVRefreshLogViewSet(QueryTimeoutMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for MV Refresh Log (Sprint 5.5).
    
    Provides monitoring and troubleshooting data for materialized view refreshes.
    READ-ONLY - logs are immutable.
    
    No firm scoping - platform operators can view all logs.
    """
    
    queryset = MVRefreshLog.objects.all()
    serializer_class = MVRefreshLogSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["view_name", "refresh_status", "triggered_by"]
    ordering_fields = ["refresh_started_at", "duration_seconds", "rows_affected"]
    ordering = ["-refresh_started_at"]
    
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        Get refresh statistics across all views.
        
        Query params:
        - view_name: filter to specific view
        - days: number of days to look back (default: 7)
        
        Returns:
        - total_refreshes
        - success_rate
        - avg_duration_seconds
        - failure_count
        - recent_failures
        """
        from django.db.models import Avg, Count
        from django.utils import timezone
        from datetime import timedelta
        
        view_name = request.query_params.get("view_name")
        days = int(request.query_params.get("days", 7))
        
        since = timezone.now() - timedelta(days=days)
        queryset = self.get_queryset().filter(refresh_started_at__gte=since)
        
        if view_name:
            queryset = queryset.filter(view_name=view_name)
        
        stats = queryset.aggregate(
            total_refreshes=Count("id"),
            success_count=Count("id", filter=models.Q(refresh_status="success")),
            failed_count=Count("id", filter=models.Q(refresh_status="failed")),
            avg_duration=Avg("duration_seconds"),
        )
        
        total = stats["total_refreshes"] or 0
        success = stats["success_count"] or 0
        success_rate = (success / total * 100) if total > 0 else 0
        
        # Get recent failures
        recent_failures = queryset.filter(refresh_status="failed").order_by("-refresh_started_at")[:5]
        failure_data = MVRefreshLogSerializer(recent_failures, many=True).data
        
        return Response({
            "period_days": days,
            "view_name": view_name or "all",
            "total_refreshes": total,
            "success_count": success,
            "failed_count": stats["failed_count"] or 0,
            "success_rate_percentage": round(success_rate, 2),
            "avg_duration_seconds": round(stats["avg_duration"] or 0, 2),
            "recent_failures": failure_data,
        })
