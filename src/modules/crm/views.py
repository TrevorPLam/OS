"""
API Views for CRM module (Pre-Sale).

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from modules.clients.permissions import DenyPortalAccess
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from modules.crm.models import Lead, Prospect, Campaign, Proposal, Contract
from modules.firm.utils import FirmScopedMixin, get_request_firm
from modules.crm.serializers import (
    LeadSerializer,
    ProspectSerializer,
    CampaignSerializer,
    ProposalSerializer,
    ContractSerializer,
)


class LeadViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Lead management (Pre-Sale).

    Leads are marketing-captured prospects before qualification.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Lead
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source', 'assigned_to', 'campaign']
    search_fields = ['company_name', 'contact_name', 'contact_email']
    ordering_fields = ['company_name', 'captured_date', 'lead_score']
    ordering = ['-captured_date']

    @action(detail=True, methods=['post'])
    def convert_to_prospect(self, request, pk=None):
        """
        Convert this lead to a prospect (sales pipeline).

        TIER 0: Firm context automatically applied to new Prospect.
        """
        lead = self.get_object()

        if lead.status == 'converted':
            return Response(
                {'error': 'Lead already converted to prospect'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            pipeline_stage='discovery',
            estimated_value=0,  # To be updated by sales team
            close_date_estimate=request.data.get('close_date_estimate'),
            assigned_to=lead.assigned_to,
            notes=f"Converted from Lead #{lead.id}"
        )

        # Mark lead as converted
        lead.status = 'converted'
        lead.qualified_date = timezone.now().date()
        lead.save()

        return Response({
            'message': 'Lead converted to prospect successfully',
            'prospect': ProspectSerializer(prospect).data
        })


class ProspectViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Prospect management (Sales Pipeline).

    Prospects are qualified sales opportunities.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Prospect
    serializer_class = ProspectSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pipeline_stage', 'assigned_to']
    search_fields = ['company_name', 'primary_contact_name', 'primary_contact_email']
    ordering_fields = ['company_name', 'close_date_estimate', 'estimated_value']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def pipeline_report(self, request):
        """
        Get pipeline summary report.

        TIER 0: Report automatically scoped to request.firm.
        """
        from django.db.models import Count, Sum
        from decimal import Decimal

        # TIER 0: self.get_queryset() is already firm-scoped
        queryset = self.get_queryset()

        pipeline_summary = queryset.values('pipeline_stage').annotate(
            count=Count('id'),
            total_value=Sum('estimated_value')
        ).order_by('pipeline_stage')

        return Response({
            'pipeline': list(pipeline_summary),
            'total_prospects': queryset.count(),
            'total_pipeline_value': queryset.aggregate(Sum('estimated_value'))['estimated_value__sum'] or Decimal('0.00')
        })


class CampaignViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Campaign management.

    Marketing campaigns for lead generation.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Campaign
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'start_date', 'leads_generated']
    ordering = ['-start_date']

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """
        Get campaign performance metrics.

        TIER 0: get_object() automatically verifies firm access.
        """
        campaign = self.get_object()

        return Response({
            'campaign': CampaignSerializer(campaign).data,
            'metrics': {
                'roi': float((campaign.revenue_generated - campaign.actual_cost) / campaign.actual_cost * 100) if campaign.actual_cost > 0 else 0,
                'cost_per_lead': float(campaign.actual_cost / campaign.leads_generated) if campaign.leads_generated > 0 else 0,
                'conversion_rate': float(campaign.opportunities_created / campaign.leads_generated * 100) if campaign.leads_generated > 0 else 0,
            }
        })


class ProposalViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Proposal management.

    Pre-sale proposals sent to prospects.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Proposal
    serializer_class = ProposalSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'prospect', 'created_by']
    search_fields = ['proposal_number', 'title']
    ordering_fields = ['proposal_number', 'created_at', 'total_value']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Mark proposal as sent to prospect.

        TIER 0: get_object() automatically verifies firm access.
        """
        from django.utils import timezone
        proposal = self.get_object()

        if proposal.status != 'draft':
            return Response(
                {'error': 'Only draft proposals can be sent'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proposal.status = 'sent'
        proposal.sent_at = timezone.now()
        proposal.save()

        return Response({'message': 'Proposal sent', 'proposal': ProposalSerializer(proposal).data})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept proposal and trigger client conversion.

        This will trigger the signal to create a Client record.

        TIER 0: get_object() automatically verifies firm access.
        """
        proposal = self.get_object()

        if proposal.status not in ['sent', 'under_review']:
            return Response(
                {'error': 'Only sent or under review proposals can be accepted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        proposal.status = 'accepted'
        proposal.save()  # This triggers the signal in modules.clients.signals

        return Response({
            'message': 'Proposal accepted - Client conversion in progress',
            'proposal': ProposalSerializer(proposal).data
        })


class ContractViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Contract management.

    Signed agreements with clients.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Contract
    serializer_class = ContractSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'client', 'proposal']
    search_fields = ['contract_number', 'title']
    ordering_fields = ['contract_number', 'start_date', 'total_value']
    ordering = ['-created_at']
