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
from modules.crm.serializers import (
    AccountContactSerializer,
    AccountRelationshipSerializer,
    AccountSerializer,
    CampaignSerializer,
    ContractSerializer,
    DealCreateSerializer,
    DealSerializer,
    DealTaskSerializer,
    IntakeFormSerializer,
    IntakeFormFieldSerializer,
    IntakeFormSubmissionSerializer,
    LeadSerializer,
    PipelineSerializer,
    PipelineStageSerializer,
    ProductConfigurationCreateSerializer,
    ProductConfigurationSerializer,
    ProductOptionSerializer,
    ProductSerializer,
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


# ============================================================================
# CPQ (Configure-Price-Quote) ViewSets - Task 3.5
# ============================================================================


class ProductViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Product management (CPQ - Task 3.5).
    
    Provides CRUD operations for products in the CPQ system.
    """
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["product_type", "status", "is_configurable", "category"]
    search_fields = ["code", "name", "description"]
    ordering_fields = ["name", "code", "base_price", "created_at"]
    ordering = ["name"]
    
    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        firm = get_request_firm(self.request)
        serializer.save(firm=firm, created_by=self.request.user)
    
    @action(detail=True, methods=["get"])
    def options(self, request, pk=None):
        """Get all options for a product."""
        product = self.get_object()
        options = product.options.all()
        serializer = ProductOptionSerializer(options, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def configurations(self, request, pk=None):
        """Get all configurations for a product."""
        product = self.get_object()
        configurations = product.configurations.all()
        serializer = ProductConfigurationSerializer(configurations, many=True)
        return Response(serializer.data)


class ProductOptionViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for ProductOption management (CPQ - Task 3.5).
    
    Provides CRUD operations for product options.
    """
    
    queryset = ProductOption.objects.all()
    serializer_class = ProductOptionSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "option_type", "required"]
    ordering_fields = ["display_order", "label"]
    ordering = ["display_order"]
    
    def get_queryset(self):
        """Filter queryset by firm through product relationship."""
        firm = get_request_firm(self.request)
        return self.queryset.filter(product__firm=firm)


class ProductConfigurationViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for ProductConfiguration management (CPQ - Task 3.5).
    
    Provides CRUD operations for product configurations with pricing calculation.
    """
    
    queryset = ProductConfiguration.objects.all()
    serializer_class = ProductConfigurationSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "status", "quote"]
    ordering_fields = ["created_at", "configuration_price"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Filter queryset by firm through product relationship."""
        firm = get_request_firm(self.request)
        return self.queryset.filter(product__firm=firm)
    
    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == "create":
            return ProductConfigurationCreateSerializer
        return ProductConfigurationSerializer
    
    def perform_create(self, serializer):
        """Set created_by on create and validate configuration."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        """Validate configuration against product rules."""
        configuration = self.get_object()
        is_valid, errors = configuration.validate_configuration()
        configuration.save()
        
        return Response({
            "is_valid": is_valid,
            "errors": errors,
            "status": configuration.status,
            "validation_errors": configuration.validation_errors,
        })
    
    @action(detail=True, methods=["post"])
    def recalculate_price(self, request, pk=None):
        """Recalculate pricing for configuration."""
        configuration = self.get_object()
        
        # Update discount if provided
        if "discount_percentage" in request.data:
            discount = request.data["discount_percentage"]
            configuration.discount_percentage = discount
        
        # Recalculate price
        configuration.calculate_price()
        configuration.save()
        
        serializer = self.get_serializer(configuration)
        return Response({
            "message": "Price recalculated successfully",
            "configuration": serializer.data,
        })
    
    @action(detail=True, methods=["post"])
    def create_quote(self, request, pk=None):
        """Create a Quote from this configuration."""
        configuration = self.get_object()
        
        # Validate configuration first
        is_valid, errors = configuration.validate_configuration()
        if not is_valid:
            return Response(
                {
                    "error": "Configuration is invalid",
                    "validation_errors": errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if quote already exists
        if configuration.quote:
            return Response(
                {"error": "Quote already exists for this configuration"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get required data from request
        client_id = request.data.get("client_id")
        quote_number = request.data.get("quote_number")
        valid_until = request.data.get("valid_until")
        
        if not client_id or not quote_number:
            return Response(
                {"error": "client_id and quote_number are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import Quote model (avoid circular import)
        from modules.pricing.models import Quote
        
        # Create quote
        firm = get_request_firm(request)
        quote = Quote.objects.create(
            firm=firm,
            quote_number=quote_number,
            client_id=client_id,
            status="draft",
            valid_until=valid_until,
            created_by=request.user,
        )
        
        # Link configuration to quote
        configuration.quote = quote
        configuration.status = "quoted"
        configuration.save()
        
        return Response({
            "message": "Quote created successfully",
            "quote_id": quote.id,
            "quote_number": quote.quote_number,
        })


# Pipeline & Deal Management ViewSets (DEAL-2)

class PipelineViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Pipeline management (DEAL-2).
    
    Pipelines represent customizable sales workflows with stages.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2.5: Portal users explicitly denied.
    """
    
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "is_default"]
    search_fields = ["name", "description"]
    ordering_fields = ["display_order", "name", "created_at"]
    ordering = ["display_order", "name"]
    
    def perform_create(self, serializer):
        """Set firm and created_by on creation."""
        serializer.save(
            firm=self.request.user.firm,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """
        Set this pipeline as the default for the firm.
        
        This will automatically unset any other default pipeline.
        """
        pipeline = self.get_object()
        
        # Check if another pipeline is currently default
        from django.db import transaction
        with transaction.atomic():
            current_default = Pipeline.objects.filter(
                firm=request.user.firm,
                is_default=True
            ).exclude(pk=pipeline.pk).first()
            
            pipeline.is_default = True
            pipeline.save()
            
            message = f"Pipeline '{pipeline.name}' set as default"
            if current_default:
                message += f" (replaced '{current_default.name}')"
            
            return Response({
                "status": message,
                "previous_default": current_default.name if current_default else None
            })
    
    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        """Get analytics for this pipeline."""
        from django.db.models import Avg, Count, Sum
        
        pipeline = self.get_object()
        active_deals = pipeline.deals.filter(is_active=True)
        
        analytics = {
            "total_deals": active_deals.count(),
            "total_value": active_deals.aggregate(Sum("value"))["value__sum"] or 0,
            "total_weighted_value": active_deals.aggregate(Sum("weighted_value"))["weighted_value__sum"] or 0,
            "average_deal_value": active_deals.aggregate(Avg("value"))["value__avg"] or 0,
            "average_probability": active_deals.aggregate(Avg("probability"))["probability__avg"] or 0,
            "stage_breakdown": [],
        }
        
        # Get deals per stage
        for stage in pipeline.stages.all():
            stage_deals = active_deals.filter(stage=stage)
            analytics["stage_breakdown"].append({
                "stage_id": stage.id,
                "stage_name": stage.name,
                "deal_count": stage_deals.count(),
                "total_value": stage_deals.aggregate(Sum("value"))["value__sum"] or 0,
                "weighted_value": stage_deals.aggregate(Sum("weighted_value"))["weighted_value__sum"] or 0,
            })
        
        return Response(analytics)


class PipelineStageViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for PipelineStage management (DEAL-2).
    
    Stages represent steps within a pipeline.
    
    TIER 0: Scoped through pipeline relationship.
    TIER 2.5: Portal users explicitly denied.
    """
    
    queryset = PipelineStage.objects.all()
    serializer_class = PipelineStageSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["pipeline", "is_active", "is_closed_won", "is_closed_lost"]
    search_fields = ["name", "description"]
    ordering_fields = ["display_order", "name"]
    ordering = ["pipeline", "display_order"]
    
    def get_queryset(self):
        """Filter stages by firm through pipeline."""
        user = self.request.user
        return PipelineStage.objects.filter(pipeline__firm=user.firm)
    
    @action(detail=True, methods=["post"])
    def reorder(self, request, pk=None):
        """Reorder stages within a pipeline."""
        stage = self.get_object()
        new_order = request.data.get("display_order")
        
        if new_order is not None:
            stage.display_order = new_order
            stage.save()
            return Response({"status": "Stage reordered"})
        
        return Response(
            {"error": "display_order is required"},
            status=status.HTTP_400_BAD_REQUEST
        )


class DealViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Deal management (DEAL-2).
    
    Deals represent sales opportunities that progress through pipeline stages.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2.5: Portal users explicitly denied.
    """
    
    queryset = Deal.objects.all()
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "pipeline",
        "stage",
        "owner",
        "account",
        "is_active",
        "is_won",
        "is_lost",
        "is_stale",
    ]
    search_fields = ["name", "description"]
    ordering_fields = ["value", "weighted_value", "expected_close_date", "created_at", "updated_at"]
    ordering = ["-created_at"]
    
    def get_serializer_class(self):
        """Use different serializer for create action."""
        if self.action == "create":
            return DealCreateSerializer
        return DealSerializer
    
    def perform_create(self, serializer):
        """Set firm and created_by on creation."""
        serializer.save()
    
    def perform_update(self, serializer):
        """Update last_activity_date on update."""
        deal = serializer.save()
        deal.update_last_activity()
    
    @action(detail=True, methods=["post"])
    def move_stage(self, request, pk=None):
        """
        Move deal to a different stage (DEAL-2 stage transition logic).
        
        Expected payload:
        {
            "stage_id": 123,
            "notes": "Moving to next stage because..."
        }
        """
        deal = self.get_object()
        stage_id = request.data.get("stage_id")
        notes = request.data.get("notes", "")
        
        if not stage_id:
            return Response(
                {"error": "stage_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Ensure stage belongs to deal's pipeline AND the firm
            new_stage = PipelineStage.objects.get(
                id=stage_id, 
                pipeline=deal.pipeline,
                pipeline__firm=request.user.firm
            )
        except PipelineStage.DoesNotExist:
            return Response(
                {"error": "Stage not found or doesn't belong to deal's pipeline"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        old_stage = deal.stage
        deal.stage = new_stage
        deal.probability = new_stage.probability  # Update probability to stage default
        deal.save()
        
        # Create activity log
        from modules.crm.models import Activity
        Activity.objects.create(
            firm=deal.firm,
            activity_type="other",
            subject=f"Deal moved from {old_stage.name} to {new_stage.name}",
            description=notes,
            activity_date=timezone.now(),
            created_by=request.user,
        )
        
        serializer = self.get_serializer(deal)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def mark_won(self, request, pk=None):
        """Mark deal as won (DEAL-2)."""
        deal = self.get_object()
        
        # Find won stage or use current
        won_stage = deal.pipeline.stages.filter(is_closed_won=True).first()
        if won_stage:
            deal.stage = won_stage
        
        deal.is_won = True
        deal.is_active = False
        deal.actual_close_date = timezone.now().date()
        deal.save()
        
        serializer = self.get_serializer(deal)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def mark_lost(self, request, pk=None):
        """Mark deal as lost (DEAL-2)."""
        deal = self.get_object()
        lost_reason = request.data.get("lost_reason", "")
        
        # Find lost stage or use current
        lost_stage = deal.pipeline.stages.filter(is_closed_lost=True).first()
        if lost_stage:
            deal.stage = lost_stage
        
        deal.is_lost = True
        deal.is_active = False
        deal.lost_reason = lost_reason
        deal.actual_close_date = timezone.now().date()
        deal.save()
        
        serializer = self.get_serializer(deal)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def convert_to_project(self, request, pk=None):
        """
        Convert deal to project (DEAL-1 conversion workflow).
        
        Expected payload (optional):
        {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "description": "Project description"
        }
        """
        deal = self.get_object()
        
        try:
            project_data = request.data or {}
            project = deal.convert_to_project(project_data)
            
            return Response({
                "status": "Deal converted to project",
                "project_id": project.id,
                "project_name": project.name,
            })
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=["get"])
    def stale(self, request):
        """Get list of stale deals (DEAL-6)."""
        stale_deals = self.get_queryset().filter(is_stale=True, is_active=True)
        serializer = self.get_serializer(stale_deals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def forecast(self, request):
        """
        Get pipeline forecast (DEAL-4 forecasting).
        
        Returns weighted value grouped by expected close date.
        """
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncMonth
        
        active_deals = self.get_queryset().filter(is_active=True)
        
        # Group by month
        forecast = active_deals.annotate(
            month=TruncMonth("expected_close_date")
        ).values("month").annotate(
            deal_count=Count("id"),
            total_value=Sum("value"),
            weighted_value=Sum("weighted_value"),
        ).order_by("month")
        
        return Response({
            "total_pipeline_value": active_deals.aggregate(Sum("value"))["value__sum"] or 0,
            "total_weighted_value": active_deals.aggregate(Sum("weighted_value"))["weighted_value__sum"] or 0,
            "monthly_forecast": list(forecast),
        })
    
    @action(detail=False, methods=["get"])
    def stale_report(self, request):
        """
        Get comprehensive stale deal report (DEAL-6).
        
        Returns statistics about stale deals including breakdown by owner, pipeline, stage, and age.
        """
        from modules.crm.deal_rotting_alerts import get_stale_deal_report
        
        # Ensure user has a firm
        if not hasattr(request.user, 'firm') or not request.user.firm:
            return Response(
                {"error": "User must be associated with a firm"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report = get_stale_deal_report(request.user.firm.id)
        
        return Response(report)
    
    @action(detail=False, methods=["post"])
    def check_stale(self, request):
        """
        Manually trigger stale deal check (DEAL-6).
        
        Checks all active deals and marks them as stale if threshold exceeded.
        """
        from modules.crm.deal_rotting_alerts import check_and_mark_stale_deals
        
        marked_count = check_and_mark_stale_deals()
        
        return Response({
            "status": "success",
            "marked_stale": marked_count,
        })
    
    @action(detail=False, methods=["post"])
    def send_stale_reminders(self, request):
        """
        Send reminders for stale deals (DEAL-6).
        
        Triggers email reminders to owners of stale deals.
        """
        from django.core.management import call_command
        from io import StringIO
        
        # Ensure user has a firm
        if not hasattr(request.user, 'firm') or not request.user.firm:
            return Response(
                {"error": "User must be associated with a firm"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dry_run = request.data.get('dry_run', True)
        
        # Capture command output
        out = StringIO()
        call_command('send_stale_deal_reminders', 
                    dry_run=dry_run,
                    firm_id=request.user.firm.id,
                    stdout=out)
        
        return Response({
            "status": "success",
            "output": out.getvalue(),
            "dry_run": dry_run,
        })


class DealTaskViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for DealTask management (DEAL-2).
    
    Tasks associated with deals.
    
    TIER 0: Scoped through deal relationship.
    TIER 2.5: Portal users explicitly denied.
    """
    
    queryset = DealTask.objects.all()
    serializer_class = DealTaskSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["deal", "status", "priority", "assigned_to"]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "priority", "created_at"]
    ordering = ["due_date", "-priority"]
    
    def get_queryset(self):
        """Filter tasks by firm through deal."""
        user = self.request.user
        return DealTask.objects.filter(deal__firm=user.firm)
    
    def perform_create(self, serializer):
        """Set created_by on creation and update deal activity."""
        task = serializer.save(created_by=self.request.user)
        task.deal.update_last_activity()
    
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark task as completed."""
        task = self.get_object()
        task.complete()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
