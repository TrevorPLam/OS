"""
Django Admin configuration for CRM models (Pre-Sale).
"""

from django.contrib import admin

from .models import (
    Account,
    AccountContact,
    AccountRelationship,
    Campaign,
    Contract,
    Deal,
    DealAssignmentRule,
    DealStageAutomation,
    DealTask,
    IntakeForm,
    IntakeFormField,
    IntakeFormSubmission,
    Lead,
    Pipeline,
    PipelineStage,
    Product,
    ProductConfiguration,
    ProductOption,
    Proposal,
    Prospect,
)
from modules.crm.lead_scoring import ScoringRule, ScoreAdjustment


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "account_type",
        "status",
        "industry",
        "owner",
        "employee_count",
        "created_at",
    ]
    list_filter = ["account_type", "status", "industry", "owner"]
    search_fields = ["name", "legal_name", "website"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["parent_account", "owner", "created_by"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("firm", "name", "legal_name", "account_type", "status", "owner")
        }),
        ("Business Details", {
            "fields": ("industry", "website", "employee_count", "annual_revenue")
        }),
        ("Billing Address", {
            "fields": (
                "billing_address_line1",
                "billing_address_line2",
                "billing_city",
                "billing_state",
                "billing_postal_code",
                "billing_country",
            ),
            "classes": ("collapse",)
        }),
        ("Shipping Address", {
            "fields": (
                "shipping_address_line1",
                "shipping_address_line2",
                "shipping_city",
                "shipping_state",
                "shipping_postal_code",
                "shipping_country",
            ),
            "classes": ("collapse",)
        }),
        ("Relationships", {
            "fields": ("parent_account",)
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(AccountContact)
class AccountContactAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "account",
        "email",
        "job_title",
        "is_primary_contact",
        "is_decision_maker",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_primary_contact", "is_decision_maker", "is_active", "preferred_contact_method"]
    search_fields = ["first_name", "last_name", "email", "account__name"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["account", "created_by"]
    
    fieldsets = (
        ("Account", {"fields": ("account",)}),
        ("Personal Information", {
            "fields": ("first_name", "last_name", "email", "phone", "mobile_phone")
        }),
        ("Professional Information", {
            "fields": ("job_title", "department")
        }),
        ("Contact Preferences", {
            "fields": (
                "is_primary_contact",
                "is_decision_maker",
                "preferred_contact_method",
                "opt_out_marketing",
            )
        }),
        ("Status", {"fields": ("is_active",)}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(AccountRelationship)
class AccountRelationshipAdmin(admin.ModelAdmin):
    list_display = [
        "from_account",
        "relationship_type",
        "to_account",
        "status",
        "start_date",
        "end_date",
        "created_at",
    ]
    list_filter = ["relationship_type", "status", "created_at"]
    search_fields = ["from_account__name", "to_account__name"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["from_account", "to_account", "created_by"]
    
    fieldsets = (
        ("Relationship", {
            "fields": ("from_account", "to_account", "relationship_type", "status")
        }),
        ("Timeline", {
            "fields": ("start_date", "end_date")
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


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
        "stage",
        "estimated_value",
        "close_date_estimate",
        "probability",
        "assigned_to",
        "created_at",
    ]
    list_filter = ["stage", "assigned_to"]
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


class IntakeFormFieldInline(admin.TabularInline):
    """Inline admin for IntakeFormField (Task 3.4)."""
    
    model = IntakeFormField
    extra = 1
    fields = ["label", "field_type", "required", "order", "scoring_enabled"]
    ordering = ["order", "id"]


@admin.register(IntakeForm)
class IntakeFormAdmin(admin.ModelAdmin):
    """Admin interface for Intake Forms (Task 3.4)."""
    
    list_display = [
        "name",
        "status",
        "submission_count",
        "qualified_count",
        "qualification_threshold",
        "created_at",
    ]
    list_filter = ["status", "qualification_enabled", "auto_create_lead", "auto_create_prospect"]
    search_fields = ["name", "title", "description"]
    readonly_fields = ["submission_count", "qualified_count", "created_at", "updated_at"]
    inlines = [IntakeFormFieldInline]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("firm", "name", "title", "description", "status")
        }),
        ("Qualification", {
            "fields": ("qualification_enabled", "qualification_threshold")
        }),
        ("Automation", {
            "fields": ("auto_create_lead", "auto_create_prospect", "default_owner")
        }),
        ("Notifications", {
            "fields": ("notify_on_submission", "notification_emails")
        }),
        ("Thank You Page", {
            "fields": ("thank_you_title", "thank_you_message", "redirect_url")
        }),
        ("Statistics", {
            "fields": ("submission_count", "qualified_count"),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(IntakeFormField)
class IntakeFormFieldAdmin(admin.ModelAdmin):
    """Admin interface for Intake Form Fields (Task 3.4)."""
    
    list_display = [
        "label",
        "form",
        "field_type",
        "required",
        "scoring_enabled",
        "order",
    ]
    list_filter = ["form", "field_type", "required", "scoring_enabled"]
    search_fields = ["label", "form__name"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Field Configuration", {
            "fields": ("form", "label", "field_type", "placeholder", "help_text", "required", "order")
        }),
        ("Options (for select fields)", {
            "fields": ("options",)
        }),
        ("Qualification Scoring", {
            "fields": ("scoring_enabled", "scoring_rules")
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(IntakeFormSubmission)
class IntakeFormSubmissionAdmin(admin.ModelAdmin):
    """Admin interface for Intake Form Submissions (Task 3.4)."""
    
    list_display = [
        "form",
        "submitter_email",
        "submitter_company",
        "qualification_score",
        "status",
        "is_qualified",
        "created_at",
    ]
    list_filter = ["form", "status", "is_qualified", "created_at"]
    search_fields = ["submitter_email", "submitter_name", "submitter_company"]
    readonly_fields = [
        "responses",
        "qualification_score",
        "is_qualified",
        "ip_address",
        "user_agent",
        "referrer",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["lead", "prospect", "reviewed_by"]
    
    fieldsets = (
        ("Form", {
            "fields": ("form", "status")
        }),
        ("Submitter Information", {
            "fields": ("submitter_email", "submitter_name", "submitter_phone", "submitter_company")
        }),
        ("Responses", {
            "fields": ("responses",)
        }),
        ("Qualification", {
            "fields": ("qualification_score", "is_qualified")
        }),
        ("Conversion", {
            "fields": ("lead", "prospect")
        }),
        ("Review", {
            "fields": ("reviewed_by", "reviewed_at", "review_notes")
        }),
        ("Metadata", {
            "fields": ("ip_address", "user_agent", "referrer"),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["calculate_scores", "create_leads", "mark_as_spam"]
    
    def calculate_scores(self, request, queryset):
        """Admin action to calculate qualification scores."""
        count = 0
        for submission in queryset:
            submission.calculate_qualification_score()
            count += 1
        self.message_user(request, f"Calculated qualification scores for {count} submission(s).")
    
    calculate_scores.short_description = "Calculate qualification scores"
    
    def create_leads(self, request, queryset):
        """Admin action to create leads from submissions."""
        count = 0
        for submission in queryset.filter(lead__isnull=True):
            submission.create_lead()
            count += 1
        self.message_user(request, f"Created {count} lead(s) from submissions.")
    
    create_leads.short_description = "Create leads from submissions"
    
    def mark_as_spam(self, request, queryset):
        """Admin action to mark submissions as spam."""
        count = queryset.update(status="spam")
        self.message_user(request, f"Marked {count} submission(s) as spam.")
    
    mark_as_spam.short_description = "Mark as spam"


# ============================================================================
# CPQ (Configure-Price-Quote) Admin - Task 3.5
# ============================================================================


class ProductOptionInline(admin.TabularInline):
    """Inline admin for ProductOption within Product admin."""
    model = ProductOption
    extra = 0
    fields = [
        "code",
        "label",
        "option_type",
        "required",
        "display_order",
        "price_modifier",
        "price_multiplier",
    ]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model (CPQ)."""
    
    list_display = [
        "code",
        "name",
        "product_type",
        "status",
        "base_price",
        "currency",
        "is_configurable",
        "created_at",
    ]
    list_filter = ["product_type", "status", "is_configurable", "category"]
    search_fields = ["code", "name", "description", "category"]
    readonly_fields = ["created_at", "created_by", "updated_at"]
    raw_id_fields = ["created_by"]
    inlines = [ProductOptionInline]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("firm", "code", "name", "description", "product_type", "status")
        }),
        ("Pricing", {
            "fields": ("base_price", "currency")
        }),
        ("Configuration", {
            "fields": ("is_configurable", "configuration_schema")
        }),
        ("Metadata", {
            "fields": ("category", "tags")
        }),
        ("Audit", {
            "fields": ("created_at", "created_by", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by on first save."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    """Admin interface for ProductOption model (CPQ)."""
    
    list_display = [
        "product",
        "code",
        "label",
        "option_type",
        "required",
        "display_order",
        "price_modifier",
        "price_multiplier",
    ]
    list_filter = ["option_type", "required", "product__product_type"]
    search_fields = ["code", "label", "description", "product__name"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["product"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("product", "code", "label", "description", "option_type")
        }),
        ("Configuration", {
            "fields": ("required", "display_order", "values")
        }),
        ("Pricing Impact", {
            "fields": ("price_modifier", "price_multiplier")
        }),
        ("Dependencies", {
            "fields": ("dependency_rules",),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(ProductConfiguration)
class ProductConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for ProductConfiguration model (CPQ)."""
    
    list_display = [
        "id",
        "product",
        "configuration_name",
        "status",
        "base_price",
        "configuration_price",
        "discount_percentage",
        "quote",
        "created_at",
    ]
    list_filter = ["status", "product__product_type"]
    search_fields = ["configuration_name", "product__name", "product__code"]
    readonly_fields = [
        "base_price",
        "configuration_price",
        "discount_amount",
        "price_breakdown",
        "validation_errors",
        "created_at",
        "created_by",
        "updated_at",
    ]
    raw_id_fields = ["product", "quote", "created_by"]
    actions = ["validate_configurations", "recalculate_prices"]
    
    fieldsets = (
        ("Product", {
            "fields": ("product",)
        }),
        ("Configuration", {
            "fields": ("configuration_name", "selected_options", "status")
        }),
        ("Pricing", {
            "fields": (
                "base_price",
                "configuration_price",
                "discount_percentage",
                "discount_amount",
                "price_breakdown",
            )
        }),
        ("Validation", {
            "fields": ("validation_errors",),
            "classes": ("collapse",)
        }),
        ("Quote Reference", {
            "fields": ("quote",),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "created_by", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by on first save and validate configuration."""
        if not change:
            obj.created_by = request.user
        
        # Validate configuration before saving
        obj.validate_configuration()
        super().save_model(request, obj, form, change)
    
    def validate_configurations(self, request, queryset):
        """Admin action to validate selected configurations."""
        count = 0
        errors = 0
        for config in queryset:
            is_valid, _ = config.validate_configuration()
            config.save()
            if is_valid:
                count += 1
            else:
                errors += 1
        
        self.message_user(
            request,
            f"Validated {count + errors} configuration(s): {count} valid, {errors} with errors."
        )
    
    validate_configurations.short_description = "Validate configurations"
    
    def recalculate_prices(self, request, queryset):
        """Admin action to recalculate prices for selected configurations."""
        count = 0
        for config in queryset:
            config.calculate_price()
            config.save()
            count += 1
        
        self.message_user(request, f"Recalculated prices for {count} configuration(s).")
    
    recalculate_prices.short_description = "Recalculate prices"


# Pipeline & Deal Management Admin (DEAL-2)

@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "firm",
        "is_active",
        "is_default",
        "display_order",
        "created_at",
    ]
    list_filter = ["firm", "is_active", "is_default"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["created_by"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("firm", "name", "description")
        }),
        ("Settings", {
            "fields": ("is_active", "is_default", "display_order")
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "pipeline",
        "probability",
        "is_active",
        "is_closed_won",
        "is_closed_lost",
        "display_order",
    ]
    list_filter = ["pipeline", "is_active", "is_closed_won", "is_closed_lost"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("pipeline", "name", "description")
        }),
        ("Settings", {
            "fields": ("probability", "is_active", "is_closed_won", "is_closed_lost", "display_order")
        }),
        ("Automation", {
            "fields": ("auto_tasks",),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


class DealTaskInline(admin.TabularInline):
    model = DealTask
    extra = 0
    fields = ["title", "status", "priority", "assigned_to", "due_date"]
    raw_id_fields = ["assigned_to"]


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "firm",
        "pipeline",
        "stage",
        "value",
        "probability",
        "weighted_value",
        "owner",
        "is_active",
        "is_won",
        "is_lost",
        "is_stale",
        "expected_close_date",
    ]
    list_filter = [
        "firm",
        "pipeline",
        "stage",
        "is_active",
        "is_won",
        "is_lost",
        "is_stale",
        "owner",
    ]
    search_fields = ["name", "description"]
    readonly_fields = [
        "weighted_value",
        "is_won",
        "is_lost",
        "actual_close_date",
        "is_stale",
        "converted_to_project",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["account", "contact", "owner", "campaign", "project", "created_by"]
    filter_horizontal = ["team_members"]
    inlines = [DealTaskInline]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("firm", "name", "description")
        }),
        ("Pipeline", {
            "fields": ("pipeline", "stage")
        }),
        ("Associations", {
            "fields": ("account", "contact", "campaign")
        }),
        ("Financial", {
            "fields": ("value", "currency", "probability", "weighted_value")
        }),
        ("Timeline", {
            "fields": ("expected_close_date", "actual_close_date")
        }),
        ("Assignment", {
            "fields": ("owner", "team_members", "split_percentage")
        }),
        ("Source", {
            "fields": ("source",)
        }),
        ("Status", {
            "fields": (
                "is_active",
                "is_won",
                "is_lost",
                "lost_reason",
                "last_activity_date",
                "is_stale",
                "stale_days_threshold",
            )
        }),
        ("Project Conversion", {
            "fields": ("converted_to_project", "project"),
            "classes": ("collapse",)
        }),
        ("Other", {
            "fields": ("tags",),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["mark_as_won", "mark_as_lost", "check_stale_deals"]
    
    def mark_as_won(self, request, queryset):
        """Admin action to mark deals as won."""
        count = 0
        for deal in queryset:
            if not deal.is_won:
                # Find won stage
                won_stage = deal.pipeline.stages.filter(is_closed_won=True).first()
                if won_stage:
                    deal.stage = won_stage
                deal.is_won = True
                deal.is_active = False
                from django.utils import timezone
                deal.actual_close_date = timezone.now().date()
                deal.save()
                count += 1
        
        self.message_user(request, f"Marked {count} deal(s) as won.")
    
    mark_as_won.short_description = "Mark selected deals as won"
    
    def mark_as_lost(self, request, queryset):
        """Admin action to mark deals as lost."""
        count = 0
        for deal in queryset:
            if not deal.is_lost:
                # Find lost stage
                lost_stage = deal.pipeline.stages.filter(is_closed_lost=True).first()
                if lost_stage:
                    deal.stage = lost_stage
                deal.is_lost = True
                deal.is_active = False
                from django.utils import timezone
                deal.actual_close_date = timezone.now().date()
                deal.save()
                count += 1
        
        self.message_user(request, f"Marked {count} deal(s) as lost.")
    
    mark_as_lost.short_description = "Mark selected deals as lost"
    
    def check_stale_deals(self, request, queryset):
        """Admin action to check and mark stale deals."""
        count = 0
        for deal in queryset.filter(is_active=True):
            if deal.last_activity_date:
                from django.utils import timezone
                days_since_activity = (timezone.now().date() - deal.last_activity_date).days
                if days_since_activity >= deal.stale_days_threshold:
                    deal.is_stale = True
                    deal.save()
                    count += 1
        
        self.message_user(request, f"Marked {count} deal(s) as stale.")
    
    check_stale_deals.short_description = "Check for stale deals"


@admin.register(DealTask)
class DealTaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "deal",
        "status",
        "priority",
        "assigned_to",
        "due_date",
        "created_at",
    ]
    list_filter = ["status", "priority", "assigned_to"]
    search_fields = ["title", "description", "deal__name"]
    readonly_fields = ["completed_at", "created_at", "updated_at"]
    raw_id_fields = ["deal", "assigned_to", "created_by"]
    
    fieldsets = (
        ("Task Information", {
            "fields": ("deal", "title", "description")
        }),
        ("Status & Priority", {
            "fields": ("status", "priority")
        }),
        ("Assignment", {
            "fields": ("assigned_to",)
        }),
        ("Timeline", {
            "fields": ("due_date", "completed_at")
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )
    
    actions = ["mark_as_completed"]
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark tasks as completed."""
        count = 0
        for task in queryset.filter(status__in=["pending", "in_progress"]):
            task.complete()
            count += 1
        
        self.message_user(request, f"Marked {count} task(s) as completed.")
    
    mark_as_completed.short_description = "Mark selected tasks as completed"


@admin.register(DealAssignmentRule)
class DealAssignmentRuleAdmin(admin.ModelAdmin):
    """Admin for DealAssignmentRule (DEAL-5)."""
    list_display = [
        "name",
        "firm",
        "assignment_type",
        "pipeline",
        "is_active",
        "priority",
        "created_at",
    ]
    list_filter = ["assignment_type", "is_active", "pipeline"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at", "last_assigned_user"]
    raw_id_fields = ["firm", "pipeline", "stage", "created_by"]
    filter_horizontal = ["target_users"]
    
    fieldsets = (
        ("Rule Information", {
            "fields": ("firm", "name", "description", "assignment_type", "is_active", "priority")
        }),
        ("Pipeline & Stage Filters", {
            "fields": ("pipeline", "stage")
        }),
        ("Assignment Configuration", {
            "fields": ("target_users", "last_assigned_user")
        }),
        ("Territory-Based Configuration", {
            "fields": ("territory_field", "territory_mapping"),
            "classes": ("collapse",)
        }),
        ("Value-Based Configuration", {
            "fields": ("min_deal_value", "max_deal_value"),
            "classes": ("collapse",)
        }),
        ("Lead Source Configuration", {
            "fields": ("lead_sources",),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(DealStageAutomation)
class DealStageAutomationAdmin(admin.ModelAdmin):
    """Admin for DealStageAutomation (DEAL-5)."""
    list_display = [
        "name",
        "firm",
        "pipeline",
        "stage",
        "trigger_type",
        "action_type",
        "is_active",
        "created_at",
    ]
    list_filter = ["trigger_type", "action_type", "is_active", "pipeline"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["firm", "pipeline", "stage", "created_by"]
    
    fieldsets = (
        ("Automation Information", {
            "fields": ("firm", "name", "description", "is_active")
        }),
        ("Trigger Configuration", {
            "fields": ("pipeline", "stage", "trigger_type")
        }),
        ("Action Configuration", {
            "fields": ("action_type", "action_config")
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )
