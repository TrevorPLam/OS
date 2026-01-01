"""
DRF Serializers for Finance module.
"""

from rest_framework import serializers

from modules.finance.models import Bill, Invoice, LedgerEntry, Payment, PaymentAllocation, ProjectProfitability, ServiceLineProfitability


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
