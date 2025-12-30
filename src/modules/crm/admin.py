"""
Django Admin configuration for CRM models (Pre-Sale).
"""

from django.contrib import admin

from .models import Campaign, Contract, Lead, Proposal, Prospect
from modules.crm.lead_scoring import ScoringRule, ScoreAdjustment


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["company_name", "contact_name", "status", "source", "lead_score", "assigned_to", "captured_date"]
    list_filter = ["status", "source", "assigned_to", "campaign"]
    search_fields = ["company_name", "contact_name", "contact_email"]
    readonly_fields = ["captured_date", "created_at", "updated_at"]


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = [
        "company_name",
        "pipeline_stage",
        "estimated_value",
        "close_date_estimate",
        "probability",
        "assigned_to",
        "created_at",
    ]
    list_filter = ["pipeline_stage", "assigned_to"]
    search_fields = ["company_name", "primary_contact_name", "primary_contact_email"]
    readonly_fields = ["created_at", "updated_at", "won_date", "lost_date"]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "type",
        "status",
        "leads_generated",
        "renewals_won",
        "revenue_generated",
        "budget",
        "start_date",
        "end_date",
    ]
    list_filter = ["type", "status", "owner"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "leads_generated",
        "opportunities_created",
        "clients_contacted",
        "renewal_proposals_sent",
        "renewals_won",
        "created_at",
        "updated_at",
    ]
    filter_horizontal = ["targeted_clients"]


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = [
        "proposal_number",
        "proposal_type",
        "get_company",
        "title",
        "status",
        "total_value",
        "valid_until",
        "converted_to_engagement",
        "created_at",
    ]
    list_filter = ["proposal_type", "status", "converted_to_engagement", "created_at", "valid_until"]
    search_fields = ["proposal_number", "title", "prospect__company_name", "client__company_name"]
    readonly_fields = ["created_at", "updated_at", "sent_at", "accepted_at", "converted_to_engagement"]

    fieldsets = (
        ("Proposal Type", {"fields": ("proposal_type",)}),
        (
            "Relationship",
            {
                "fields": ("prospect", "client"),
                "description": "Select EITHER prospect (new business) OR client (renewal/expansion)",
            },
        ),
        ("Basic Information", {"fields": ("proposal_number", "created_by", "title", "description", "status")}),
        ("Financial Terms", {"fields": ("total_value", "currency")}),
        ("Timeline", {"fields": ("valid_until", "estimated_start_date", "estimated_end_date")}),
        (
            "Conversion Settings",
            {"fields": ("auto_create_project", "enable_portal_on_acceptance", "converted_to_engagement")},
        ),
        ("Audit", {"fields": ("sent_at", "accepted_at", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_company(self, obj):
        """Get company name (either prospect or client)."""
        if obj.proposal_type == "prospective_client" and obj.prospect:
            return obj.prospect.company_name
        elif obj.client:
            return obj.client.company_name
        return "-"

    get_company.short_description = "Company"


@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    """Admin for ScoringRule model."""

    list_display = [
        'name',
        'firm',
        'rule_type',
        'trigger',
        'points',
        'is_active',
        'priority',
        'times_applied',
        'created_at',
    ]
    list_filter = [
        'firm',
        'rule_type',
        'trigger',
        'is_active',
        'created_at',
    ]
    search_fields = [
        'name',
        'description',
    ]
    readonly_fields = [
        'times_applied',
        'last_applied_at',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['created_by']

    fieldsets = (
        (
            'Basic Information',
            {
                'fields': (
                    'firm',
                    'name',
                    'description',
                    'rule_type',
                )
            }
        ),
        (
            'Trigger & Conditions',
            {
                'fields': (
                    'trigger',
                    'conditions',
                ),
                'description': 'Conditions is a JSON object with field: value pairs'
            }
        ),
        (
            'Scoring',
            {
                'fields': (
                    'points',
                    'max_applications',
                    'decay_days',
                )
            }
        ),
        (
            'Status & Priority',
            {
                'fields': (
                    'is_active',
                    'priority',
                )
            }
        ),
        (
            'Usage Statistics',
            {
                'fields': (
                    'times_applied',
                    'last_applied_at',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            'Metadata',
            {
                'fields': (
                    'created_by',
                    'created_at',
                    'updated_at',
                ),
                'classes': ('collapse',)
            }
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('firm', 'created_by')


@admin.register(ScoreAdjustment)
class ScoreAdjustmentAdmin(admin.ModelAdmin):
    """Admin for ScoreAdjustment model."""

    list_display = [
        'lead',
        'points',
        'reason',
        'rule',
        'trigger_event',
        'is_decayed',
        'applied_at',
    ]
    list_filter = [
        'trigger_event',
        'is_decayed',
        'applied_at',
    ]
    search_fields = [
        'lead__company_name',
        'lead__contact_name',
        'reason',
    ]
    readonly_fields = [
        'lead',
        'rule',
        'points',
        'reason',
        'trigger_event',
        'event_data',
        'decays_at',
        'is_decayed',
        'applied_at',
        'applied_by',
    ]
    raw_id_fields = ['lead', 'rule', 'applied_by']

    fieldsets = (
        (
            'Adjustment Details',
            {
                'fields': (
                    'lead',
                    'points',
                    'reason',
                )
            }
        ),
        (
            'Rule & Trigger',
            {
                'fields': (
                    'rule',
                    'trigger_event',
                    'event_data',
                )
            }
        ),
        (
            'Decay',
            {
                'fields': (
                    'decays_at',
                    'is_decayed',
                )
            }
        ),
        (
            'Metadata',
            {
                'fields': (
                    'applied_at',
                    'applied_by',
                )
            }
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('lead', 'rule', 'applied_by')

    def has_add_permission(self, request):
        """Adjustments are created automatically or via API, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Adjustments are read-only for audit trail."""
        return False


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = [
        "contract_number",
        "client",
        "title",
        "status",
        "total_value",
        "start_date",
        "end_date",
        "created_at",
    ]
    list_filter = ["status", "payment_terms", "created_at"]
    search_fields = ["contract_number", "title", "client__company_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("contract_number", "client", "proposal", "signed_by", "title", "description", "status")},
        ),
        ("Financial Terms", {"fields": ("total_value", "currency", "payment_terms")}),
        ("Timeline", {"fields": ("start_date", "end_date", "signed_date")}),
        ("Documents", {"fields": ("contract_file_url",)}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
