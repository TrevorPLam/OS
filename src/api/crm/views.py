"""
DRF ViewSets for CRM module.
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from modules.crm.models import Client, Proposal, Contract
from modules.firm.viewsets import FirmScopedViewSetMixin
from .serializers import ClientSerializer, ProposalSerializer, ContractSerializer


class ClientViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client model.

    Supports CRUD operations and filtering by status, industry, owner.
    """
    queryset = Client.objects.filter()
    serializer_class = ClientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'industry', 'owner']
    search_fields = ['company_name', 'primary_contact_name', 'primary_contact_email']
    ordering_fields = ['company_name', 'created_at', 'status']
    ordering = ['-created_at']


class ProposalViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Proposal model.

    Supports CRUD operations and filtering by client, status.
    """
    queryset = Proposal.objects.select_related('client', 'created_by')
    serializer_class = ProposalSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'status', 'created_by']
    search_fields = ['proposal_number', 'title', 'client__company_name']
    ordering_fields = ['proposal_number', 'created_at', 'valid_until']
    ordering = ['-created_at']


class ContractViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Contract model.

    Supports CRUD operations and filtering by client, status.
    """
    queryset = Contract.objects.select_related('client', 'proposal', 'signed_by')
    serializer_class = ContractSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'status', 'payment_terms']
    search_fields = ['contract_number', 'title', 'client__company_name']
    ordering_fields = ['contract_number', 'created_at', 'start_date']
    ordering = ['-created_at']
