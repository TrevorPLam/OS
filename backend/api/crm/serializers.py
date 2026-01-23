"""
Serializers for CRM entities.

Aligns serializer fields with the current CRM/Clients models after the
post-sale Client moved to modules.clients.
"""

import re

from django.utils import timezone
from rest_framework import serializers

from modules.clients.models import Client
from modules.crm.models import Contract, IntakeForm, IntakeFormField, IntakeFormSubmission, Proposal


class ClientSerializer(serializers.ModelSerializer):
    """Enhanced Client serializer with validation."""

    class Meta:
        model = Client
        fields = [
            "id",
            "firm",
            "source_prospect",
            "source_proposal",
            "company_name",
            "industry",
            "primary_contact_name",
            "primary_contact_email",
            "primary_contact_phone",
            "street_address",
            "city",
            "state",
            "postal_code",
            "country",
            "website",
            "employee_count",
            "status",
            "account_manager",
            "portal_enabled",
            "total_lifetime_value",
            "active_projects_count",
            "client_since",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_primary_contact_email(self, value):
        """Validate email format."""
        if value and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            raise serializers.ValidationError("Invalid email format")
        return value.lower() if value else value

    def validate_primary_contact_phone(self, value):
        """Validate phone number format."""
        if value:
            cleaned = re.sub(r"[\s\-\(\)\.]", "", value)
            if not re.match(r"^\+?[\d]{10,15}$", cleaned):
                raise serializers.ValidationError("Phone number must be 10-15 digits, optionally starting with +")
        return value

    def validate_website(self, value):
        """Validate website URL."""
        if value and not re.match(r"^https?://", value):
            raise serializers.ValidationError("Website must start with http:// or https://")
        return value


class ProposalSerializer(serializers.ModelSerializer):
    """Enhanced Proposal serializer with validation."""

    client_name = serializers.CharField(source="client.company_name", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            "id",
            "firm",
            "proposal_type",
            "prospect",
            "client",
            "client_name",
            "proposal_number",
            "title",
            "description",
            "total_value",
            "currency",
            "status",
            "valid_until",
            "estimated_start_date",
            "estimated_end_date",
            "created_by",
            "sent_at",
            "accepted_at",
            "converted_to_engagement",
            "auto_create_project",
            "enable_portal_on_acceptance",
            "notes",
            "created_at",
            "updated_at",
            "is_expired",
        ]
        read_only_fields = ["created_at", "updated_at", "sent_at", "accepted_at", "proposal_number"]

    def get_is_expired(self, obj):
        """Check if proposal has expired."""
        if obj.valid_until and obj.status in ["draft", "sent"]:
            return obj.valid_until < timezone.now().date()
        return False

    def validate_total_value(self, value):
        """Validate total value is positive."""
        if value and value <= 0:
            raise serializers.ValidationError("Estimated value must be greater than 0")
        return value

    def validate_valid_until(self, value):
        """Validate valid_until is in the future."""
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Valid until date must be in the future")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        if self.instance and attrs.get("status") == "sent":
            if self.instance.valid_until and self.instance.valid_until < timezone.now().date():
                raise serializers.ValidationError(
                    {"status": "Cannot send expired proposal. Update valid_until date first."}
                )
        return attrs


class ContractSerializer(serializers.ModelSerializer):
    """Enhanced Contract serializer with validation."""

    client_name = serializers.CharField(source="client.company_name", read_only=True)
    proposal_number = serializers.CharField(source="proposal.proposal_number", read_only=True, allow_null=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            "id",
            "firm",
            "client",
            "client_name",
            "proposal",
            "proposal_number",
            "contract_number",
            "title",
            "description",
            "total_value",
            "currency",
            "status",
            "payment_terms",
            "start_date",
            "end_date",
            "signed_date",
            "signed_by",
            "contract_file_url",
            "notes",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["created_at", "updated_at", "contract_number"]

    def get_is_active(self, obj):
        """Check if contract is currently active."""
        today = timezone.now().date()
        return obj.status == "active" and obj.start_date <= today <= obj.end_date

    def validate_total_value(self, value):
        """Validate contract value is positive."""
        if value and value <= 0:
            raise serializers.ValidationError("Contract value must be greater than 0")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        start_date = attrs.get("start_date") or (self.instance.start_date if self.instance else None)
        end_date = attrs.get("end_date") or (self.instance.end_date if self.instance else None)

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date"})

        proposal = attrs.get("proposal")
        client = attrs.get("client") or (self.instance.client if self.instance else None)
        if proposal and client and proposal.client_id != client.id:
            raise serializers.ValidationError({"proposal": "Proposal must belong to the same client as the contract"})

        signed_date = attrs.get("signed_date")
        if signed_date:
            if start_date and signed_date > start_date:
                raise serializers.ValidationError({"signed_date": "Signed date cannot be after start date"})

        return attrs


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
    default_owner_name = serializers.CharField(source="default_owner.get_full_name", read_only=True)
    
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
