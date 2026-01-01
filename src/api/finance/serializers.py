"""
DRF Serializers for Finance module.
"""

from rest_framework import serializers

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


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class BillSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "approved_at"]


class LedgerEntrySerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    bill_reference = serializers.CharField(source="bill.reference_number", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = "__all__"
        read_only_fields = ["created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model (Medium Feature 2.10)."""
    
    client_name = serializers.CharField(source="client.company_name", read_only=True)
    
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "amount_allocated", "amount_unallocated"]


class PaymentAllocationSerializer(serializers.ModelSerializer):
    """Serializer for PaymentAllocation model (Medium Feature 2.10)."""
    
    payment_number = serializers.CharField(source="payment.payment_number", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    
    class Meta:
        model = PaymentAllocation
        fields = "__all__"
        read_only_fields = ["created_at"]


class ProjectProfitabilitySerializer(serializers.ModelSerializer):
    """Serializer for ProjectProfitability model (Task 3.3)."""
    
    project_name = serializers.CharField(source="project.name", read_only=True)
    client_name = serializers.CharField(source="project.client.company_name", read_only=True)
    
    class Meta:
        model = ProjectProfitability
        fields = [
            "id",
            "firm",
            "project",
            "project_name",
            "client_name",
            "total_revenue",
            "recognized_revenue",
            "labor_cost",
            "expense_cost",
            "overhead_cost",
            "gross_margin",
            "gross_margin_percentage",
            "net_margin",
            "net_margin_percentage",
            "estimated_completion_cost",
            "estimated_final_margin",
            "hours_logged",
            "billable_utilization",
            "last_calculated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_revenue",
            "recognized_revenue",
            "labor_cost",
            "expense_cost",
            "overhead_cost",
            "gross_margin",
            "gross_margin_percentage",
            "net_margin",
            "net_margin_percentage",
            "hours_logged",
            "billable_utilization",
            "last_calculated_at",
            "created_at",
        ]


class ServiceLineProfitabilitySerializer(serializers.ModelSerializer):
    """Serializer for ServiceLineProfitability model (Task 3.3)."""
    
    class Meta:
        model = ServiceLineProfitability
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "period_start",
            "period_end",
            "total_revenue",
            "total_cost",
            "gross_margin",
            "margin_percentage",
            "project_count",
            "active_project_count",
            "last_calculated_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "total_revenue",
            "total_cost",
            "gross_margin",
            "margin_percentage",
            "project_count",
            "active_project_count",
            "last_calculated_at",
            "created_at",
        ]


class RevenueByProjectMonthMVSerializer(serializers.ModelSerializer):
    """
    Serializer for RevenueByProjectMonthMV materialized view (Sprint 5.2).
    
    Provides pre-aggregated revenue reporting data for fast dashboard queries.
    All fields are read-only as this is a materialized view.
    """
    
    # Computed properties exposed as fields
    gross_margin = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    gross_margin_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    net_margin = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    net_margin_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    utilization_rate = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    data_age_minutes = serializers.IntegerField(read_only=True)
    
    # Metadata for reporting compliance (REPORTING_METADATA.md)
    metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = RevenueByProjectMonthMV
        fields = [
            # Identifiers
            "firm",
            "project_id",
            "project_name",
            "project_code",
            "client_id",
            "month",
            # Revenue metrics
            "total_revenue",
            "labor_cost",
            "expense_cost",
            "overhead_cost",
            "gross_margin",
            "gross_margin_percentage",
            "net_margin",
            "net_margin_percentage",
            # Team metrics
            "team_members",
            "total_hours",
            "billable_hours",
            "utilization_rate",
            # Invoice metrics
            "invoice_count",
            "paid_invoice_count",
            # Metadata
            "refreshed_at",
            "data_age_minutes",
            "metadata",
        ]
        read_only_fields = "__all__"  # All fields are read-only (MV)
    
    def get_metadata(self, obj):
        """
        Add required reporting metadata per REPORTING_METADATA.md.
        
        Reports must include metadata about sources, freshness, and non-authoritative nature.
        """
        return {
            "source_modules": ["finance", "projects"],
            "generated_at": obj.refreshed_at.isoformat(),
            "freshness_window": f"{obj.data_age_minutes} minutes",
            "join_keys_used": ["project_id", "firm_id"],
            "coverage_notes": "Last 5 years of data; includes paid/partial invoices and approved expenses",
            "non_authoritative": True,
            "provenance_pointers": {
                "invoices": f"finance.Invoice (project_id={obj.project_id})",
                "time_entries": f"projects.TimeEntry (project_id={obj.project_id})",
                "expenses": f"projects.Expense (project_id={obj.project_id})",
            },
            "disclaimer": "This report is derived from multiple modules and is provided for informational purposes only. "
                         "It is non-authoritative and does not supersede the underlying source records. "
                         "Refer to the source systems for official values.",
        }


class MVRefreshLogSerializer(serializers.ModelSerializer):
    """
    Serializer for MVRefreshLog model (Sprint 5.5).
    
    Provides refresh history and monitoring data for materialized views.
    """
    
    duration_seconds = serializers.FloatField(read_only=True)
    
    class Meta:
        model = MVRefreshLog
        fields = [
            "id",
            "view_name",
            "firm_id",
            "refresh_started_at",
            "refresh_completed_at",
            "refresh_status",
            "rows_affected",
            "error_message",
            "triggered_by",
            "duration_seconds",
        ]
        read_only_fields = "__all__"  # Log entries are read-only
