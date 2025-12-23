"""
Django Admin configuration for Finance models.
"""
from django.contrib import admin
from .models import Invoice, Bill, LedgerEntry


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number',
        'client',
        'project',
        'status',
        'total_amount',
        'amount_paid',
        'issue_date',
        'due_date'
    ]
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'client__company_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'client', 'project', 'created_by', 'status')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'amount_paid', 'currency')
        }),
        ('Payment Terms', {
            'fields': ('issue_date', 'due_date', 'payment_terms', 'paid_date')
        }),
        ('Content', {
            'fields': ('line_items', 'notes')
        }),
        ('Integration', {
            'fields': ('stripe_invoice_id',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number',
        'vendor_name',
        'bill_number',
        'status',
        'total_amount',
        'amount_paid',
        'bill_date',
        'due_date'
    ]
    list_filter = ['status', 'expense_category', 'bill_date', 'due_date']
    search_fields = ['reference_number', 'bill_number', 'vendor_name']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    fieldsets = (
        ('Vendor Information', {
            'fields': ('vendor_name', 'vendor_email', 'project')
        }),
        ('Bill Details', {
            'fields': ('bill_number', 'reference_number', 'status', 'expense_category')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'amount_paid', 'currency')
        }),
        ('Dates', {
            'fields': ('bill_date', 'due_date', 'paid_date')
        }),
        ('Content', {
            'fields': ('description', 'line_items')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_date',
        'entry_type',
        'account',
        'amount',
        'description',
        'transaction_group_id'
    ]
    list_filter = ['entry_type', 'account', 'transaction_date']
    search_fields = ['description', 'transaction_group_id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Entry Information', {
            'fields': ('transaction_date', 'entry_type', 'account', 'amount', 'description')
        }),
        ('References', {
            'fields': ('invoice', 'bill', 'transaction_group_id')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
