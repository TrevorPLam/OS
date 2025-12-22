"""
Django Admin configuration for CRM models (Pre-Sale).
"""
from django.contrib import admin
from .models import Lead, Prospect, Campaign, Proposal, Contract


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
        'renewals_won',
        'revenue_generated',
        'budget',
        'start_date',
        'end_date'
    ]
    list_filter = ['type', 'status', 'owner']
    search_fields = ['name', 'description']
    readonly_fields = [
        'leads_generated',
        'opportunities_created',
        'clients_contacted',
        'renewal_proposals_sent',
        'renewals_won',
        'created_at',
        'updated_at'
    ]
    filter_horizontal = ['targeted_clients']


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = [
        'proposal_number',
        'proposal_type',
        'get_company',
        'title',
        'status',
        'total_value',
        'valid_until',
        'converted_to_engagement',
        'created_at'
    ]
    list_filter = ['proposal_type', 'status', 'converted_to_engagement', 'created_at', 'valid_until']
    search_fields = [
        'proposal_number',
        'title',
        'prospect__company_name',
        'client__company_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'accepted_at', 'converted_to_engagement']

    fieldsets = (
        ('Proposal Type', {
            'fields': ('proposal_type',)
        }),
        ('Relationship', {
            'fields': ('prospect', 'client'),
            'description': 'Select EITHER prospect (new business) OR client (renewal/expansion)'
        }),
        ('Basic Information', {
            'fields': ('proposal_number', 'created_by', 'title', 'description', 'status')
        }),
        ('Financial Terms', {
            'fields': ('total_value', 'currency')
        }),
        ('Timeline', {
            'fields': ('valid_until', 'estimated_start_date', 'estimated_end_date')
        }),
        ('Conversion Settings', {
            'fields': ('auto_create_project', 'enable_portal_on_acceptance', 'converted_to_engagement')
        }),
        ('Audit', {
            'fields': ('sent_at', 'accepted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_company(self, obj):
        """Get company name (either prospect or client)."""
        if obj.proposal_type == 'prospective_client' and obj.prospect:
            return obj.prospect.company_name
        elif obj.client:
            return obj.client.company_name
        return '-'
    get_company.short_description = 'Company'


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
