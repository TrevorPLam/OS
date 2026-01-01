"""
API Views for CRM module (Pre-Sale).

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.crm.models import (
    Account,
    AccountContact,
    AccountRelationship,
    Campaign,
    Contract,
    IntakeForm,
    IntakeFormField,
    IntakeFormSubmission,
    Lead,
    Proposal,
    Prospect,
)
from modules.crm.serializers import (
    AccountContactSerializer,
    AccountRelationshipSerializer,
    AccountSerializer,
    CampaignSerializer,
    ContractSerializer,
    IntakeFormSerializer,
    IntakeFormFieldSerializer,
    IntakeFormSubmissionSerializer,
    LeadSerializer,
    ProposalSerializer,
    ProspectSerializer,
)
from modules.firm.utils import FirmScopedMixin, get_request_firm


class AccountViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Account management (Task 3.1).
    
    Accounts represent companies/organizations in the CRM system.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    
    model = Account
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["account_type", "status", "industry", "owner"]
    search_fields = ["name", "legal_name", "website"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]
    
    @action(detail=True, methods=["get"])
    def contacts(self, request, pk=None):
        """
        Get all contacts for this account.
        
        TIER 0: Firm context automatically applied.
        """
        account = self.get_object()
        contacts = account.contacts.filter(is_active=True)
        serializer = AccountContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def relationships(self, request, pk=None):
        """
        Get all relationships for this account.
        
        Returns both outgoing and incoming relationships.
        """
        account = self.get_object()
        outgoing = account.relationships_from.all()
        incoming = account.relationships_to.all()
        
        return Response({
            "outgoing": AccountRelationshipSerializer(outgoing, many=True).data,
            "incoming": AccountRelationshipSerializer(incoming, many=True).data,
        })


class AccountContactViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for AccountContact management (Task 3.1).
    
    Contacts are individuals associated with accounts.
    
    TIER 0: Automatically scoped to request.firm via account relationship.
    """
    
    model = AccountContact
    serializer_class = AccountContactSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["account", "is_primary_contact", "is_decision_maker", "is_active"]
    search_fields = ["first_name", "last_name", "email", "job_title"]
    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["last_name", "first_name"]
    
    def get_queryset(self):
        """
        Override to scope by firm through account relationship.
        
        TIER 0: Ensure firm isolation.
        """
        firm = get_request_firm(self.request)
        return AccountContact.objects.filter(account__firm=firm).select_related("account")


class AccountRelationshipViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for AccountRelationship management (Task 3.1).
    
    Manages relationships between accounts (e.g., parent-subsidiary).
    
    TIER 0: Automatically scoped to request.firm via from_account relationship.
    """
    
    model = AccountRelationship
    serializer_class = AccountRelationshipSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["from_account", "to_account", "relationship_type", "status"]
    ordering_fields = ["created_at", "start_date"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """
        Override to scope by firm through from_account relationship.
        
        TIER 0: Ensure firm isolation.
        """
        firm = get_request_firm(self.request)
        return AccountRelationship.objects.filter(
            from_account__firm=firm
        ).select_related("from_account", "to_account")


class LeadViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Lead management (Pre-Sale).

    Leads are marketing-captured prospects before qualification.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Lead
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "source", "assigned_to", "campaign"]
    search_fields = ["company_name", "contact_name", "contact_email"]
    ordering_fields = ["company_name", "captured_date", "lead_score"]
    ordering = ["-captured_date"]

    @action(detail=True, methods=["post"])
    def convert_to_prospect(self, request, pk=None):
        """
        Convert this lead to a prospect (sales pipeline).

        TIER 0: Firm context automatically applied to new Prospect.
        """
        lead = self.get_object()

        if lead.status == "converted":
            return Response({"error": "Lead already converted to prospect"}, status=status.HTTP_400_BAD_REQUEST)

        # TIER 0: Get firm from request
        firm = get_request_firm(request)

        # Create Prospect from Lead data
        prospect = Prospect.objects.create(
            firm=firm,  # TIER 0: Add firm context
            lead=lead,
            company_name=lead.company_name,
            industry=lead.industry,
            website=lead.website,
            primary_contact_name=lead.contact_name,
            primary_contact_email=lead.contact_email,
            primary_contact_phone=lead.contact_phone,
            primary_contact_title=lead.contact_title,
            stage="discovery",
            estimated_value=0,  # To be updated by sales team
            close_date_estimate=request.data.get("close_date_estimate"),
            assigned_to=lead.assigned_to,
            notes=f"Converted from Lead #{lead.id}",
        )

        # Mark lead as converted
        lead.status = "converted"
        lead.qualified_date = timezone.now().date()
        lead.save()

        return Response(
            {"message": "Lead converted to prospect successfully", "prospect": ProspectSerializer(prospect).data}
        )


class ProspectViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Prospect management (Sales Pipeline).

    Prospects are qualified sales opportunities.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Prospect
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["stage", "assigned_to"]
    search_fields = ["company_name", "primary_contact_name", "primary_contact_email"]
    ordering_fields = ["company_name", "close_date_estimate", "estimated_value"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["get"])
    def pipeline_report(self, request):
        """
        Get pipeline summary report.

        TIER 0: Report automatically scoped to request.firm.
        """
        from decimal import Decimal

        from django.db.models import Count, Sum

        # TIER 0: self.get_queryset() is already firm-scoped
        with self.with_query_timeout():
            queryset = self.get_queryset()

            pipeline_summary = (
                queryset.values("stage")
                .annotate(count=Count("id"), total_value=Sum("estimated_value"))
                .order_by("stage")
            )

            return Response(
                {
                    "pipeline": list(pipeline_summary),
                    "total_prospects": queryset.count(),
                    "total_pipeline_value": queryset.aggregate(Sum("estimated_value"))["estimated_value__sum"]
                    or Decimal("0.00"),
                }
            )


class CampaignViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Campaign management.

    Marketing campaigns for lead generation.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Campaign
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["type", "status", "owner"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "start_date", "leads_generated"]
    ordering = ["-start_date"]

    @action(detail=True, methods=["get"])
    def performance(self, request, pk=None):
        """
        Get campaign performance metrics.

        TIER 0: get_object() automatically verifies firm access.
        """
        campaign = self.get_object()

        return Response(
            {
                "campaign": CampaignSerializer(campaign).data,
                "metrics": {
                    "roi": (
                        float((campaign.revenue_generated - campaign.actual_cost) / campaign.actual_cost * 100)
                        if campaign.actual_cost > 0
                        else 0
                    ),
                    "cost_per_lead": (
                        float(campaign.actual_cost / campaign.leads_generated) if campaign.leads_generated > 0 else 0
                    ),
                    "conversion_rate": (
                        float(campaign.opportunities_created / campaign.leads_generated * 100)
                        if campaign.leads_generated > 0
                        else 0
                    ),
                },
            }
        )


class ProposalViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Proposal management.

    Pre-sale proposals sent to prospects.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Proposal
    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "prospect", "created_by"]
    search_fields = ["proposal_number", "title"]
    ordering_fields = ["proposal_number", "created_at", "total_value"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        Mark proposal as sent to prospect.

        TIER 0: get_object() automatically verifies firm access.
        """
        from django.utils import timezone

        proposal = self.get_object()

        if proposal.status != "draft":
            return Response({"error": "Only draft proposals can be sent"}, status=status.HTTP_400_BAD_REQUEST)

        proposal.status = "sent"
        proposal.sent_at = timezone.now()
        proposal.save()

        return Response({"message": "Proposal sent", "proposal": ProposalSerializer(proposal).data})

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Accept proposal and trigger client conversion.

        This will trigger the signal to create a Client record.

        TIER 0: get_object() automatically verifies firm access.
        """
        proposal = self.get_object()

        if proposal.status not in ["sent", "under_review"]:
            return Response(
                {"error": "Only sent or under review proposals can be accepted"}, status=status.HTTP_400_BAD_REQUEST
            )

        proposal.status = "accepted"
        proposal.save()  # This triggers the signal in modules.clients.signals

        return Response(
            {
                "message": "Proposal accepted - Client conversion in progress",
                "proposal": ProposalSerializer(proposal).data,
            }
        )


class ContractViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Contract management.

    Signed agreements with clients.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Contract
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "client", "proposal"]
    search_fields = ["contract_number", "title"]
    ordering_fields = ["contract_number", "start_date", "total_value"]
    ordering = ["-created_at"]


class IntakeFormViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Intake Forms (Task 3.4).
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations for intake forms with embedded fields.
    """
    
    model = IntakeForm
    serializer_class = IntakeFormSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "qualification_enabled", "auto_create_lead"]
    search_fields = ["name", "title", "description"]
    ordering_fields = ["name", "submission_count", "created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Override to prefetch fields for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.prefetch_related("fields")


class IntakeFormFieldViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Intake Form Fields (Task 3.4).
    
    Note: No FirmScopedMixin as fields belong to forms, not directly to firms.
    Access control through form ownership.
    """
    
    model = IntakeFormField
    serializer_class = IntakeFormFieldSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["form", "field_type", "required", "scoring_enabled"]
    search_fields = ["label"]
    ordering_fields = ["order", "created_at"]
    ordering = ["form", "order"]
    
    def get_queryset(self):
        """Filter to only show fields from forms in user's firm."""
        user = self.request.user
        return IntakeFormField.objects.filter(form__firm=user.firm).select_related("form")


class IntakeFormSubmissionViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Intake Form Submissions (Task 3.4).
    
    Note: No FirmScopedMixin as submissions belong to forms, not directly to firms.
    Access control through form ownership.
    """
    
    model = IntakeFormSubmission
    serializer_class = IntakeFormSubmissionSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["form", "status", "is_qualified"]
    search_fields = ["submitter_email", "submitter_name", "submitter_company"]
    ordering_fields = ["qualification_score", "created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Filter to only show submissions from forms in user's firm."""
        user = self.request.user
        return IntakeFormSubmission.objects.filter(form__firm=user.firm).select_related(
            "form", "lead", "prospect", "reviewed_by"
        )
    
    @action(detail=True, methods=["post"])
    def calculate_score(self, request, pk=None):
        """Calculate qualification score for this submission."""
        submission = self.get_object()
        score = submission.calculate_qualification_score()
        serializer = self.get_serializer(submission)
        return Response({
            "score": score,
            "is_qualified": submission.is_qualified,
            "submission": serializer.data
        })
    
    @action(detail=True, methods=["post"])
    def create_lead(self, request, pk=None):
        """Create a Lead record from this submission."""
        submission = self.get_object()
        if submission.lead:
            return Response(
                {"error": "Lead already exists for this submission"},
                status=status.HTTP_400_BAD_REQUEST
            )
        lead = submission.create_lead()
        from modules.crm.serializers import LeadSerializer
        lead_serializer = LeadSerializer(lead)
        return Response({
            "message": "Lead created successfully",
            "lead": lead_serializer.data
        })
