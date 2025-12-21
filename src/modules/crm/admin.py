"""
Django Admin configuration for CRM models (Pre-Sale).
"""
from django.contrib import admin
from .models import Lead, Prospect, Campaign, Proposal, Contract, Client


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'company_name',
        'contact_name',
        'status',
        'source',
        'lead_score',
        'assigned_to',
        'captured_date'
    ]
    list_filter = ['status', 'source', 'assigned_to', 'campaign']
    search_fields = ['company_name', 'contact_name', 'contact_email']
    readonly_fields = ['captured_date', 'created_at', 'updated_at']


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = [
        'company_name',
        'pipeline_stage',
        'estimated_value',
        'close_date_estimate',
        'probability',
        'assigned_to',
        'created_at'
    ]
    list_filter = ['pipeline_stage', 'assigned_to']
    search_fields = ['company_name', 'primary_contact_name', 'primary_contact_email']
    readonly_fields = ['created_at', 'updated_at', 'won_date', 'lost_date']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'type',
        'status',
        'leads_generated',
        'opportunities_created',
        'budget',
        'start_date',
        'end_date'
    ]
    list_filter = ['type', 'status', 'owner']
    search_fields = ['name', 'description']
    readonly_fields = ['leads_generated', 'created_at', 'updated_at']


# DEPRECATED: Old Client admin - kept for data migration compatibility
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
        ('DEPRECATED', {
            'description': 'This model is deprecated. Use modules.clients.Client for new clients.',
            'fields': ()
        }),
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
        'prospect',
        'title',
        'status',
        'total_value',
        'valid_until',
        'converted_to_client',
        'created_at'
    ]
    list_filter = ['status', 'converted_to_client', 'created_at', 'valid_until']
    search_fields = ['proposal_number', 'title', 'prospect__company_name']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'accepted_at', 'converted_to_client']
    fieldsets = (
        ('Basic Information', {
            'fields': ('proposal_number', 'prospect', 'created_by', 'title', 'description', 'status')
        }),
        ('Financial Terms', {
            'fields': ('total_value', 'currency')
        }),
        ('Timeline', {
            'fields': ('valid_until', 'estimated_start_date', 'estimated_end_date')
        }),
        ('Conversion Settings', {
            'fields': ('auto_create_project', 'enable_portal_on_acceptance', 'converted_to_client')
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
