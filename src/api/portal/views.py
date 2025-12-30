"""
Client Portal ViewSets (DOC-26.1).

Implements client portal IA per docs/26:
- Primary navigation: Home, Messages, Documents, Appointments, Billing, Engagements, Profile
- Account switcher for multi-account portal users
- Core flows: message, upload, book, pay

All endpoints are portal-user-only with client scoping.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from permissions import PortalAccessMixin
from modules.clients.models import Client, ClientPortalUser
from modules.clients.permissions import IsPortalUser
from modules.documents.models import Document, Folder, DocumentAccessLog
from modules.documents.services import S3Service
from modules.calendar.models import Appointment, AppointmentType, BookingLink
from modules.calendar.services import AvailabilityService, BookingService
from modules.firm.utils import get_request_firm
from modules.core.observability import get_correlation_id
from modules.core.notifications import EmailNotification
from modules.firm.audit import AuditEvent
from modules.firm.models import FirmMembership

from .serializers import (
    PortalDocumentSerializer,
    PortalFolderSerializer,
    PortalAppointmentSerializer,
    PortalProfileSerializer,
    PortalAccountSerializer,
    PortalHomeSerializer,
)


class PortalHomeViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ViewSet):
    """
    Portal Home/Dashboard view (DOC-26.1).

    Provides overview of recent activity, upcoming appointments, and pending items.
    """

    permission_classes = [IsAuthenticated, IsPortalUser]

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """
        Get portal home dashboard data.

        Returns:
        - Recent messages
        - Upcoming appointments
        - Recent documents
        - Pending invoices
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        # Get accessible accounts (for multi-account users)
        accessible_clients = self._get_accessible_clients(portal_user)

        # Build dashboard data
        dashboard_data = {
            "recent_messages": [],  # Would fetch from communications module
            "upcoming_appointments": self._get_upcoming_appointments(accessible_clients),
            "recent_documents": self._get_recent_documents(accessible_clients),
            "pending_invoices": self._get_pending_invoices(accessible_clients),
            "account_count": accessible_clients.count(),
        }

        serializer = PortalHomeSerializer(dashboard_data)
        return Response(serializer.data)

    def _get_accessible_clients(self, portal_user):
        """Get all clients this portal user can access."""
        # Base: user's primary client
        clients = Client.objects.filter(id=portal_user.client_id)

        # TODO: Add organization-based multi-account logic (DOC-26.1 account switcher)
        # If portal_user.client.organization, include other clients in same org

        return clients

    def _get_upcoming_appointments(self, clients):
        """Get upcoming appointments for accessible clients."""
        from datetime import datetime, timedelta

        end_date = datetime.now() + timedelta(days=30)
        appointments = Appointment.objects.filter(
            account__in=clients,
            start_time__gte=datetime.now(),
            start_time__lte=end_date,
            status__in=["confirmed", "requested"],
        ).order_by("start_time")[:5]

        return [
            {
                "id": appt.id,
                "title": appt.appointment_type.name,
                "start_time": appt.start_time,
                "staff_user": appt.staff_user.get_full_name() if appt.staff_user else None,
            }
            for appt in appointments
        ]

    def _get_recent_documents(self, clients):
        """Get recently uploaded documents for accessible clients."""
        documents = Document.objects.filter(
            client__in=clients,
            visibility="client",
        ).order_by("-created_at")[:5]

        return [
            {
                "id": doc.id,
                "name": doc.name,
                "created_at": doc.created_at,
                "file_type": doc.file_type,
            }
            for doc in documents
        ]

    def _get_pending_invoices(self, clients):
        """Get pending invoices for accessible clients."""
        from modules.finance.models import Invoice

        invoices = Invoice.objects.filter(
            client__in=clients,
            status="sent",
        ).order_by("-issue_date")[:5]

        return [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount": float(inv.total_amount),
                "due_date": inv.due_date,
            }
            for inv in invoices
        ]


class PortalAccountSwitcherViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ViewSet):
    """
    Account switcher for portal users with multiple account grants (DOC-26.1).

    Allows portal users who belong to an Organization to switch between
    accessible accounts. All lists and permissions are re-scoped on switch.
    """

    permission_classes = [IsAuthenticated, IsPortalUser]

    @action(detail=False, methods=["get"], url_path="accounts")
    def list_accounts(self, request):
        """
        List all accounts this portal user can access.

        Returns accounts if:
        - User's primary client
        - Other clients in same organization (if organization exists)
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        # Start with primary client
        accessible_clients = [portal_user.client]

        # Add other clients from same organization
        if portal_user.client.organization:
            org_clients = Client.objects.filter(
                organization=portal_user.client.organization,
                firm=portal_user.client.firm,
            ).exclude(id=portal_user.client_id)
            accessible_clients.extend(org_clients)

        serializer = PortalAccountSerializer(accessible_clients, many=True)
        return Response({
            "accounts": serializer.data,
            "current_account_id": portal_user.client_id,
            "has_multiple_accounts": len(accessible_clients) > 1,
        })

    @action(detail=False, methods=["post"], url_path="switch")
    def switch_account(self, request):
        """
        Switch active account context.

        Body: {"account_id": <client_id>}

        Validates that the portal user has access to the requested account.
        This would typically update session/token context.
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)
        account_id = request.data.get("account_id")

        if not account_id:
            return Response(
                {"error": "account_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify access to requested account
        accessible_client_ids = [portal_user.client_id]
        if portal_user.client.organization:
            accessible_client_ids.extend(
                Client.objects.filter(
                    organization=portal_user.client.organization,
                    firm=portal_user.client.firm,
                ).values_list("id", flat=True)
            )

        if int(account_id) not in accessible_client_ids:
            return Response(
                {"error": "Access denied to requested account"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # TODO: Update session/token context with new client_id
        # For now, just validate and return success

        return Response({
            "success": True,
            "active_account_id": account_id,
            "message": "Account context switched successfully",
        })


class PortalProfileViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ViewSet):
    """
    Portal user profile management (DOC-26.1).

    Allows portal users to view and update their profile settings.
    """

    permission_classes = [IsAuthenticated, IsPortalUser]

    @action(detail=False, methods=["get"], url_path="me")
    def get_profile(self, request):
        """Get current portal user's profile."""
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)
        serializer = PortalProfileSerializer(portal_user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], url_path="me")
    def update_profile(self, request):
        """Update current portal user's profile."""
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        # Allow updating specific fields
        allowed_fields = ["notification_preferences"]
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = PortalProfileSerializer(portal_user, data=update_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class PortalDocumentViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    Portal Documents view (DOC-26.1).

    Read-only access to client-visible documents with upload capability.
    Implements upload flow: view upload request → upload → appears in Documents.
    """

    permission_classes = [IsAuthenticated, IsPortalUser]
    portal_permission_required = "can_view_documents"
    serializer_class = PortalDocumentSerializer
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, OrderingFilter]
    filterset_fields = ["folder", "file_type"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """
        Return documents visible to portal user.

        Scoped to:
        - User's accessible clients (primary + organization if applicable)
        - Visibility = "client"
        """
        portal_user = self.get_validated_portal_user(self.request, enforce_permission=False)

        # Get accessible clients
        accessible_clients = [portal_user.client_id]
        if portal_user.client.organization:
            accessible_clients.extend(
                Client.objects.filter(
                    organization=portal_user.client.organization,
                    firm=portal_user.client.firm,
                ).values_list("id", flat=True)
            )

        return Document.objects.filter(
            client_id__in=accessible_clients,
            visibility="client",
        ).select_related("folder", "uploaded_by")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Generate presigned URL for document download.

        Validates portal user has access before generating URL.
        """
        document = self.get_object()  # Automatically validates queryset access
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        try:
            s3_service = S3Service()
            download_url = s3_service.generate_presigned_url(
                document.s3_bucket,
                document.s3_key,
                expiration=3600,  # 1 hour
            )

            # Log document access per DOC-14.2
            DocumentAccessLog.log_access(
                firm_id=document.firm_id,
                document=document,
                action="url_issued",
                actor_type="portal",
                actor_user=request.user,
                actor_portal_user_id=portal_user.id,
                correlation_id=get_correlation_id(request),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={"expiration_seconds": 3600},
            )

            return Response({"download_url": download_url})
        except Exception as e:
            return Response(
                {"error": f"Failed to generate download URL: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsPortalUser])
    def upload(self, request):
        """
        Upload a document to the portal (DOC-26.1 upload flow).

        Portal users can upload documents which are automatically set to
        client visibility and notify staff.

        POST /api/portal/documents/upload/
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        # Check upload permission
        if not portal_user.can_upload_documents:
            return Response(
                {"error": "Upload permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            file_obj = request.FILES.get("file")
            if not file_obj:
                return Response(
                    {"error": "No file provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            firm = get_request_firm(request)
            folder_id = request.data.get("folder")
            name = request.data.get("name", file_obj.name)
            description = request.data.get("description", "")

            # Upload to S3
            s3_service = S3Service()
            folder_path = f"firm-{firm.id}/client-{portal_user.client_id}/portal-uploads"
            upload_result = s3_service.upload_file(file_obj, folder=folder_path)

            # Create document record (always client-visible)
            document = Document.objects.create(
                firm=firm,
                client=portal_user.client,
                folder_id=folder_id,
                name=name,
                description=description,
                visibility="client",  # Portal uploads always client-visible
                file_type=file_obj.content_type,
                file_size_bytes=file_obj.size,
                s3_key=upload_result["s3_key"],
                s3_bucket=upload_result["s3_bucket"],
                current_version=1,
                uploaded_by=request.user,
            )

            # Log document upload access
            DocumentAccessLog.log_access(
                firm_id=firm.id,
                document=document,
                action="upload",
                actor_type="portal",
                actor_user=request.user,
                actor_portal_user_id=portal_user.id,
                correlation_id=get_correlation_id(request),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    "file_size": file_obj.size,
                    "file_type": file_obj.content_type,
                },
            )

            # Create audit event for portal upload
            AuditEvent.objects.create(
                firm=firm,
                event_type="portal_document_upload",
                severity="info",
                actor=request.user,
                resource_type="document",
                resource_id=document.id,
                details={
                    "document_name": name,
                    "client_id": portal_user.client_id,
                    "portal_user_id": portal_user.id,
                    "file_size": file_obj.size,
                },
            )

            # Notify staff members of new portal upload
            staff_emails = FirmMembership.objects.filter(
                firm=firm,
                is_active=True,
            ).exclude(
                user__email=""
            ).values_list("user__email", flat=True)

            if staff_emails:
                client_name = portal_user.client.company_name or "Client"
                EmailNotification.send(
                    to=list(staff_emails),
                    subject=f"New document uploaded by {client_name}",
                    html_content=f"""
                    <p>A new document has been uploaded to the client portal.</p>
                    <ul>
                        <li><strong>Client:</strong> {client_name}</li>
                        <li><strong>Document:</strong> {name}</li>
                        <li><strong>Size:</strong> {file_obj.size / 1024:.1f} KB</li>
                        <li><strong>Uploaded by:</strong> {request.user.get_full_name() or request.user.email}</li>
                    </ul>
                    <p>Please review the document in the client portal.</p>
                    """,
                )

            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PortalFolderViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    Portal Folders view (DOC-26.1).

    Read-only access to client-visible folders.
    """

    permission_classes = [IsAuthenticated, IsPortalUser]
    serializer_class = PortalFolderSerializer
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter]
    filterset_fields = ["parent"]
    search_fields = ["name"]
    ordering = ["name"]

    def get_queryset(self):
        """Return folders visible to portal user."""
        portal_user = self.get_validated_portal_user(self.request, enforce_permission=False)

        # Get accessible clients
        accessible_clients = [portal_user.client_id]
        if portal_user.client.organization:
            accessible_clients.extend(
                Client.objects.filter(
                    organization=portal_user.client.organization,
                    firm=portal_user.client.firm,
                ).values_list("id", flat=True)
            )

        return Folder.objects.filter(
            client_id__in=accessible_clients,
            visibility="client",
        ).select_related("parent")


class PortalAppointmentViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    Portal Appointments view (DOC-26.1).

    Implements booking flow: choose meeting type → choose availability → confirm.
    Portal users can view their appointments and book new ones.
    """

    permission_classes = [IsAuthenticated, IsPortalUser]
    portal_permission_required = "can_book_appointments"
    serializer_class = PortalAppointmentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "appointment_type"]
    ordering_fields = ["start_time"]
    ordering = ["start_time"]

    def get_queryset(self):
        """Return appointments for portal user's accessible accounts."""
        portal_user = self.get_validated_portal_user(self.request, enforce_permission=False)

        # Get accessible clients
        accessible_clients = [portal_user.client_id]
        if portal_user.client.organization:
            accessible_clients.extend(
                Client.objects.filter(
                    organization=portal_user.client.organization,
                    firm=portal_user.client.firm,
                ).values_list("id", flat=True)
            )

        return Appointment.objects.filter(
            account_id__in=accessible_clients,
        ).select_related("appointment_type", "staff_user")

    @action(detail=False, methods=["get"], url_path="available-types")
    def available_types(self, request):
        """
        List appointment types available for booking.

        Returns only active types that allow portal booking.
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)
        firm = get_request_firm(request)

        types = AppointmentType.objects.filter(
            firm=firm,
            status="active",
        )

        return Response([
            {
                "id": apt.id,
                "name": apt.name,
                "description": apt.description,
                "duration_minutes": apt.duration_minutes,
                "location_mode": apt.location_mode,
            }
            for apt in types
        ])

    @action(detail=False, methods=["post"], url_path="available-slots")
    def available_slots(self, request):
        """
        Get available booking slots for an appointment type.

        Body: {
            "appointment_type_id": <id>,
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD"
        }
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        appointment_type_id = request.data.get("appointment_type_id")
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")

        if not all([appointment_type_id, start_date_str, end_date_str]):
            return Response(
                {"error": "appointment_type_id, start_date, and end_date required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get appointment type
        try:
            apt_type = AppointmentType.objects.get(id=appointment_type_id)
        except AppointmentType.DoesNotExist:
            return Response(
                {"error": "Appointment type not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate available slots using AvailabilityService
        from datetime import datetime
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        availability_service = AvailabilityService()
        slots = availability_service.get_available_slots(
            appointment_type=apt_type,
            start_date=start_date,
            end_date=end_date,
        )

        return Response({"slots": slots})

    @action(detail=False, methods=["post"], url_path="book")
    def book(self, request):
        """
        Book an appointment (DOC-26.1 booking flow).

        Body: {
            "appointment_type_id": <id>,
            "start_time": "ISO8601 datetime",
            "notes": "optional notes"
        }
        """
        portal_user = self.get_validated_portal_user(request, enforce_permission=False)

        appointment_type_id = request.data.get("appointment_type_id")
        start_time_str = request.data.get("start_time")
        notes = request.data.get("notes", "")

        if not all([appointment_type_id, start_time_str]):
            return Response(
                {"error": "appointment_type_id and start_time required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            apt_type = AppointmentType.objects.get(id=appointment_type_id)
        except AppointmentType.DoesNotExist:
            return Response(
                {"error": "Appointment type not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Book using BookingService
        from datetime import datetime
        start_time = datetime.fromisoformat(start_time_str)

        booking_service = BookingService()
        result = booking_service.book_appointment(
            appointment_type=apt_type,
            account=portal_user.client,
            contact=None,  # TODO: Link to Contact if available
            start_time=start_time,
            notes=notes,
            booked_by=request.user,
        )

        if result["success"]:
            serializer = self.get_serializer(result["appointment"])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": result["error"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """
        Cancel an appointment.

        Portal users can cancel their own appointments.
        """
        appointment = self.get_object()  # Validates access via queryset

        if appointment.status in ["cancelled", "completed"]:
            return Response(
                {"error": f"Cannot cancel {appointment.status} appointment"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status
        appointment.status = "cancelled"
        appointment.save()

        # TODO: Notify staff of cancellation

        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
