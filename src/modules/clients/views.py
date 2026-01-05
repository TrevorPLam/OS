"""
API Views for Clients module.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
Client portal views filter by portal user's client (which is firm-scoped).
TIER 2: Portal ViewSets use IsPortalUserOrFirmUser for portal containment.
TIER 2.5: Firm admin ViewSets use DenyPortalAccess to block portal users.
TIER 2.6: Organizations enable cross-client collaboration within firms.
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from permissions import PortalAccessMixin, PortalFirmAccessPermission
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.portal_branding import PortalBranding
from modules.clients.models import (
    Client,
    ClientChatThread,
    ClientComment,
    ClientEngagement,
    ClientMessage,
    ClientNote,
    ClientPortalUser,
    Organization,
    ConsentRecord,
    Contact,
    EmailOptInRequest,
    EmailUnsubscribeToken,
)
from modules.clients.permissions import DenyPortalAccess, IsPortalUserOrFirmUser
from modules.clients.serializers import (
    ClientChatThreadSerializer,
    ClientCommentSerializer,
    ClientContractSerializer,
    ClientEngagementDetailSerializer,
    ClientEngagementSerializer,
    ClientMessageSerializer,
    ClientNoteSerializer,
    ClientPortalUserSerializer,
    ClientProjectSerializer,
    ClientProposalSerializer,
    ClientSerializer,
    OrganizationSerializer,
    ConsentRecordSerializer,
    ConsentRecordCreateSerializer,
    ConsentProofExportSerializer,
)
from modules.core.notifications import EmailComplianceDetails, EmailNotification
from modules.firm.utils import FirmScopedMixin, get_request_firm


class OrganizationViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Organization management.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2.6: Organizations enable cross-client collaboration within a firm.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Firm users only
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["enable_cross_client_visibility"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("firm", "created_by")

    def perform_create(self, serializer):
        """Set firm and created_by when creating organization."""
        firm = get_request_firm(self.request)
        serializer.save(firm=firm, created_by=self.request.user)


class ClientViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client management (Post-sale).

    Provides CRUD operations for clients that have been converted from prospects.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    model = Client
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "account_manager", "portal_enabled"]
    search_fields = ["company_name", "primary_contact_name", "primary_contact_email"]
    ordering_fields = ["company_name", "client_since", "total_lifetime_value"]
    ordering = ["-client_since"]

    def get_queryset(self):
        """Override to add select_related for performance (TIER 5.2)."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("organization", "account_manager")

    @action(detail=True, methods=["get"])
    def overview(self, request, pk=None):
        """
        Get comprehensive client overview.

        Returns client details plus related projects, invoices, and engagements.
        """
        client = self.get_object()
        serializer = self.get_serializer(client)

        # Get related data counts
        overview_data = {
            **serializer.data,
            "projects_count": client.projects.count(),
            "active_projects": client.projects.filter(status="in_progress").count(),
            "invoices_count": client.invoices.count(),
            "outstanding_invoices": client.invoices.filter(status__in=["sent", "partial", "overdue"]).count(),
            "engagements_count": client.engagements.count(),
            "portal_users_count": client.portal_users.count(),
        }

        return Response(overview_data)

    @action(detail=True, methods=["post"])
    def enable_portal(self, request, pk=None):
        """Enable client portal access for this client."""
        client = self.get_object()
        client.portal_enabled = True
        client.save()
        return Response({"status": "portal enabled", "client": ClientSerializer(client).data})

    @action(detail=True, methods=["post"])
    def disable_portal(self, request, pk=None):
        """Disable client portal access for this client."""
        client = self.get_object()
        client.portal_enabled = False
        client.save()
        return Response({"status": "portal disabled", "client": ClientSerializer(client).data})

    @action(detail=True, methods=["post"])
    def enable_autopay(self, request, pk=None):
        """Enable autopay for a client and store the payment method id."""
        client = self.get_object()
        payment_method_id = request.data.get("payment_method_id")

        if not payment_method_id:
            return Response({"detail": "payment_method_id is required"}, status=400)

        client.autopay_enabled = True
        client.autopay_payment_method_id = payment_method_id
        client.autopay_activated_at = timezone.now()
        client.autopay_activated_by = request.user
        client.save(
            update_fields=[
                "autopay_enabled",
                "autopay_payment_method_id",
                "autopay_activated_at",
                "autopay_activated_by",
            ]
        )

        return Response({"status": "autopay enabled", "client": ClientSerializer(client).data})

    @action(detail=True, methods=["post"])
    def disable_autopay(self, request, pk=None):
        """Disable autopay and clear payment method reference."""
        client = self.get_object()
        client.autopay_enabled = False
        client.autopay_payment_method_id = ""
        client.autopay_activated_at = None
        client.autopay_activated_by = None
        client.save(
            update_fields=[
                "autopay_enabled",
                "autopay_payment_method_id",
                "autopay_activated_at",
                "autopay_activated_by",
            ]
        )

        client.invoices.update(autopay_opt_in=False, autopay_status="cancelled")

        return Response({"status": "autopay disabled", "client": ClientSerializer(client).data})


class ClientPortalUserViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client Portal User management.

    Manages client-side users with portal access.

    TIER 0: Firm-scoped through client__firm relationship.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    serializer_class = ClientPortalUserSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter]
    filterset_fields = ["client", "role"]
    search_fields = ["user__username", "user__email", "client__company_name"]

    def get_queryset(self):
        """Filter portal users to firm via client relationship."""
        firm = get_request_firm(self.request)
        return ClientPortalUser.objects.filter(client__firm=firm)

    def perform_create(self, serializer):
        """Set invited_by to current user."""
        serializer.save(invited_by=self.request.user)


class ClientNoteViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client Notes (internal only).

    Notes are NOT visible to clients - for internal team use only.

    TIER 0: Firm-scoped through client__firm relationship.
    TIER 2.5: Portal users explicitly denied (internal firm use only).
    """

    serializer_class = ClientNoteSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter]
    filterset_fields = ["client", "author", "is_pinned"]
    search_fields = ["note", "client__company_name"]

    def get_queryset(self):
        """
        Filter notes to firm via client relationship.

        TIER 0: Firm context automatically applied.
        Optionally filter by client_id query param.
        """
        firm = get_request_firm(self.request)
        queryset = ClientNote.objects.filter(client__firm=firm)

        client_id = self.request.query_params.get("client_id")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset


class ClientEngagementViewSet(QueryTimeoutMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client Engagements.

    Tracks all contracts/engagements with version history.

    TIER 0: Firm-scoped through client__firm relationship.
    TIER 2.5: Portal users explicitly denied (firm admin only).
    """

    serializer_class = ClientEngagementSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["client", "status"]
    ordering_fields = ["start_date", "version", "contracted_value"]
    ordering = ["-start_date"]

    def get_queryset(self):
        """Filter engagements to firm via client relationship (TIER 5.2 optimized)."""
        firm = get_request_firm(self.request)
        return ClientEngagement.objects.filter(client__firm=firm).select_related(
            "client", "contract", "parent_engagement"
        )

    @action(detail=False, methods=["get"])
    def by_client(self, request):
        """
        Get all engagements for a specific client.

        TIER 0: Queryset already firm-scoped via get_queryset().
        """
        client_id = request.query_params.get("client_id")
        if not client_id:
            return Response({"error": "client_id query parameter required"}, status=400)

        with self.with_query_timeout():
            engagements = self.get_queryset().filter(client_id=client_id)
            serializer = self.get_serializer(engagements, many=True)
            return Response(serializer.data)


class ClientProjectViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Projects (read-only).

    Shows projects for the authenticated client portal user.
    Clients can view their projects and tasks, but cannot modify them.

    TIER 0: Firm-scoped for firm users, client-scoped for portal users.
    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientProjectSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    portal_permission_required = "can_view_projects"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["name", "start_date", "end_date"]
    ordering = ["-start_date"]

    def get_queryset(self):
        """
        Filter projects by authenticated client portal user's client.

        TIER 0:
        - Client portal users: see only their client's projects
        - Firm users: see all projects for their firm
        """
        from modules.projects.models import Project

        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            return Project.objects.filter(client=portal_user.client).prefetch_related("tasks_set")

        return Project.objects.filter(client__firm=firm)

    @action(detail=True, methods=["get"])
    def tasks(self, request, pk=None):
        """
        Get all tasks for a specific project.

        Returns tasks with client comments.
        """
        project = self.get_object()
        from modules.clients.serializers import ClientTaskSerializer
        from modules.projects.models import Task

        with self.with_query_timeout():
            tasks = Task.objects.filter(project=project).order_by("position", "-created_at")
            serializer = ClientTaskSerializer(tasks, many=True)
            return Response(serializer.data)


class ClientCommentViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client Comments on Tasks.

    Allows client portal users to comment on tasks in their projects.
    Comments are visible to both firm team and client.

    TIER 0: Firm-scoped for firm users, client-scoped for portal users.
    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientCommentSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["task", "client", "is_read_by_firm"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Filter comments based on user type.

        TIER 0:
        - Client portal users: only see comments for their client
        - Firm users: see comments for their firm (via client)
        """
        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request, enforce_permission=False)

        if portal_user:
            queryset = ClientComment.objects.filter(client=portal_user.client)
        else:
            queryset = ClientComment.objects.filter(client__firm=firm)

        # Filter by task_id if provided in query params
        task_id = self.request.query_params.get("task_id")
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    def perform_create(self, serializer):
        """
        Create comment with automatic client detection.

        The serializer handles setting author and client from request context.
        """
        serializer.save()

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """
        Mark a client comment as read by firm team.

        Only accessible to firm users (not client portal users).
        """
        comment = self.get_object()

        if self.get_validated_portal_user(request, enforce_permission=False):
            return Response({"error": "Only firm team members can mark comments as read"}, status=403)

        from django.utils import timezone

        comment.is_read_by_firm = True
        comment.read_by = request.user
        comment.read_at = timezone.now()
        comment.save()

        return Response({"status": "marked as read", "comment": ClientCommentSerializer(comment).data})

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """
        Get all unread client comments.

        Only accessible to firm users.
        """
        # Check if user is a firm user
        try:
            ClientPortalUser.objects.get(user=request.user)
            return Response({"error": "Only firm team members can access this endpoint"}, status=403)
        except ClientPortalUser.DoesNotExist:
            # Firm user - get unread comments
            with self.with_query_timeout():
                unread_comments = self.get_queryset().filter(is_read_by_firm=False)
                serializer = self.get_serializer(unread_comments, many=True)
                return Response(serializer.data)


class ClientInvoiceViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Invoices (read-only).

    Shows invoices for the authenticated client portal user.
    Clients can view their invoices but cannot modify them.
    Includes payment link generation for Stripe.

    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = None  # Will be imported below
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    portal_permission_required = "can_view_billing"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["invoice_number", "issue_date", "due_date", "total_amount"]
    ordering = ["-issue_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from modules.clients.serializers import ClientInvoiceSerializer

        self.serializer_class = ClientInvoiceSerializer

    def get_queryset(self):
        """
        Filter invoices by authenticated client portal user's client.

        TIER 0:
        - Client portal users: see only their client's invoices
        - Firm users: see all invoices for their firm
        """
        from modules.finance.models import Invoice

        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            return (
                Invoice.objects.filter(client=portal_user.client)
                .select_related("client", "project")
                .order_by("-issue_date")
            )

        return Invoice.objects.filter(firm=firm).select_related("client", "project")

    @action(detail=True, methods=["post"])
    def generate_payment_link(self, request, pk=None):
        """
        Generate Stripe payment link for an invoice.

        Returns a Stripe Checkout session URL that the client can use to pay.
        """
        invoice = self.get_object()

        # Verify invoice can be paid
        if invoice.status not in ["sent", "partial", "overdue"]:
            return Response(
                {"error": "Invoice cannot be paid online. Status must be sent, partial, or overdue."}, status=400
            )

        if invoice.balance_due <= 0:
            return Response({"error": "Invoice has no outstanding balance."}, status=400)

        # Create Stripe Checkout session
        from modules.finance.services import StripeService
        from django.conf import settings
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Build success and cancel URLs
            # These should redirect back to the client portal
            base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else request.build_absolute_uri('/')[:-1]
            success_url = f"{base_url}/portal/invoices/{invoice.id}?payment=success"
            cancel_url = f"{base_url}/portal/invoices/{invoice.id}?payment=cancelled"

            # Get client email if available
            customer_email = invoice.client.email if hasattr(invoice.client, 'email') else None

            # Create Stripe Checkout session
            session = StripeService.create_checkout_session(
                amount=invoice.balance_due,
                currency=invoice.currency.lower(),
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"invoice_id": str(invoice.id)},
                customer_email=customer_email,
                invoice_number=invoice.invoice_number,
            )

            return Response(
                {
                    "status": "payment_link_generated",
                    "payment_url": session.url,
                    "session_id": session.id,
                    "invoice_number": invoice.invoice_number,
                    "amount_due": str(invoice.balance_due),
                    "currency": invoice.currency,
                }
            )

        except Exception as e:
            logger.error(f"Failed to create payment link: {str(e)}")
            return Response(
                {
                    "error": "Failed to generate payment link",
                    "details": str(e),
                },
                status=500,
            )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get invoice summary for the client.

        Returns counts and totals by status.
        """
        portal_user = self.get_validated_portal_user(request)
        if portal_user is None:
            return Response({"error": "Only client portal users can access this endpoint"}, status=403)
        client = portal_user.client

        from django.db.models import Count, Sum

        from modules.finance.models import Invoice

        with self.with_query_timeout():
            # TIER 0: verified - client belongs to portal_user who belongs to request firm
            invoices = Invoice.objects.filter(client=client)

            # Get summary statistics
            summary = {
                "total_invoices": invoices.count(),
                "total_billed": invoices.aggregate(total=Sum("total_amount"))["total"] or 0,
                "total_paid": invoices.aggregate(total=Sum("amount_paid"))["total"] or 0,
                "total_outstanding": sum(inv.balance_due for inv in invoices),
                "by_status": {},
            }

            # Count by status
            status_counts = invoices.values("status").annotate(count=Count("id"), total=Sum("total_amount"))

            for item in status_counts:
                summary["by_status"][item["status"]] = {
                    "count": item["count"],
                    "total": str(item["total"]) if item["total"] else "0.00",  # Maintain precision as string
                }

            # Overdue invoices
            overdue_invoices = invoices.filter(status__in=["sent", "partial"])
            from django.utils import timezone

            today = timezone.now().date()
            overdue_count = sum(1 for inv in overdue_invoices if inv.due_date < today)

            summary["overdue_count"] = overdue_count

            return Response(summary)


class ClientChatThreadViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client Chat Threads.

    Manages daily chat threads between clients and firm team.
    Threads auto-rotate daily for organization.

    TIER 0: Firm-scoped for firm users, client-scoped for portal users.
    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientChatThreadSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    portal_permission_required = "can_message_team"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["client", "is_active", "date"]
    ordering_fields = ["date", "last_message_at"]
    ordering = ["-date"]

    def get_queryset(self):
        """
        Filter threads based on user type.

        TIER 0:
        - Client portal users: only see their client's threads
        - Firm users: see threads for their firm (via client)
        """
        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            return ClientChatThread.objects.filter(client=portal_user.client).prefetch_related("messages")

        return ClientChatThread.objects.filter(client__firm=firm).prefetch_related("messages")

    @action(detail=False, methods=["get"])
    def active(self, request):
        """
        Get or create today's active thread for the client.

        Returns the active thread with recent messages.
        """
        portal_user = self.get_validated_portal_user(request)
        if portal_user is None:
            return Response({"error": "Only client portal users can access this endpoint"}, status=403)
        client = portal_user.client

        # Get or create today's thread
        from django.utils import timezone

        today = timezone.now().date()

        thread, created = ClientChatThread.objects.get_or_create(
            client=client, date=today, defaults={"is_active": True}
        )

        serializer = self.get_serializer(thread)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """
        Archive a chat thread.

        Only accessible to firm users.
        """
        if self.get_validated_portal_user(request, enforce_permission=False):
            return Response({"error": "Only firm team members can archive threads"}, status=403)

        thread = self.get_object()
        from django.utils import timezone

        thread.is_active = False
        thread.archived_at = timezone.now()
        thread.save()

        return Response({"status": "thread archived", "thread": ClientChatThreadSerializer(thread).data})


class ClientMessageViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ModelViewSet):
    """
    ViewSet for Client Messages.

    Handles real-time messaging between clients and firm team.
    Messages are organized by daily threads.

    TIER 0: Firm-scoped for firm users, client-scoped for portal users.
    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientMessageSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    portal_permission_required = "can_message_team"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["thread", "is_from_client", "message_type", "is_read"]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        """
        Filter messages based on user type.

        TIER 0:
        - Client portal users: only see their client's messages
        - Firm users: see messages for their firm (via thread.client)
        """
        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            queryset = ClientMessage.objects.filter(thread__client=portal_user.client).select_related(
                "thread", "sender"
            )
        else:
            queryset = ClientMessage.objects.filter(thread__client__firm=firm).select_related("thread", "sender")

        return queryset

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        """
        Mark a message as read.

        Accessible to both clients and firm users.
        """
        message = self.get_object()

        from django.utils import timezone

        message.is_read = True
        message.read_by = request.user
        message.read_at = timezone.now()
        message.save()

        return Response({"status": "marked as read", "message": ClientMessageSerializer(message).data})

    @action(detail=False, methods=["get"])
    def unread(self, request):
        """
        Get unread messages for the current user.

        For clients: get unread messages from firm
        For firm: get unread messages from all clients
        """
        with self.with_query_timeout():
            queryset = self.get_queryset()

            if self.get_validated_portal_user(request, enforce_permission=False):
                unread = queryset.filter(is_read=False, is_from_client=False)
            else:
                unread = queryset.filter(is_read=False, is_from_client=True)

            serializer = self.get_serializer(unread, many=True)
            return Response(serializer.data)


class ClientProposalViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Proposals (read-only).

    Shows proposals sent to the client.
    Clients can view proposal details but cannot modify them.

    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientProposalSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "proposal_type"]
    ordering_fields = ["created_at", "valid_until"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Filter proposals by authenticated client portal user's client.

        TIER 0:
        - Client portal users: see only their client's proposals
        - Firm users: see all proposals for their firm
        """
        from modules.crm.models import Proposal

        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            return Proposal.objects.filter(client=portal_user.client).select_related("client", "prospect")

        return Proposal.objects.filter(firm=firm).select_related("client", "prospect")

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Accept a proposal (client-side acceptance).

        Creates a DocuSign envelope for e-signature workflow.
        """
        import base64
        import logging
        from modules.esignature.docusign_service import DocuSignService
        from modules.esignature.models import DocuSignConnection, Envelope
        
        logger = logging.getLogger(__name__)
        proposal = self.get_object()

        # Verify proposal can be accepted
        if proposal.status not in ["sent", "under_review"]:
            return Response({"error": "Proposal cannot be accepted. Status must be sent or under review."}, status=400)

        # Check if firm has DocuSign connection
        try:
            connection = DocuSignConnection.objects.get(firm=proposal.firm, is_active=True)
        except DocuSignConnection.DoesNotExist:
            return Response(
                {
                    "error": "E-signature not configured. Please contact your administrator to set up DocuSign integration.",
                    "proposal_number": proposal.proposal_number,
                },
                status=400
            )
        
        # Check if envelope already exists for this proposal
        existing_envelope = Envelope.objects.filter(
            proposal=proposal,
            status__in=["sent", "delivered", "signed"]
        ).first()
        
        if existing_envelope:
            return Response(
                {
                    "status": "pending_signature",
                    "message": "Proposal is already pending signature.",
                    "envelope_id": existing_envelope.envelope_id,
                    "proposal_number": proposal.proposal_number,
                }
            )
        
        try:
            # Generate proposal document (placeholder - would use actual proposal PDF)
            # In production, this would render the proposal as a PDF
            document_content = f"PROPOSAL {proposal.proposal_number}\n\nThis is a placeholder document."
            document_base64 = base64.b64encode(document_content.encode()).decode()
            
            # Prepare recipient information
            recipients = [
                {
                    "email": request.user.email,
                    "name": request.user.get_full_name() or request.user.username,
                    "recipient_id": 1,
                    "routing_order": 1,
                }
            ]
            
            # Create envelope via DocuSign
            service = DocuSignService(connection=connection)
            envelope_data = service.create_envelope(
                document_base64=document_base64,
                document_name=f"Proposal_{proposal.proposal_number}.pdf",
                recipients=recipients,
                email_subject=f"Please sign proposal {proposal.proposal_number}",
                email_message=f"Please review and sign the attached proposal.",
                status="sent",
            )
            
            # Create envelope record
            envelope = Envelope.objects.create(
                firm=proposal.firm,
                connection=connection,
                envelope_id=envelope_data["envelopeId"],
                status=envelope_data["status"],
                proposal=proposal,
                subject=f"Proposal {proposal.proposal_number}",
                message="Please review and sign the attached proposal.",
                recipients=recipients,
                sent_at=timezone.now(),
                created_by=request.user,
            )
            
            # Update proposal status
            proposal.status = "pending_signature"
            proposal.save(update_fields=["status", "updated_at"])
            
            logger.info(f"Created DocuSign envelope {envelope.envelope_id} for proposal {proposal.proposal_number}")
            
            return Response(
                {
                    "status": "pending_signature",
                    "message": "E-signature request sent successfully. Please check your email to sign the proposal.",
                    "envelope_id": envelope.envelope_id,
                    "proposal_number": proposal.proposal_number,
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create DocuSign envelope for proposal {proposal.proposal_number}: {str(e)}")
            return Response(
                {
                    "error": f"Failed to send e-signature request: {str(e)}",
                    "proposal_number": proposal.proposal_number,
                },
                status=500
            )


class ClientContractViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Contracts (read-only).

    Shows active and historical contracts for the client.
    Includes contract document download links.

    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientContractSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["start_date", "end_date", "created_at"]
    ordering = ["-start_date"]

    def get_queryset(self):
        """
        Filter contracts by authenticated client portal user's client.

        TIER 0:
        - Client portal users: see only their client's contracts
        - Firm users: see all contracts for their firm
        """
        from modules.crm.models import Contract

        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            return Contract.objects.filter(client=portal_user.client).select_related("client", "proposal", "signed_by")

        return Contract.objects.filter(firm=firm).select_related("client", "proposal", "signed_by")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Get download link for contract document.

        Returns the S3 URL for the signed contract PDF.
        """
        contract = self.get_object()

        if not contract.contract_file_url:
            return Response({"error": "No contract document available for download."}, status=404)

        return Response(
            {
                "download_url": contract.contract_file_url,
                "contract_number": contract.contract_number,
                "filename": f"{contract.contract_number}.pdf",
            }
        )


