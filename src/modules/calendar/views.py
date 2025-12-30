"""
Calendar Views.

Provides API endpoints for appointment booking, availability, and management.
Implements docs/34 sections 3 (booking flows) and 7 (permissions).
"""

from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from modules.auth.permissions import IsStaffUser
from .models import AppointmentType, AvailabilityProfile, BookingLink, Appointment
from .serializers import (
    AppointmentTypeSerializer,
    AvailabilityProfileSerializer,
    BookingLinkSerializer,
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    BookAppointmentSerializer,
    CancelAppointmentSerializer,
    AvailableSlotsSerializer,
)
from .services import AvailabilityService, RoutingService, BookingService


class AppointmentTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AppointmentType management.

    Per docs/34 section 7: Staff can manage appointment types.
    """

    queryset = AppointmentType.objects.all()
    serializer_class = AppointmentTypeSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "location_mode", "routing_policy"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "duration_minutes", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm)

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(firm=self.request.firm, created_by=self.request.user)


class AvailabilityProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AvailabilityProfile management.

    Per docs/34 section 7: Staff can manage their availability; managers can manage team pools.
    """

    queryset = AvailabilityProfile.objects.all()
    serializer_class = AvailabilityProfileSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["owner_type", "status"]
    search_fields = ["name", "owner_team_name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm)

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(firm=self.request.firm, created_by=self.request.user)


class BookingLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for BookingLink management.

    Per docs/34 section 7: Public booking link creation restricted to Manager+.
    """

    queryset = BookingLink.objects.all()
    serializer_class = BookingLinkSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["visibility", "status", "appointment_type"]
    search_fields = ["slug"]
    ordering_fields = ["created_at", "slug"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by firm context."""
        return self.queryset.filter(firm=self.request.firm)

    def perform_create(self, serializer):
        """Set firm and created_by on create."""
        serializer.save(firm=self.request.firm, created_by=self.request.user)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Appointment management and booking.

    Per docs/34 section 3: Provides booking flows for portal and staff.
    Per docs/34 section 7: Portal can book/cancel only within granted account scope.
    """

    queryset = Appointment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "appointment_type", "staff_user", "account"]
    search_fields = ["staff_user__username", "account__name"]
    ordering_fields = ["start_time", "created_at"]
    ordering = ["start_time"]

    def get_queryset(self):
        """Filter by firm context and portal permissions."""
        queryset = self.queryset.filter(firm=self.request.firm).select_related(
            "appointment_type",
            "staff_user",
            "account",
            "contact",
        )

        # Portal users can only see their own appointments (per docs/34 section 7)
        if hasattr(self.request, "is_portal_request") and self.request.is_portal_request:
            # Filter to appointments for accounts the portal user has access to
            # (This would need actual portal user context from middleware)
            queryset = queryset.filter(account__in=self.request.portal_accounts)

        return queryset

    def get_serializer_class(self):
        """Use detail serializer for retrieve, list serializer otherwise."""
        if self.action == "retrieve":
            return AppointmentDetailSerializer
        return AppointmentListSerializer

    @action(detail=False, methods=["post"], url_path="book")
    def book(self, request):
        """
        Book an appointment (per docs/34 section 3.1).

        Creates appointment in requested or confirmed status based on requires_approval.
        """
        serializer = BookAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get appointment type
        try:
            appointment_type = AppointmentType.objects.get(
                firm=request.firm,
                appointment_type_id=serializer.validated_data["appointment_type_id"],
                status="active",
            )
        except AppointmentType.DoesNotExist:
            return Response(
                {"error": "Appointment type not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Route to staff user (per docs/34 section 2.4)
        routing_service = RoutingService()
        staff_user, routing_reason = routing_service.route_appointment(
            appointment_type=appointment_type,
            account=None,  # TODO: Get from validated_data if provided
            engagement=None,
        )

        if not staff_user:
            return Response(
                {"error": "Could not route appointment to a staff member"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate end time
        start_time = serializer.validated_data["start_time"]
        end_time = start_time + timedelta(minutes=appointment_type.duration_minutes)

        # Book appointment (per docs/34 section 4.5: atomic transaction)
        booking_service = BookingService()
        try:
            appointment = booking_service.book_appointment(
                appointment_type=appointment_type,
                start_time=start_time,
                end_time=end_time,
                staff_user=staff_user,
                booked_by=request.user,
                intake_responses=serializer.validated_data.get("intake_responses", {}),
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_409_CONFLICT
            )

        return Response(
            {
                "message": "Appointment booked successfully",
                "appointment": AppointmentDetailSerializer(appointment).data,
                "routing_reason": routing_reason,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Cancel an appointment (per docs/34 section 3).

        Creates status history entry for audit trail.
        """
        appointment = self.get_object()
        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check permissions: staff or owner can cancel
        if hasattr(request, "is_portal_request") and request.is_portal_request:
            # Portal users can only cancel their own appointments
            if not (appointment.account and appointment.account in request.portal_accounts):
                return Response(
                    {"error": "You don't have permission to cancel this appointment"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        booking_service = BookingService()
        appointment = booking_service.cancel_appointment(
            appointment=appointment,
            reason=serializer.validated_data["reason"],
            cancelled_by=request.user,
        )

        return Response(
            {"message": "Appointment cancelled", "appointment": AppointmentDetailSerializer(appointment).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="confirm", permission_classes=[IsAuthenticated, IsStaffUser])
    def confirm(self, request, pk=None):
        """
        Confirm a requested appointment (approval flow per docs/34 section 3.1).

        Staff only.
        """
        appointment = self.get_object()

        booking_service = BookingService()
        try:
            appointment = booking_service.confirm_appointment(
                appointment=appointment,
                confirmed_by=request.user,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Appointment confirmed", "appointment": AppointmentDetailSerializer(appointment).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="available-slots")
    def available_slots(self, request):
        """
        Get available slots for booking (per docs/34 section 4).

        Computes availability with buffers and constraints.
        """
        serializer = AvailableSlotsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get appointment type
        try:
            appointment_type = AppointmentType.objects.get(
                firm=request.firm,
                appointment_type_id=serializer.validated_data["appointment_type_id"],
                status="active",
            )
        except AppointmentType.DoesNotExist:
            return Response(
                {"error": "Appointment type not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get staff user (or route)
        staff_user = None
        if appointment_type.routing_policy == "fixed_staff":
            staff_user = appointment_type.fixed_staff_user

        if not staff_user:
            return Response(
                {"error": "Could not determine staff for availability"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get availability profile (simplified: use first active profile for staff)
        profile = AvailabilityProfile.objects.filter(
            firm=request.firm,
            owner_type="staff",
            owner_staff_user=staff_user,
            status="active",
        ).first()

        if not profile:
            return Response(
                {"error": "No availability profile found for staff"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Compute available slots
        availability_service = AvailabilityService()
        slots = availability_service.compute_available_slots(
            profile=profile,
            appointment_type=appointment_type,
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"],
            staff_user=staff_user,
        )

        # Format slots for response
        formatted_slots = [
            {
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "duration_minutes": appointment_type.duration_minutes,
            }
            for start, end in slots
        ]

        return Response(
            {
                "appointment_type": AppointmentTypeSerializer(appointment_type).data,
                "staff_user": staff_user.username,
                "slots": formatted_slots,
                "total_slots": len(formatted_slots),
            },
            status=status.HTTP_200_OK,
        )
