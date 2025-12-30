"""
Lead Scoring Automation Views.

Provides API endpoints for automated lead scoring and score management.
"""

from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser, IsManager
from modules.firm.utils import FirmScopedMixin

from modules.crm.models import Lead
from modules.crm.lead_scoring import ScoringRule, ScoreAdjustment
from modules.crm.scoring_serializers import (
    ScoringRuleSerializer,
    ScoreAdjustmentSerializer,
    LeadScoreBreakdownSerializer,
    TestRuleSerializer,
    ApplyRuleSerializer,
    ManualScoreAdjustmentSerializer,
)


class ScoringRuleViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for ScoringRule management.

    Allows managers to create and manage automated lead scoring rules.
    Only managers can create/edit rules (staff can view).
    """

    model = ScoringRule
    serializer_class = ScoringRuleSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['rule_type', 'trigger', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'times_applied', 'created_at']
    ordering = ['-priority', 'name']

    def get_permissions(self):
        """
        Managers can create/edit/delete rules.
        Staff can view rules.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsStaffUser(), IsManager()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create scoring rule with firm and creator."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffUser])
    def test_rule(self, request, pk=None):
        """
        Test rule against leads without applying.

        Shows which leads would match the rule and what their score adjustment would be.

        Request body:
            {
                "lead_ids": [1, 2, 3],  # Optional, tests against all if not provided
                "event_data": {}  # Optional event data
            }

        Response:
            {
                "rule": {...},
                "total_leads_tested": 100,
                "matching_leads": 15,
                "matches": [
                    {
                        "lead_id": 1,
                        "lead_name": "...",
                        "would_apply": true,
                        "points": 10,
                        "reason": "..."
                    }
                ]
            }
        """
        rule = self.get_object()
        serializer = TestRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead_ids = serializer.validated_data.get('lead_ids')
        event_data = serializer.validated_data.get('event_data', {})

        # Get leads to test
        leads = Lead.firm_scoped.for_firm(request.firm)
        if lead_ids:
            leads = leads.filter(id__in=lead_ids)

        # Test rule against each lead
        matches = []
        matching_count = 0

        for lead in leads:
            can_apply = rule.can_apply_to_lead(lead)
            matches_conditions = rule.matches_conditions(lead, event_data)
            would_apply = can_apply and matches_conditions

            if would_apply:
                matching_count += 1

            matches.append({
                'lead_id': lead.id,
                'lead_name': f"{lead.company_name} ({lead.contact_name})",
                'current_score': lead.lead_score,
                'would_apply': would_apply,
                'can_apply': can_apply,
                'matches_conditions': matches_conditions,
                'points': rule.points if would_apply else 0,
                'new_score': min(100, max(0, lead.lead_score + rule.points)) if would_apply else lead.lead_score,
            })

        return Response({
            'rule': ScoringRuleSerializer(rule).data,
            'total_leads_tested': len(matches),
            'matching_leads': matching_count,
            'matches': matches,
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffUser, IsManager])
    def apply_rule(self, request, pk=None):
        """
        Manually apply rule to specific leads.

        Forces rule application to selected leads (even if already applied).
        Manager-only action.

        Request body:
            {
                "lead_ids": [1, 2, 3],
                "event_data": {}  # Optional
            }

        Response:
            {
                "rule": {...},
                "applied_count": 3,
                "adjustments": [...]
            }
        """
        rule = self.get_object()
        serializer = ApplyRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lead_ids = serializer.validated_data['lead_ids']
        event_data = serializer.validated_data.get('event_data', {})

        # Get leads
        leads = Lead.firm_scoped.for_firm(request.firm).filter(id__in=lead_ids)

        # Apply rule to each lead
        adjustments = []
        for lead in leads:
            adjustment = rule.apply_to_lead(
                lead=lead,
                event_data=event_data,
                applied_by=request.user
            )
            if adjustment:
                adjustments.append(adjustment)

        return Response({
            'rule': ScoringRuleSerializer(rule).data,
            'applied_count': len(adjustments),
            'adjustments': ScoreAdjustmentSerializer(adjustments, many=True).data,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsStaffUser, IsManager])
    def recalculate_scores(self, request):
        """
        Recalculate all lead scores for firm.

        Manager-only action. Recalculates scores from scratch based on
        non-decayed adjustments.

        Response:
            {
                "message": "Lead scores recalculated",
                "leads_updated": 42,
                "average_score": 57.3
            }
        """
        from django.db.models import Avg

        # Get all leads for firm
        leads = Lead.firm_scoped.for_firm(request.firm)

        # Recalculate each lead's score
        count = 0
        for lead in leads:
            lead.recalculate_score()
            count += 1

        # Calculate average score
        avg_score = leads.aggregate(avg=Avg('lead_score'))['avg'] or 0

        return Response({
            'message': 'Lead scores recalculated',
            'leads_updated': count,
            'average_score': round(avg_score, 2),
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffUser, IsManager])
    def activate(self, request, pk=None):
        """Activate scoring rule (manager-only)."""
        rule = self.get_object()
        rule.is_active = True
        rule.save(update_fields=['is_active', 'updated_at'])

        return Response(
            {'message': 'Rule activated', 'rule': ScoringRuleSerializer(rule).data},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsStaffUser, IsManager])
    def deactivate(self, request, pk=None):
        """Deactivate scoring rule (manager-only)."""
        rule = self.get_object()
        rule.is_active = False
        rule.save(update_fields=['is_active', 'updated_at'])

        return Response(
            {'message': 'Rule deactivated', 'rule': ScoringRuleSerializer(rule).data},
            status=status.HTTP_200_OK
        )


class ScoreAdjustmentViewSet(QueryTimeoutMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ScoreAdjustment (read-only).

    Adjustments are created automatically by rules or manually via Lead endpoints.
    Provides audit trail of all score changes.
    """

    queryset = ScoreAdjustment.objects.all()
    serializer_class = ScoreAdjustmentSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['lead', 'rule', 'trigger_event', 'is_decayed', 'applied_by']
    ordering_fields = ['applied_at', 'points']
    ordering = ['-applied_at']

    def get_queryset(self):
        """Filter by firm context through lead relationship."""
        queryset = super().get_queryset()

        # Filter to adjustments for leads in user's firm
        queryset = queryset.filter(lead__firm=self.request.firm)

        return queryset.select_related('lead', 'rule', 'applied_by')

    @action(detail=False, methods=['get'])
    def by_lead(self, request):
        """
        Get score adjustments for a specific lead.

        Query parameters:
            - lead_id: Lead ID (required)

        Response: List of adjustments for lead with score breakdown
        """
        lead_id = request.query_params.get('lead_id')
        if not lead_id:
            return Response(
                {'error': 'lead_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lead = Lead.firm_scoped.for_firm(request.firm).get(id=lead_id)
        except Lead.DoesNotExist:
            return Response(
                {'error': 'Lead not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get adjustments
        adjustments = self.get_queryset().filter(lead=lead)

        # Get score breakdown
        breakdown = lead.get_score_breakdown()

        return Response({
            'lead_id': lead.id,
            'lead_name': f"{lead.company_name} ({lead.contact_name})",
            'current_score': lead.lead_score,
            'total_adjustments': adjustments.count(),
            'active_adjustments': adjustments.filter(is_decayed=False).count(),
            'breakdown': LeadScoreBreakdownSerializer(breakdown, many=True).data,
            'adjustments': ScoreAdjustmentSerializer(adjustments, many=True).data,
        }, status=status.HTTP_200_OK)
