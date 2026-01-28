"""
Serializers for CRM module (Pre-Sale).
"""

from rest_framework import serializers

from modules.crm.models import (
    Account,
    AccountContact,
    AccountRelationship,
    Campaign,
    Contract,
    Deal,
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


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model (Task 3.1)."""
    
    owner_name = serializers.SerializerMethodField()
    parent_account_name = serializers.CharField(source="parent_account.name", read_only=True)
    contact_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            "id",
            "firm",
            "name",
            "legal_name",
            "account_type",
            "status",
            "industry",
            "website",
            "employee_count",
            "annual_revenue",
            "billing_address_line1",
            "billing_address_line2",
            "billing_city",
            "billing_state",
            "billing_postal_code",
            "billing_country",
            "shipping_address_line1",
            "shipping_address_line2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "owner",
            "owner_name",
            "parent_account",
            "parent_account_name",
            "contact_count",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "contact_count"]
    
    def get_owner_name(self, obj):
        """Get owner's name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return None
    
    def get_contact_count(self, obj):
        """Get count of contacts for this account."""
        return obj.contacts.count()


class AccountContactSerializer(serializers.ModelSerializer):
    """Serializer for AccountContact model (Task 3.1)."""
    
    account_name = serializers.CharField(source="account.name", read_only=True)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = AccountContact
        fields = [
            "id",
            "account",
            "account_name",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "mobile_phone",
            "job_title",
            "department",
            "is_primary_contact",
            "is_decision_maker",
            "preferred_contact_method",
            "opt_out_marketing",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "full_name"]


class AccountRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for AccountRelationship model (Task 3.1)."""
    
    from_account_name = serializers.CharField(source="from_account.name", read_only=True)
    to_account_name = serializers.CharField(source="to_account.name", read_only=True)
    
    class Meta:
        model = AccountRelationship
        fields = [
            "id",
            "from_account",
            "from_account_name",
            "to_account",
            "to_account_name",
            "relationship_type",
            "status",
            "start_date",
            "end_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeadSerializer(serializers.ModelSerializer):
    """Serializer for Lead model."""

    assigned_to_name = serializers.SerializerMethodField()
    campaign_name = serializers.CharField(source="campaign.name", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id",
            "company_name",
            "industry",
            "website",
            "contact_name",
            "contact_email",
            "contact_phone",
            "contact_title",
            "source",
            "status",
            "lead_score",
            "campaign",
            "campaign_name",
            "assigned_to",
            "assigned_to_name",
            "captured_date",
            "first_contacted",
            "qualified_date",
            "created_at",
            "updated_at",
            "notes",
        ]
        read_only_fields = ["id", "captured_date", "created_at", "updated_at"]

    def get_assigned_to_name(self, obj):
        """Get assigned sales rep's name."""
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
        return None


class ProspectSerializer(serializers.ModelSerializer):
    """Serializer for Prospect model."""

    assigned_to_name = serializers.SerializerMethodField()
    lead_company = serializers.CharField(source="lead.company_name", read_only=True)

    class Meta:
        model = Prospect
        fields = [
            "id",
            "lead",
            "lead_company",
            "company_name",
            "industry",
            "website",
            "employee_count",
            "annual_revenue",
            "primary_contact_name",
            "primary_contact_email",
            "primary_contact_phone",
            "primary_contact_title",
            "street_address",
            "city",
            "state",
            "postal_code",
            "country",
            "stage",
            "probability",
            "estimated_value",
            "close_date_estimate",
            "assigned_to",
            "assigned_to_name",
            "created_at",
            "updated_at",
            "last_activity_date",
            "won_date",
            "lost_date",
            "lost_reason",
            "notes",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "won_date", "lost_date"]

    def get_assigned_to_name(self, obj):
        """Get assigned account executive's name."""
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()
        return None


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model."""

    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "description",
            "type",
            "status",
            "start_date",
            "end_date",
            "budget",
            "actual_cost",
            "targeted_clients",
            "target_leads",
            "leads_generated",
            "opportunities_created",
            "clients_contacted",
            "renewal_proposals_sent",
            "renewals_won",
            "revenue_generated",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "leads_generated",
            "clients_contacted",
            "renewal_proposals_sent",
            "renewals_won",
            "created_at",
            "updated_at",
        ]

    def get_owner_name(self, obj):
        """Get campaign owner's name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return None


class ProposalSerializer(serializers.ModelSerializer):
    """Serializer for Proposal model."""

    prospect_name = serializers.CharField(source="prospect.company_name", read_only=True, allow_null=True)
    client_name = serializers.CharField(source="client.company_name", read_only=True, allow_null=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            "id",
            "proposal_type",
            "prospect",
            "prospect_name",
            "client",
            "client_name",
            "created_by",
            "created_by_name",
            "proposal_number",
            "title",
            "description",
            "status",
            "total_value",
            "currency",
            "valid_until",
            "estimated_start_date",
            "estimated_end_date",
            "converted_to_engagement",
            "auto_create_project",
            "enable_portal_on_acceptance",
            "sent_at",
            "accepted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "converted_to_engagement",
            "sent_at",
            "accepted_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Validate proposal has either prospect OR client based on type."""
        proposal_type = data.get("proposal_type", "prospective_client")
        prospect = data.get("prospect")
        client = data.get("client")

        if proposal_type == "prospective_client":
            if not prospect:
                raise serializers.ValidationError("Prospective client proposals must have a prospect.")
            if client:
                raise serializers.ValidationError("Prospective client proposals cannot have a client.")
        else:  # update_client or renewal_client
            if not client:
                raise serializers.ValidationError(
                    f"{dict(Proposal.TYPE_CHOICES)[proposal_type]} proposals must have a client."
                )
            if prospect:
                raise serializers.ValidationError(
                    f"{dict(Proposal.TYPE_CHOICES)[proposal_type]} proposals cannot have a prospect."
                )

        return data

    def get_created_by_name(self, obj):
        """Get proposal creator's name."""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
        return None


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for Contract model."""

    client_name = serializers.CharField(source="client.company_name", read_only=True)
    proposal_number = serializers.CharField(source="proposal.proposal_number", read_only=True)
    signed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "client",
            "client_name",
            "proposal",
            "proposal_number",
            "signed_by",
            "signed_by_name",
            "contract_number",
            "title",
            "description",
            "status",
            "total_value",
            "currency",
            "payment_terms",
            "start_date",
            "end_date",
            "signed_date",
            "contract_file_url",
            "created_at",
            "updated_at",
            "notes",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_signed_by_name(self, obj):
        """Get signer's name."""
        if obj.signed_by:
            return f"{obj.signed_by.first_name} {obj.signed_by.last_name}".strip()
        return None


class IntakeFormFieldSerializer(serializers.ModelSerializer):
    """Serializer for IntakeFormField (Task 3.4)."""
    
    class Meta:
        model = IntakeFormField
        fields = [
            "id",
            "form",
            "label",
            "field_type",
            "placeholder",
            "help_text",
            "required",
            "order",
            "options",
            "scoring_enabled",
            "scoring_rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class IntakeFormSerializer(serializers.ModelSerializer):
    """Serializer for IntakeForm (Task 3.4)."""
    
    fields = IntakeFormFieldSerializer(many=True, read_only=True)
    default_owner_name = serializers.CharField(source="default_owner.get_full_name", read_only=True, allow_null=True)
    
    class Meta:
        model = IntakeForm
        fields = [
            "id",
            "firm",
            "name",
            "title",
            "description",
            "status",
            "qualification_enabled",
            "qualification_threshold",
            "auto_create_lead",
            "auto_create_prospect",
            "default_owner",
            "default_owner_name",
            "notify_on_submission",
            "notification_emails",
            "thank_you_title",
            "thank_you_message",
            "redirect_url",
            "submission_count",
            "qualified_count",
            "fields",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = ["id", "submission_count", "qualified_count", "created_at", "updated_at"]


class IntakeFormSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for IntakeFormSubmission (Task 3.4)."""
    
    form_name = serializers.CharField(source="form.name", read_only=True)
    lead_email = serializers.CharField(source="lead.email", read_only=True, allow_null=True)
    prospect_company = serializers.CharField(source="prospect.company", read_only=True, allow_null=True)
    
    class Meta:
        model = IntakeFormSubmission
        fields = [
            "id",
            "form",
            "form_name",
            "lead",
            "lead_email",
            "prospect",
            "prospect_company",
            "responses",
            "qualification_score",
            "status",
            "is_qualified",
            "submitter_email",
            "submitter_name",
            "submitter_phone",
            "submitter_company",
            "ip_address",
            "user_agent",
            "referrer",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "qualification_score",
            "is_qualified",
            "ip_address",
            "user_agent",
            "referrer",
            "created_at",
            "updated_at",
        ]
    
    def validate_responses(self, value):
        """Validate that responses match the form's field definitions."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Responses must be a dictionary")
        return value


# ============================================================================
# CPQ (Configure-Price-Quote) Serializers - Task 3.5
# ============================================================================


class ProductOptionSerializer(serializers.ModelSerializer):
    """Serializer for ProductOption model (CPQ)."""
    
    class Meta:
        model = ProductOption
        fields = [
            "id",
            "product",
            "code",
            "label",
            "description",
            "option_type",
            "required",
            "display_order",
            "values",
            "price_modifier",
            "price_multiplier",
            "dependency_rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model (CPQ)."""
    
    options = ProductOptionSerializer(many=True, read_only=True)
    options_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    
    class Meta:
        model = Product
        fields = [
            "id",
            "firm",
            "code",
            "name",
            "description",
            "product_type",
            "status",
            "base_price",
            "currency",
            "is_configurable",
            "configuration_schema",
            "category",
            "tags",
            "options",
            "options_count",
            "created_at",
            "created_by",
            "created_by_name",
            "updated_at",
        ]
        read_only_fields = ["created_at", "created_by", "updated_at"]
    
    def get_options_count(self, obj):
        """Get count of product options."""
        return obj.options.count()


class ProductConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for ProductConfiguration model (CPQ)."""
    
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    quote_number = serializers.CharField(source="quote.quote_number", read_only=True)
    
    class Meta:
        model = ProductConfiguration
        fields = [
            "id",
            "product",
            "product_name",
            "product_code",
            "configuration_name",
            "selected_options",
            "base_price",
            "configuration_price",
            "price_breakdown",
            "discount_percentage",
            "discount_amount",
            "status",
            "validation_errors",
            "quote",
            "quote_number",
            "created_at",
            "created_by",
            "created_by_name",
            "updated_at",
        ]
        read_only_fields = [
            "base_price",
            "configuration_price",
            "price_breakdown",
            "discount_amount",
            "validation_errors",
            "created_at",
            "created_by",
            "updated_at",
        ]
    
    def validate_selected_options(self, value):
        """Validate selected options against product's available options."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Selected options must be a dictionary")
        return value


class ProductConfigurationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ProductConfiguration with validation."""
    
    class Meta:
        model = ProductConfiguration
        fields = [
            "product",
            "configuration_name",
            "selected_options",
            "discount_percentage",
        ]
    
    def create(self, validated_data):
        """Create configuration and validate it."""
        configuration = ProductConfiguration(**validated_data)
        configuration.base_price = configuration.product.base_price
        configuration.save()  # This triggers price calculation
        configuration.validate_configuration()
        configuration.save()
        return configuration


# Pipeline & Deal Management Serializers (DEAL-2)

class PipelineStageSerializer(serializers.ModelSerializer):
    """Serializer for PipelineStage model."""
    
    deal_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PipelineStage
        fields = [
            "id",
            "pipeline",
            "name",
            "description",
            "probability",
            "is_active",
            "is_closed_won",
            "is_closed_lost",
            "display_order",
            "auto_tasks",
            "deal_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "deal_count"]
    
    def get_deal_count(self, obj):
        """Get count of active deals in this stage."""
        return obj.deals.filter(is_active=True).count()


class PipelineSerializer(serializers.ModelSerializer):
    """Serializer for Pipeline model."""
    
    stages = PipelineStageSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    deal_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Pipeline
        fields = [
            "id",
            "firm",
            "name",
            "description",
            "is_active",
            "is_default",
            "display_order",
            "stages",
            "deal_count",
            "total_value",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "firm", "created_at", "updated_at", "created_by", "created_by_name"]
    
    def get_deal_count(self, obj):
        """Get count of active deals in this pipeline."""
        return obj.deals.filter(is_active=True).count()
    
    def get_total_value(self, obj):
        """Get total value of active deals in this pipeline."""
        from django.db.models import Sum
        result = obj.deals.filter(is_active=True).aggregate(total=Sum("value"))
        return result["total"] or 0


class DealTaskSerializer(serializers.ModelSerializer):
    """Serializer for DealTask model."""
    
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = DealTask
        fields = [
            "id",
            "deal",
            "title",
            "description",
            "priority",
            "status",
            "assigned_to",
            "assigned_to_name",
            "due_date",
            "completed_at",
            "is_overdue",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by", "created_by_name", "completed_at"]
    
    def get_is_overdue(self, obj):
        """Check if task is overdue."""
        if obj.due_date and obj.status not in ["completed", "cancelled"]:
            from django.utils import timezone
            return obj.due_date < timezone.now().date()
        return False


class DealSerializer(serializers.ModelSerializer):
    """Serializer for Deal model."""
    
    pipeline_name = serializers.CharField(source="pipeline.name", read_only=True)
    stage_name = serializers.CharField(source="stage.name", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    contact_name = serializers.CharField(source="contact.full_name", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    tasks = DealTaskSerializer(many=True, read_only=True)
    team_member_names = serializers.SerializerMethodField()
    days_in_stage = serializers.SerializerMethodField()
    days_since_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            "id",
            "firm",
            "pipeline",
            "pipeline_name",
            "stage",
            "stage_name",
            "name",
            "description",
            "account",
            "account_name",
            "contact",
            "contact_name",
            "value",
            "currency",
            "probability",
            "weighted_value",
            "expected_close_date",
            "actual_close_date",
            "owner",
            "owner_name",
            "team_members",
            "team_member_names",
            "split_percentage",
            "source",
            "campaign",
            "is_active",
            "is_won",
            "is_lost",
            "lost_reason",
            "last_activity_date",
            "is_stale",
            "stale_days_threshold",
            "days_since_activity",
            "converted_to_project",
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "tags",
            "tasks",
            "days_in_stage",
        ]
        read_only_fields = [
            "id",
            "firm",
            "weighted_value",
            "is_won",
            "is_lost",
            "actual_close_date",
            "is_stale",
            "converted_to_project",
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
    
    def get_team_member_names(self, obj):
        """Get list of team member names."""
        return [member.get_full_name() for member in obj.team_members.all()]
    
    def get_days_in_stage(self, obj):
        """Calculate days in current stage."""
        from django.utils import timezone
        return (timezone.now().date() - obj.updated_at.date()).days
    
    def get_days_since_activity(self, obj):
        """Calculate days since last activity."""
        if obj.last_activity_date:
            from django.utils import timezone
            return (timezone.now().date() - obj.last_activity_date).days
        return None
    
    def validate(self, data):
        """Validate deal data."""
        # Ensure stage belongs to pipeline
        if "stage" in data and "pipeline" in data:
            if data["stage"].pipeline != data["pipeline"]:
                raise serializers.ValidationError({
                    "stage": "Stage must belong to the selected pipeline."
                })
        
        # Ensure account and contact belong to same firm
        if "account" in data and data.get("account"):
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                firm = request.user.firm
                if data["account"].firm != firm:
                    raise serializers.ValidationError({
                        "account": "Account must belong to your firm."
                    })
        
        # Validate probability range
        if "probability" in data:
            if not 0 <= data["probability"] <= 100:
                raise serializers.ValidationError({
                    "probability": "Probability must be between 0 and 100."
                })
        
        return data


class DealCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Deal with minimal fields."""
    
    class Meta:
        model = Deal
        fields = [
            "pipeline",
            "stage",
            "name",
            "description",
            "account",
            "contact",
            "value",
            "currency",
            "probability",
            "expected_close_date",
            "owner",
            "source",
            "campaign",
            "tags",
        ]
    
    def validate(self, data):
        """Validate deal data."""
        # Ensure stage belongs to pipeline
        if data["stage"].pipeline != data["pipeline"]:
            raise serializers.ValidationError({
                "stage": "Stage must belong to the selected pipeline."
            })
        
        return data
    
    def create(self, validated_data):
        """Create deal with firm from request."""
        request = self.context.get("request")
        validated_data["firm"] = request.user.firm
        validated_data["created_by"] = request.user
        
        # Set initial last_activity_date
        from django.utils import timezone
        validated_data["last_activity_date"] = timezone.now().date()
        
        return super().create(validated_data)


# ============================================================================
# Enrichment Serializers
# ============================================================================


class EnrichmentProviderSerializer(serializers.ModelSerializer):
    """Serializer for EnrichmentProvider model."""

    success_rate = serializers.FloatField(read_only=True)
    provider_display = serializers.CharField(source="get_provider_display", read_only=True)

    class Meta:
        from .models import EnrichmentProvider
        model = EnrichmentProvider
        fields = [
            "id",
            "provider",
            "provider_display",
            "is_enabled",
            "auto_enrich_on_create",
            "auto_refresh_enabled",
            "refresh_interval_hours",
            "total_enrichments",
            "successful_enrichments",
            "failed_enrichments",
            "success_rate",
            "last_used_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_enrichments",
            "successful_enrichments",
            "failed_enrichments",
            "success_rate",
            "last_used_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create provider with firm from request."""
        request = self.context.get("request")
        validated_data["firm"] = request.user.firm
        validated_data["created_by"] = request.user
        return super().create(validated_data)


class EnrichmentProviderDetailSerializer(EnrichmentProviderSerializer):
    """Detailed serializer for EnrichmentProvider with API credentials."""

    class Meta(EnrichmentProviderSerializer.Meta):
        fields = EnrichmentProviderSerializer.Meta.fields + [
            "api_key",
            "api_secret",
            "additional_config",
        ]


class ContactEnrichmentSerializer(serializers.ModelSerializer):
    """Serializer for ContactEnrichment model."""

    provider_name = serializers.CharField(
        source="enrichment_provider.get_provider_display",
        read_only=True
    )
    data_completeness = serializers.FloatField(read_only=True)
    contact_email = serializers.CharField(read_only=True)
    needs_refresh = serializers.SerializerMethodField()

    class Meta:
        from .models import ContactEnrichment
        model = ContactEnrichment
        fields = [
            "id",
            "account_contact",
            "client_contact",
            "enrichment_provider",
            "provider_name",
            "company_name",
            "company_domain",
            "company_industry",
            "company_size",
            "company_revenue",
            "company_description",
            "company_logo_url",
            "company_location",
            "company_founded_year",
            "contact_title",
            "contact_seniority",
            "contact_role",
            "linkedin_url",
            "twitter_url",
            "facebook_url",
            "github_url",
            "technologies",
            "confidence_score",
            "fields_enriched",
            "fields_missing",
            "data_completeness",
            "contact_email",
            "last_enriched_at",
            "next_refresh_at",
            "refresh_count",
            "is_stale",
            "needs_refresh",
            "enrichment_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "provider_name",
            "data_completeness",
            "contact_email",
            "last_enriched_at",
            "refresh_count",
            "needs_refresh",
            "created_at",
            "updated_at",
        ]

    def get_needs_refresh(self, obj):
        """Check if enrichment needs refresh."""
        return obj.needs_refresh()


class ContactEnrichmentDetailSerializer(ContactEnrichmentSerializer):
    """Detailed serializer for ContactEnrichment with raw data."""

    class Meta(ContactEnrichmentSerializer.Meta):
        fields = ContactEnrichmentSerializer.Meta.fields + ["raw_data"]


class EnrichmentQualityMetricSerializer(serializers.ModelSerializer):
    """Serializer for EnrichmentQualityMetric model."""

    provider_name = serializers.CharField(
        source="enrichment_provider.get_provider_display",
        read_only=True
    )
    success_rate = serializers.FloatField(read_only=True)

    class Meta:
        from .models import EnrichmentQualityMetric
        model = EnrichmentQualityMetric
        fields = [
            "id",
            "enrichment_provider",
            "provider_name",
            "metric_date",
            "total_enrichments",
            "successful_enrichments",
            "failed_enrichments",
            "success_rate",
            "average_completeness",
            "average_confidence",
            "field_success_rates",
            "average_response_time_ms",
            "error_types",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "provider_name",
            "success_rate",
            "created_at",
        ]


class EnrichContactRequestSerializer(serializers.Serializer):
    """Serializer for manual contact enrichment requests."""

    email = serializers.EmailField(required=True, help_text="Contact email address")
    providers = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of provider names to use (optional)"
    )

    def validate_providers(self, value):
        """Validate provider names."""
        from .models import EnrichmentProvider

        valid_providers = [choice[0] for choice in EnrichmentProvider.PROVIDER_CHOICES]
        for provider in value:
            if provider not in valid_providers:
                raise serializers.ValidationError(
                    f"Invalid provider: {provider}. "
                    f"Valid options: {', '.join(valid_providers)}"
                )
        return value


class EnrichLinkedInRequestSerializer(serializers.Serializer):
    """Serializer for LinkedIn profile enrichment requests."""

    linkedin_url = serializers.URLField(
        required=True,
        help_text="LinkedIn profile URL"
    )

    def validate_linkedin_url(self, value):
        """Validate LinkedIn URL."""
        if "linkedin.com/in/" not in value:
            raise serializers.ValidationError(
                "Invalid LinkedIn URL. Must be a profile URL (linkedin.com/in/...)"
            )
        return value
