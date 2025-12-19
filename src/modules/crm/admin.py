"""
Django Admin configuration for CRM models.
"""
from django.contrib import admin
from .models import Client, Proposal, Contract


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'company_name',
        'status',
        'primary_contact_name',
        'primary_contact_email',
        'owner',
        'created_at'
    ]
    list_filter = ['status', 'industry', 'created_at']
    search_fields = ['company_name', 'primary_contact_name', 'primary_contact_email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'industry', 'status', 'website', 'employee_count', 'annual_revenue')
        }),
        ('Primary Contact', {
            'fields': ('primary_contact_name', 'primary_contact_email', 'primary_contact_phone')
        }),
        ('Address', {
            'fields': ('street_address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Internal Tracking', {
            'fields': ('owner', 'source', 'notes')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = [
        'proposal_number',
        'client',
        'title',
        'status',
        'total_value',
        'valid_until',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'valid_until']
    search_fields = ['proposal_number', 'title', 'client__company_name']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'accepted_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('proposal_number', 'client', 'created_by', 'title', 'description', 'status')
        }),
        ('Financial Terms', {
            'fields': ('total_value', 'currency')
        }),
        ('Timeline', {
            'fields': ('valid_until', 'estimated_start_date', 'estimated_end_date')
        }),
        ('Audit', {
            'fields': ('sent_at', 'accepted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        'contract_number',
        'client',
        'title',
        'status',
        'total_value',
        'start_date',
        'end_date',
        'created_at'
    ]
    list_filter = ['status', 'payment_terms', 'created_at']
    search_fields = ['contract_number', 'title', 'client__company_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('contract_number', 'client', 'proposal', 'signed_by', 'title', 'description', 'status')
        }),
        ('Financial Terms', {
            'fields': ('total_value', 'currency', 'payment_terms')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'signed_date')
        }),
        ('Documents', {
            'fields': ('contract_file_url',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
