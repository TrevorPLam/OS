"""
DRF ViewSets for CRM module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from modules.crm.models import Lead, Prospect, Campaign, Proposal, Contract
from modules.firm.utils import FirmScopedMixin
from .serializers import LeadSerializer, ProspectSerializer, CampaignSerializer, ProposalSerializer, ContractSerializer


class LeadViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Lead model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by status, source, assigned_to.
    """
    model = Lead
    serializer_class = LeadSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source', 'assigned_to', 'campaign']
    search_fields = ['company_name', 'contact_name', 'contact_email']
    ordering_fields = ['company_name', 'created_at', 'status']
    ordering = ['-created_at']


class ProspectViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Prospect model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by pipeline_stage, assigned_to.
    """
    model = Prospect
    serializer_class = ProspectSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pipeline_stage', 'assigned_to', 'close_date_estimate']
    search_fields = ['company_name', 'contact_name', 'contact_email']
    ordering_fields = ['company_name', 'created_at', 'estimated_value']
    ordering = ['-created_at']


class CampaignViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Campaign model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by status, type.
    """
    model = Campaign
    serializer_class = CampaignSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'start_date', 'created_at']
    ordering = ['-start_date', '-created_at']


class ProposalViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Proposal model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by prospect, client, status.
    """
    model = Proposal
    serializer_class = ProposalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['prospect', 'client', 'status', 'proposal_type']
    search_fields = ['proposal_number', 'title']
    ordering_fields = ['proposal_number', 'created_at', 'valid_until']
    ordering = ['-created_at']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('prospect', 'client', 'created_by')


class ContractViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Contract model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    Supports CRUD operations and filtering by client, status.
    """
    model = Contract
    serializer_class = ContractSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'status', 'payment_terms']
    search_fields = ['contract_number', 'title']
    ordering_fields = ['contract_number', 'created_at', 'start_date']
    ordering = ['-created_at']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('client', 'proposal', 'signed_by')
