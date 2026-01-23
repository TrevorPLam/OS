"""
Support Module Views.

Provides API endpoints for ticketing, SLA tracking, and customer surveys.
Implements HubSpot Service Hub-like functionality.
"""

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.query_guards import QueryTimeoutMixin
from modules.auth.role_permissions import IsStaffUser, IsManager
from modules.firm.utils import FirmScopedMixin

from .models import SLAPolicy, Ticket, TicketComment, Survey, SurveyResponse
from .serializers import (
    SLAPolicySerializer,
    TicketSerializer,
    TicketCommentSerializer,
    SurveySerializer,
    SurveyResponseSerializer,
)


class SLAPolicyViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SLA Policy management.

    SLA policies define response and resolution time targets for tickets.
    Only managers can create/edit SLA policies.
    """

    model = SLAPolicy
    serializer_class = SLAPolicySerializer
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["priority", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "priority", "created_at"]
    ordering = ["priority", "name"]

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )


class TicketViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Support Ticket management.

    Tickets can be created by staff or through client portal.
    Staff can view all tickets; portal users can only view their own.
    """

    model = Ticket
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]  # Both staff and portal users
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "priority", "channel", "assigned_to", "client"]
    search_fields = ["ticket_number", "subject", "description", "contact_name", "contact_email"]
    ordering_fields = ["created_at", "updated_at", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by firm context and portal permissions."""
        queryset = super().get_queryset()

        # Portal users can only see their own tickets
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            # Filter to tickets for clients the portal user has access to
            queryset = queryset.filter(client__in=self.request.portal_clients)

        return queryset.select_related(
            "client",
            "assigned_to",
            "sla_policy",
        )

    def perform_create(self, serializer):
        """Create ticket (auto-assigns ticket number and SLA policy)."""
        serializer.save(firm=self.request.firm)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def assign(self, request, pk=None):
        """
        Assign ticket to a staff member.

        Staff only action.
        """
        ticket = self.get_object()
        assigned_to_id = request.data.get("assigned_to")
        assigned_team = request.data.get("assigned_team", "")

        if not assigned_to_id:
            return Response(
                {"error": "assigned_to is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            assigned_to = User.objects.get(id=assigned_to_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        ticket.assigned_to = assigned_to
        ticket.assigned_team = assigned_team
        ticket.save(update_fields=["assigned_to", "assigned_team", "updated_at"])

        return Response(
            {"message": "Ticket assigned successfully", "ticket": TicketSerializer(ticket).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def resolve(self, request, pk=None):
        """
        Mark ticket as resolved.

        Staff only action. Creates resolution timestamp and checks SLA.
        """
        ticket = self.get_object()

        if ticket.status in ["resolved", "closed"]:
            return Response(
                {"error": "Ticket is already resolved or closed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.resolve(resolved_by=request.user)
        ticket.check_sla_breach()

        return Response(
            {"message": "Ticket resolved", "ticket": TicketSerializer(ticket).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsStaffUser])
    def close(self, request, pk=None):
        """
        Close ticket.

        Staff only action. Tickets should be resolved before closing.
        """
        ticket = self.get_object()

        if ticket.status == "closed":
            return Response(
                {"error": "Ticket is already closed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.close()

        return Response(
            {"message": "Ticket closed", "ticket": TicketSerializer(ticket).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def add_satisfaction_rating(self, request, pk=None):
        """
        Add customer satisfaction rating to ticket.

        Available to both staff and portal users.
        """
        ticket = self.get_object()
        rating = request.data.get("satisfaction_rating")
        comment = request.data.get("satisfaction_comment", "")

        if not rating:
            return Response(
                {"error": "satisfaction_rating is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
        except (ValueError, TypeError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.satisfaction_rating = rating
        ticket.satisfaction_comment = comment
        ticket.save(update_fields=["satisfaction_rating", "satisfaction_comment", "updated_at"])

        return Response(
            {"message": "Satisfaction rating added", "ticket": TicketSerializer(ticket).data},
            status=status.HTTP_200_OK,
        )


class TicketCommentViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Ticket Comments.

    Staff can add comments and internal notes.
    Portal users can add comments to their own tickets.
    """

    queryset = TicketComment.objects.all()
    serializer_class = TicketCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["ticket", "is_internal", "is_customer_reply"]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        """Filter by ticket access permissions."""
        queryset = self.queryset

        # Portal users can only see comments on their tickets
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            queryset = queryset.filter(
                ticket__client__in=self.request.portal_clients,
                is_internal=False,  # Portal users cannot see internal notes
            )

        return queryset.select_related("ticket", "created_by")

    def perform_create(self, serializer):
        """Create comment with appropriate flags."""
        # Determine if this is a customer reply based on user type
        is_customer_reply = (
            hasattr(self.request, "is_portal_request") and self.request.is_portal_request
        )

        serializer.save(
            created_by=self.request.user,
            is_customer_reply=is_customer_reply,
        )


class SurveyViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Customer Survey management.

    Surveys define feedback questions (NPS, CSAT, CES, custom).
    Only managers can create/edit surveys.
    """

    model = Survey
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated, IsStaffUser, IsManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["survey_type", "status"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(
            firm=self.request.firm,
            created_by=self.request.user,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate survey (make it available for use)."""
        survey = self.get_object()
        survey.status = "active"
        survey.save(update_fields=["status"])

        return Response(
            {"message": "Survey activated", "survey": SurveySerializer(survey).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Archive survey (no longer available for use)."""
        survey = self.get_object()
        survey.status = "archived"
        survey.save(update_fields=["status"])

        return Response(
            {"message": "Survey archived", "survey": SurveySerializer(survey).data},
            status=status.HTTP_200_OK,
        )


class SurveyResponseViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Survey Responses.

    Survey responses can be submitted by both staff and portal users.
    Tracks NPS scores and customer feedback.
    """

    queryset = SurveyResponse.objects.all()
    serializer_class = SurveyResponseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["survey", "client", "nps_category", "ticket", "project"]
    ordering_fields = ["submitted_at", "nps_score"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        """Filter by survey firm and portal permissions."""
        queryset = self.queryset

        # Filter by firm
        queryset = queryset.filter(survey__firm=self.request.firm)

        # Portal users can only see their own responses
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            queryset = queryset.filter(client__in=self.request.portal_clients)

        return queryset.select_related("survey", "client", "ticket", "project")

    def perform_create(self, serializer):
        """Create survey response (auto-calculates NPS category)."""
        serializer.save()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsStaffUser])
    def nps_summary(self, request):
        """
        Calculate NPS (Net Promoter Score) summary.

        NPS = % Promoters - % Detractors
        Staff only endpoint.
        """
        firm = request.firm
        queryset = SurveyResponse.objects.filter(
            survey__firm=firm,
            nps_score__isnull=False,
        )

        # Apply filters if provided
        survey_id = request.query_params.get("survey")
        if survey_id:
            queryset = queryset.filter(survey_id=survey_id)

        total = queryset.count()
        if total == 0:
            return Response(
                {
                    "total_responses": 0,
                    "promoters": 0,
                    "passives": 0,
                    "detractors": 0,
                    "nps_score": None,
                },
                status=status.HTTP_200_OK,
            )

        promoters = queryset.filter(nps_category="promoter").count()
        passives = queryset.filter(nps_category="passive").count()
        detractors = queryset.filter(nps_category="detractor").count()

        promoter_pct = (promoters / total) * 100
        detractor_pct = (detractors / total) * 100
        nps_score = promoter_pct - detractor_pct

        return Response(
            {
                "total_responses": total,
                "promoters": promoters,
                "promoter_percentage": round(promoter_pct, 2),
                "passives": passives,
                "passive_percentage": round((passives / total) * 100, 2),
                "detractors": detractors,
                "detractor_percentage": round(detractor_pct, 2),
                "nps_score": round(nps_score, 2),
            },
            status=status.HTTP_200_OK,
        )
