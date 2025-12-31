"""
DRF ViewSets for CRM module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.crm.models import Campaign, Contract, Lead, Proposal, Prospect
from modules.firm.utils import FirmScopedMixin

from .serializers import CampaignSerializer, ContractSerializer, LeadSerializer, ProposalSerializer, ProspectSerializer


class LeadViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Lead model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by status, source, assigned_to.
    """

    model = Lead
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "source", "assigned_to", "campaign"]
    search_fields = ["company_name", "contact_name", "contact_email"]
    ordering_fields = ["company_name", "created_at", "status"]
    ordering = ["-created_at"]


class ProspectViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Prospect model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by stage, assigned_to.
    """

    model = Prospect
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["stage", "assigned_to", "close_date_estimate"]
    search_fields = ["company_name", "contact_name", "contact_email"]
    ordering_fields = ["company_name", "created_at", "estimated_value"]
    ordering = ["-created_at"]


class CampaignViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Campaign model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by status, type.
    """

    model = Campaign
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "type"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "start_date", "created_at"]
    ordering = ["-start_date", "-created_at"]


class ProposalViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Proposal model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by prospect, client, status.
    """

    model = Proposal
    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["prospect", "client", "status", "proposal_type"]
    search_fields = ["proposal_number", "title"]
    ordering_fields = ["proposal_number", "created_at", "valid_until"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("prospect", "client", "created_by")


class ContractViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Contract model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by client, status.
    """

    model = Contract
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["client", "status", "payment_terms"]
    search_fields = ["contract_number", "title"]
    ordering_fields = ["contract_number", "created_at", "start_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("client", "proposal", "signed_by")
