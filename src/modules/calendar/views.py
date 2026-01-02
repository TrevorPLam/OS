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

from modules.auth.role_permissions import IsStaffUser
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

    @action(detail=True, methods=["get"], url_path="round-robin-stats")
    def round_robin_stats(self, request, pk=None):
        """
        Get round robin distribution statistics for this appointment type (TEAM-2).

        Shows appointment counts per staff member and whether rebalancing is needed.
        """
        appointment_type = self.get_object()

        if appointment_type.routing_policy != "round_robin_pool":
            return Response(
                {"error": "This endpoint only works with round robin appointment types"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pool = list(appointment_type.round_robin_pool.all())
        
        if not pool:
            return Response(
                {"pool_members": [], "needs_rebalancing": False, "message": "Round robin pool is empty"},
                status=status.HTTP_200_OK,
            )

        # Get counts for each pool member
        stats = []
        total_count = 0
        for staff in pool:
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                status__in=["requested", "confirmed"],
            ).count()
            
            # Get recent count (last 30 days)
            from django.utils import timezone as django_tz
            recent_cutoff = django_tz.now() - timedelta(days=30)
            recent_count = Appointment.objects.filter(
                appointment_type=appointment_type,
                staff_user=staff,
                start_time__gte=recent_cutoff,
                status__in=["requested", "confirmed", "completed"],
            ).count()

            weight = appointment_type.round_robin_weights.get(str(staff.id), 1.0)
            
            stats.append({
                "staff_id": staff.id,
                "staff_username": staff.username,
                "total_appointments": count,
                "recent_appointments_30d": recent_count,
                "weight": weight,
                "weighted_ratio": count / weight if weight > 0 else 0,
            })
            total_count += count

        # Calculate average
        avg_count = total_count / len(pool) if pool else 0

        # Check if needs rebalancing
        from modules.calendar.services import RoundRobinService
        rr_service = RoundRobinService()
        needs_rebalancing = rr_service._needs_rebalancing(appointment_type)

        # Calculate deviation for each member
        for stat in stats:
            deviation = abs(stat["total_appointments"] - avg_count) / avg_count if avg_count > 0 else 0
            stat["deviation_from_average"] = deviation

        # Sort by total appointments (descending)
        stats.sort(key=lambda x: x["total_appointments"], reverse=True)

        return Response(
            {
                "appointment_type_id": appointment_type.appointment_type_id,
                "appointment_type_name": appointment_type.name,
                "strategy": appointment_type.round_robin_strategy,
                "pool_size": len(pool),
                "total_appointments": total_count,
                "average_appointments": avg_count,
                "needs_rebalancing": needs_rebalancing,
                "rebalancing_threshold": float(appointment_type.round_robin_rebalancing_threshold),
                "pool_members": stats,
            },
            status=status.HTTP_200_OK,
        )


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

        # Calculate end time first (needed for round robin routing)
        start_time = serializer.validated_data["start_time"]
        end_time = start_time + timedelta(minutes=appointment_type.duration_minutes)

        # Route to staff user (per docs/34 section 2.4)
        # TEAM-2: Pass start_time and end_time for advanced round robin
        routing_service = RoutingService()
        account = serializer.validated_data.get("account")
        engagement = serializer.validated_data.get("engagement")
        staff_user, routing_reason = routing_service.route_appointment(
            appointment_type=appointment_type,
            account=account,
            engagement=engagement,
            start_time=start_time,
            end_time=end_time,
        )

        if not staff_user:
            return Response(
                {"error": "Could not route appointment to a staff member"},
                status=status.HTTP_400_BAD_REQUEST,
            )


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

    @action(detail=False, methods=["post"], url_path="collective-available-slots")
    def collective_available_slots(self, request):
        """
        Get available slots for collective event booking (TEAM-1).

        Computes Venn diagram availability where all required hosts must be free.
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

        # Verify it's a collective event
        if appointment_type.event_category != "collective":
            return Response(
                {"error": "This endpoint only works with collective event types"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Compute collective available slots
        availability_service = AvailabilityService()
        slots_with_hosts = availability_service.compute_collective_available_slots(
            appointment_type=appointment_type,
            start_date=serializer.validated_data["start_date"],
            end_date=serializer.validated_data["end_date"],
        )

        # Format slots for response
        formatted_slots = [
            {
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "duration_minutes": appointment_type.duration_minutes,
                "available_hosts": [
                    {
                        "id": host.id,
                        "username": host.username,
                        "is_required": host in appointment_type.required_hosts.all(),
                    }
                    for host in hosts
                ],
                "required_hosts_count": appointment_type.required_hosts.count(),
                "total_hosts_count": len(hosts),
            }
            for start, end, hosts in slots_with_hosts
        ]

        return Response(
            {
                "appointment_type": AppointmentTypeSerializer(appointment_type).data,
                "required_hosts": [
                    {"id": h.id, "username": h.username}
                    for h in appointment_type.required_hosts.all()
                ],
                "optional_hosts": [
                    {"id": h.id, "username": h.username}
                    for h in appointment_type.optional_hosts.all()
                ],
                "slots": formatted_slots,
                "total_slots": len(formatted_slots),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="book-collective")
    def book_collective(self, request):
        """
        Book a collective event appointment (TEAM-1).

        Creates appointment with multiple hosts (required + available optional).
        """
        # Validate basic booking data
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

        # Verify it's a collective event
        if appointment_type.event_category != "collective":
            return Response(
                {"error": "This endpoint only works with collective event types"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate end time
        start_time = serializer.validated_data["start_time"]
        end_time = start_time + timedelta(minutes=appointment_type.duration_minutes)

        # Get the required and available optional hosts for this time slot
        availability_service = AvailabilityService()
        slots_with_hosts = availability_service.compute_collective_available_slots(
            appointment_type=appointment_type,
            start_date=start_time.date(),
            end_date=start_time.date(),
        )

        # Find the matching slot
        matching_hosts = None
        for slot_start, slot_end, hosts in slots_with_hosts:
            if slot_start == start_time and slot_end == end_time:
                matching_hosts = hosts
                break

        if not matching_hosts:
            return Response(
                {"error": "The selected time slot is no longer available for all required hosts"},
                status=status.HTTP_409_CONFLICT,
            )

        # Book collective appointment
        booking_service = BookingService()
        try:
            appointment = booking_service.book_collective_appointment(
                appointment_type=appointment_type,
                start_time=start_time,
                end_time=end_time,
                collective_hosts=matching_hosts,
                booked_by=request.user,
                intake_responses=serializer.validated_data.get("intake_responses", {}),
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_409_CONFLICT
            )

        return Response(
            {
                "message": "Collective event appointment booked successfully",
                "appointment": AppointmentDetailSerializer(appointment).data,
                "hosts": [
                    {"id": h.id, "username": h.username}
                    for h in appointment.collective_hosts.all()
                ],
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="substitute-host", permission_classes=[IsAuthenticated, IsStaffUser])
    def substitute_host(self, request, pk=None):
        """
        Substitute a host in a collective event appointment (TEAM-1).

        Staff only. Allows replacing one host with another if new host is available.
        """
        appointment = self.get_object()

        # Verify it's a collective event
        if appointment.appointment_type.event_category != "collective":
            return Response(
                {"error": "Host substitution only applies to collective events"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get old and new host IDs from request
        old_host_id = request.data.get("old_host_id")
        new_host_id = request.data.get("new_host_id")
        reason = request.data.get("reason", "")

        if not old_host_id or not new_host_id:
            return Response(
                {"error": "Both old_host_id and new_host_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get user instances
        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            old_host = User.objects.get(id=old_host_id, firm=request.firm)
            new_host = User.objects.get(id=new_host_id, firm=request.firm)
        except User.DoesNotExist:
            return Response(
                {"error": "One or both hosts not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Perform substitution
        booking_service = BookingService()
        try:
            appointment = booking_service.substitute_collective_host(
                appointment=appointment,
                old_host=old_host,
                new_host=new_host,
                substituted_by=request.user,
                reason=reason,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_409_CONFLICT
            )

        return Response(
            {
                "message": "Host substituted successfully",
                "appointment": AppointmentDetailSerializer(appointment).data,
                "old_host": {"id": old_host.id, "username": old_host.username},
                "new_host": {"id": new_host.id, "username": new_host.username},
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="register-attendee")
    def register_attendee(self, request, pk=None):
        """
        Register an attendee for a group event (TEAM-3).

        Handles capacity checking and waitlist management automatically.
        """
        appointment = self.get_object()

        # Verify it's a group event
        if appointment.appointment_type.event_category != "group":
            return Response(
                {"error": "This endpoint only works with group event types"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get attendee information
        contact_id = request.data.get("contact_id")
        attendee_name = request.data.get("attendee_name", "")
        attendee_email = request.data.get("attendee_email", "")

        contact = None
        if contact_id:
            from modules.clients.models import Contact
            try:
                contact = Contact.objects.get(id=contact_id, firm=request.firm)
            except Contact.DoesNotExist:
                return Response(
                    {"error": "Contact not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Register attendee
        from modules.calendar.services import GroupEventService
        group_service = GroupEventService()
        
        try:
            result, is_waitlisted = group_service.register_attendee(
                appointment=appointment,
                contact=contact,
                attendee_name=attendee_name,
                attendee_email=attendee_email,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get capacity info
        capacity_info = group_service.get_capacity_info(appointment)

        if is_waitlisted:
            return Response(
                {
                    "message": "Added to waitlist",
                    "waitlist_position": result.waitlist_id,
                    "capacity_info": capacity_info,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "message": "Registered successfully",
                    "attendee_id": result.attendee_id,
                    "capacity_info": capacity_info,
                },
                status=status.HTTP_201_CREATED,
            )

    @action(detail=True, methods=["post"], url_path="cancel-attendee")
    def cancel_attendee(self, request, pk=None):
        """
        Cancel an attendee from a group event (TEAM-3).

        Automatically promotes from waitlist if available.
        """
        appointment = self.get_object()

        # Verify it's a group event
        if appointment.appointment_type.event_category != "group":
            return Response(
                {"error": "This endpoint only works with group event types"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attendee_id = request.data.get("attendee_id")
        if not attendee_id:
            return Response(
                {"error": "attendee_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from modules.calendar.services import GroupEventService
        group_service = GroupEventService()
        
        try:
            cancelled_attendee, promoted_entry = group_service.cancel_attendee(
                appointment=appointment,
                attendee_id=attendee_id,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_404_NOT_FOUND
            )

        response_data = {
            "message": "Attendee cancelled",
            "cancelled_attendee_id": cancelled_attendee.attendee_id,
        }

        if promoted_entry:
            response_data["promoted_from_waitlist"] = {
                "waitlist_id": promoted_entry.waitlist_id,
                "name": promoted_entry.contact.name if promoted_entry.contact else promoted_entry.waitlist_name,
            }

        # Get updated capacity info
        capacity_info = group_service.get_capacity_info(appointment)
        response_data["capacity_info"] = capacity_info

        return Response(response_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="group-attendees")
    def group_attendees(self, request, pk=None):
        """
        Get the list of attendees for a group event (TEAM-3).
        """
        appointment = self.get_object()

        if appointment.appointment_type.event_category != "group":
            return Response(
                {"error": "This endpoint only works with group event types"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from modules.calendar.services import GroupEventService
        group_service = GroupEventService()
        
        attendees = group_service.get_attendee_list(appointment)
        waitlist = group_service.get_waitlist(appointment)
        capacity_info = group_service.get_capacity_info(appointment)

        attendees_data = [
            {
                "attendee_id": a.attendee_id,
                "name": a.contact.name if a.contact else a.attendee_name,
                "email": a.contact.email if a.contact else a.attendee_email,
                "status": a.status,
                "registered_at": a.registered_at.isoformat(),
            }
            for a in attendees
        ]

        waitlist_data = [
            {
                "waitlist_id": w.waitlist_id,
                "name": w.contact.name if w.contact else w.waitlist_name,
                "email": w.contact.email if w.contact else w.waitlist_email,
                "priority": w.priority,
                "joined_at": w.joined_at.isoformat(),
            }
            for w in waitlist
        ]

        return Response(
            {
                "capacity_info": capacity_info,
                "attendees": attendees_data,
                "waitlist": waitlist_data,
            },
            status=status.HTTP_200_OK,
        )