class ClientEngagementHistoryViewSet(QueryTimeoutMixin, PortalAccessMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Engagement History (read-only).

    Shows engagement version history with renewal tracking.
    Displays the full engagement timeline for the client.

    TIER 2: Portal-accessible endpoint (portal users + firm users allowed).
    """

    serializer_class = ClientEngagementDetailSerializer
    permission_classes = [IsPortalUserOrFirmUser, PortalFirmAccessPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["version", "start_date"]
    ordering = ["-version"]

    def get_queryset(self):
        """
        Filter engagements by authenticated client portal user's client.

        TIER 0:
        - Client portal users: see only their client's engagements
        - Firm users: see all engagements for their firm
        """
        firm = get_request_firm(self.request)
        portal_user = self.get_validated_portal_user(self.request)

        if portal_user:
            return (
                ClientEngagement.objects.filter(client=portal_user.client)
                .select_related("client", "contract", "parent_engagement")
                .prefetch_related("renewals")
            )

        return (
            ClientEngagement.objects.filter(client__firm=firm)
            .select_related("client", "contract", "parent_engagement")
            .prefetch_related("renewals")
        )

    @action(detail=False, methods=["get"])
    def timeline(self, request):
        """
        Get engagement timeline visualization data.

        Returns all engagements ordered by version for timeline display.
        """
        portal_user = self.get_validated_portal_user(request)
        if portal_user is None:
            return Response({"error": "Only client portal users can access this endpoint"}, status=403)
        client = portal_user.client

        with self.with_query_timeout():
            engagements = ClientEngagement.objects.filter(client=client).select_related("contract").order_by("version")

            serializer = self.get_serializer(engagements, many=True)

            return Response(
                {"client_name": client.company_name, "total_versions": engagements.count(), "timeline": serializer.data}
            )


class ConsentRecordViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ConsentRecord (CRM-INT-4).
    
    Provides read-only access to consent records with chain verification and export.
    Consent records are immutable - they cannot be updated or deleted via API.
    
    TIER 0: Uses FirmScopedMixin for automatic tenant isolation via contact->client->firm.
    """
    
    serializer_class = ConsentRecordSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        BoundedSearchFilter,
    ]
    filterset_fields = {
        "contact": ["exact"],
        "consent_type": ["exact", "in"],
        "action": ["exact", "in"],
        "legal_basis": ["exact", "in"],
        "timestamp": ["gte", "lte", "date"],
    }
    search_fields = ["contact__first_name", "contact__last_name", "contact__email", "source"]
    ordering_fields = ["timestamp", "consent_type", "action"]
    ordering = ["-timestamp"]
    
    def get_queryset(self):
        """
        Get consent records for the current firm.
        
        TIER 0: Auto-filters by firm via contact->client->firm relationship.
        """
        firm = get_request_firm(self.request)
        
        with self.with_query_timeout():
            queryset = ConsentRecord.objects.filter(
                contact__client__firm=firm
            ).select_related(
                "contact",
                "contact__client",
                "actor"
            )
        
        return queryset
    
    def _get_firm_contact(self, request, contact_id):
        """
        Helper method to get a contact and verify it belongs to the current firm.
        
        Args:
            request: The request object
            contact_id: ID of the contact to retrieve
        
        Returns:
            Contact: The contact object if found and belongs to firm
        
        Raises:
            Contact.DoesNotExist: If contact not found or doesn't belong to firm
        """
        firm = get_request_firm(request)
        return Contact.objects.get(id=contact_id, client__firm=firm)
    
    @action(detail=False, methods=["post"], url_path="create")
    def create_consent_record(self, request):
        """
        Create a new consent record.
        
        This endpoint allows creating new consent records with proper validation.
        The record hash will be automatically computed on save.
        """
        serializer = ConsentRecordCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Verify the contact belongs to the current firm
        contact = serializer.validated_data['contact']
        try:
            # Use helper method to verify firm membership
            self._get_firm_contact(request, contact.id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found or does not belong to your firm"},
                status=404
            )
        
        consent_record = serializer.save()
        
        # Return the created record
        output_serializer = ConsentRecordSerializer(consent_record)
        return Response(output_serializer.data, status=201)

    @action(detail=False, methods=["post"], url_path="request-double-opt-in")
    def request_double_opt_in(self, request):
        """
        Initiate double opt-in for a contact.

        Sends a confirmation email with a public opt-in link.
        """
        contact_id = request.data.get("contact_id")
        if not contact_id:
            return Response({"error": "contact_id is required"}, status=400)

        try:
            contact = self._get_firm_contact(request, contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found or does not belong to your firm"},
                status=404,
            )

        consent_text = request.data.get("consent_text", "")
        consent_version = request.data.get("consent_version", "")
        source = request.data.get("source", "signup_form")
        source_url = request.data.get("source_url", "")

        opt_in_request = EmailOptInRequest.create_request(
            contact,
            requested_by=request.user,
            source=source,
            source_url=source_url,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            consent_text=consent_text,
            consent_version=consent_version,
        )

        unsubscribe_token = EmailUnsubscribeToken.create_token(
            contact,
            source="double_opt_in",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        confirm_url = request.build_absolute_uri(
            reverse("public-opt-in-detail", args=[opt_in_request.token])
        )
        unsubscribe_url = request.build_absolute_uri(
            reverse("public-unsubscribe-detail", args=[unsubscribe_token.token])
        )

        branding = PortalBranding.objects.filter(firm=contact.client.firm).first()
        sender_name = branding.email_from_name if branding and branding.email_from_name else contact.client.firm.name
        sender_email = (
            branding.email_from_address
            if branding and branding.email_from_address
            else getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@consultantpro.com")
        )
        reply_to = [branding.email_reply_to] if branding and branding.email_reply_to else None
        physical_address = branding.email_physical_address if branding else ""

        compliance = EmailComplianceDetails(
            sender_name=sender_name,
            sender_email=sender_email,
            reply_to=reply_to,
            physical_address=physical_address,
            unsubscribe_url=unsubscribe_url,
            company_name=contact.client.firm.name,
            compliance_reason="You are receiving this email to confirm your subscription.",
        )

        html_content = (
            "<p>Please confirm your subscription by clicking the link below:</p>"
            f"<p><a href=\"{confirm_url}\">Confirm subscription</a></p>"
        )
        if branding:
            html_content = branding.render_email_html(html_content)

        EmailNotification.send(
            to=[contact.email],
            subject="Confirm your subscription",
            html_content=html_content,
            text_content=f"Confirm your subscription: {confirm_url}",
            from_email=sender_email,
            from_name=sender_name,
            compliance=compliance,
        )

        return Response(
            {
                "status": "confirmation_sent",
                "contact_id": contact.id,
                "opt_in_request_id": opt_in_request.id,
            },
            status=201,
        )
    
    @action(detail=False, methods=["get"], url_path="by-contact/(?P<contact_id>[0-9]+)")
    def by_contact(self, request, contact_id=None):
        """
        Get all consent records for a specific contact.
        
        Returns records ordered by timestamp (newest first).
        """
        try:
            contact = self._get_firm_contact(request, contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found or does not belong to your firm"},
                status=404
            )
        
        with self.with_query_timeout():
            records = ConsentRecord.objects.filter(
                contact=contact
            ).select_related("actor", "contact", "contact__client").order_by("-timestamp")
        
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"], url_path="current-status/(?P<contact_id>[0-9]+)")
    def current_status(self, request, contact_id=None):
        """
        Get current consent status for a contact across all consent types.
        
        Returns the latest action for each consent type.
        """
        try:
            contact = self._get_firm_contact(request, contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found or does not belong to your firm"},
                status=404
            )
        
        # Get current status for each consent type
        consent_status = {}
        for consent_type, display_name in ConsentRecord.CONSENT_TYPE_CHOICES:
            status = ConsentRecord.get_current_consent(contact, consent_type)
            consent_status[consent_type] = {
                "display_name": display_name,
                "has_consent": status["has_consent"],
                "latest_action": status["latest_action"],
                "timestamp": status["timestamp"].isoformat() if status["timestamp"] else None,
            }
        
        return Response({
            "contact": {
                "id": contact.id,
                "name": contact.full_name,
                "email": contact.email,
            },
            "consent_status": consent_status,
        })
    
    @action(detail=False, methods=["get"], url_path="verify-chain/(?P<contact_id>[0-9]+)")
    def verify_chain(self, request, contact_id=None):
        """
        Verify the integrity of the consent chain for a contact.
        
        Validates the cryptographic hash chain for all consent records.
        """
        try:
            contact = self._get_firm_contact(request, contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found or does not belong to your firm"},
                status=404
            )
        
        # Get consent_type filter if provided
        consent_type = request.query_params.get('consent_type')
        
        # Verify chain
        verification = ConsentRecord.verify_chain(contact, consent_type)
        
        return Response({
            "contact": {
                "id": contact.id,
                "name": contact.full_name,
                "email": contact.email,
            },
            "consent_type": consent_type,
            "verification": verification,
        })
    
    @action(detail=False, methods=["get"], url_path="export-proof/(?P<contact_id>[0-9]+)")
    def export_proof(self, request, contact_id=None):
        """
        Export consent proof for a contact (GDPR right to access).
        
        Returns complete consent history with chain verification.
        This export can be provided to the data subject or regulatory authorities.
        """
        try:
            contact = self._get_firm_contact(request, contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"error": "Contact not found or does not belong to your firm"},
                status=404
            )
        
        # Get consent_type filter if provided
        consent_type = request.query_params.get('consent_type')
        
        # Export proof
        proof_data = ConsentRecord.export_consent_proof(contact, consent_type)
        
        serializer = ConsentProofExportSerializer(proof_data)
        
        return Response(serializer.data)
