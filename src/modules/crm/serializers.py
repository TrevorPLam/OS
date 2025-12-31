"""
Serializers for CRM module (Pre-Sale).
"""

from rest_framework import serializers

from modules.crm.models import Campaign, Contract, Lead, Proposal, Prospect


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
