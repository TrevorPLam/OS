"""
Django Admin configuration for Finance models.
"""

from django.contrib import admin

from .models import Bill, Invoice, LedgerEntry, ProjectProfitability, ServiceLineProfitability


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "client",
        "project",
        "status",
        "total_amount",
        "amount_paid",
        "issue_date",
        "due_date",
    ]
    list_filter = ["status", "issue_date", "due_date"]
    search_fields = ["invoice_number", "client__company_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("invoice_number", "client", "project", "created_by", "status")}),
        ("Financial", {"fields": ("subtotal", "tax_amount", "total_amount", "amount_paid", "currency")}),
        ("Payment Terms", {"fields": ("issue_date", "due_date", "payment_terms", "paid_date")}),
        ("Content", {"fields": ("line_items", "notes")}),
        ("Integration", {"fields": ("stripe_invoice_id",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "vendor_name",
        "bill_number",
        "status",
        "total_amount",
        "amount_paid",
        "bill_date",
        "due_date",
    ]
    list_filter = ["status", "expense_category", "bill_date", "due_date"]
    search_fields = ["reference_number", "bill_number", "vendor_name"]
    readonly_fields = ["created_at", "updated_at", "approved_at"]
    fieldsets = (
        ("Vendor Information", {"fields": ("vendor_name", "vendor_email", "project")}),
        ("Bill Details", {"fields": ("bill_number", "reference_number", "status", "expense_category")}),
        ("Financial", {"fields": ("subtotal", "tax_amount", "total_amount", "amount_paid", "currency")}),
        ("Dates", {"fields": ("bill_date", "due_date", "paid_date")}),
        ("Content", {"fields": ("description", "line_items")}),
        ("Approval", {"fields": ("approved_by", "approved_at")}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["transaction_date", "entry_type", "account", "amount", "description", "transaction_group_id"]
    list_filter = ["entry_type", "account", "transaction_date"]
    search_fields = ["description", "transaction_group_id"]
    readonly_fields = ["created_at"]
    fieldsets = (
        ("Entry Information", {"fields": ("transaction_date", "entry_type", "account", "amount", "description")}),
        ("References", {"fields": ("invoice", "bill", "transaction_group_id")}),
        ("Audit", {"fields": ("created_by", "created_at"), "classes": ("collapse",)}),
    )


@admin.register(ProjectProfitability)
class ProjectProfitabilityAdmin(admin.ModelAdmin):
    """Admin interface for Project Profitability (Task 3.3)."""
    
    list_display = [
        "project",
        "total_revenue",
        "gross_margin",
        "gross_margin_percentage",
        "net_margin_percentage",
        "hours_logged",
        "billable_utilization",
        "last_calculated_at",
    ]
    list_filter = ["last_calculated_at", "firm"]
    search_fields = ["project__name", "project__client__company_name"]
    readonly_fields = [
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
    
    fieldsets = (
        ("Project", {"fields": ("firm", "project")}),
        ("Revenue", {"fields": ("total_revenue", "recognized_revenue")}),
        ("Costs", {"fields": ("labor_cost", "expense_cost", "overhead_cost")}),
        ("Margins", {"fields": ("gross_margin", "gross_margin_percentage", "net_margin", "net_margin_percentage")}),
        ("Metrics", {"fields": ("hours_logged", "billable_utilization")}),
        ("Forecasting", {"fields": ("estimated_completion_cost", "estimated_final_margin")}),
        ("Timestamps", {"fields": ("last_calculated_at", "created_at"), "classes": ("collapse",)}),
    )
    
    actions = ["recalculate_profitability"]
    
    def recalculate_profitability(self, request, queryset):
        """Admin action to recalculate profitability for selected records."""
        count = 0
        for record in queryset:
            record.calculate_profitability()
            count += 1
        self.message_user(request, f"Recalculated profitability for {count} project(s).")
    
    recalculate_profitability.short_description = "Recalculate profitability"


@admin.register(ServiceLineProfitability)
class ServiceLineProfitabilityAdmin(admin.ModelAdmin):
    """Admin interface for Service Line Profitability (Task 3.3)."""
    
    list_display = [
        "name",
        "period_start",
        "period_end",
        "project_count",
        "total_revenue",
        "gross_margin",
        "margin_percentage",
        "last_calculated_at",
    ]
    list_filter = ["firm", "period_start", "period_end"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "total_revenue",
        "total_cost",
        "gross_margin",
        "margin_percentage",
        "project_count",
        "active_project_count",
        "last_calculated_at",
        "created_at",
    ]
    
    fieldsets = (
        ("Service Line", {"fields": ("firm", "name", "description")}),
        ("Period", {"fields": ("period_start", "period_end")}),
        ("Metrics", {"fields": ("total_revenue", "total_cost", "gross_margin", "margin_percentage")}),
        ("Projects", {"fields": ("project_count", "active_project_count")}),
        ("Timestamps", {"fields": ("last_calculated_at", "created_at"), "classes": ("collapse",)}),
    )
