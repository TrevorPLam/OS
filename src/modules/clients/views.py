"""
API Views for Clients module.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from modules.clients.models import (
    Client,
    ClientPortalUser,
    ClientNote,
    ClientEngagement,
    ClientComment,
    ClientChatThread,
    ClientMessage,
)
from modules.clients.serializers import (
    ClientSerializer,
    ClientPortalUserSerializer,
    ClientNoteSerializer,
    ClientEngagementSerializer,
    ClientCommentSerializer,
    ClientProjectSerializer,
    ClientMessageSerializer,
    ClientChatThreadSerializer,
    ClientProposalSerializer,
    ClientContractSerializer,
    ClientEngagementDetailSerializer,
)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client management (Post-sale).

    Provides CRUD operations for clients that have been converted from prospects.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'account_manager', 'portal_enabled']
    search_fields = ['company_name', 'primary_contact_name', 'primary_contact_email']
    ordering_fields = ['company_name', 'client_since', 'total_lifetime_value']
    ordering = ['-client_since']

    @action(detail=True, methods=['get'])
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
            'projects_count': client.projects.count(),
            'active_projects': client.projects.filter(status='in_progress').count(),
            'invoices_count': client.invoices.count(),
            'outstanding_invoices': client.invoices.filter(status__in=['sent', 'partial', 'overdue']).count(),
            'engagements_count': client.engagements.count(),
            'portal_users_count': client.portal_users.count(),
        }

        return Response(overview_data)

    @action(detail=True, methods=['post'])
    def enable_portal(self, request, pk=None):
        """Enable client portal access for this client."""
        client = self.get_object()
        client.portal_enabled = True
        client.save()
        return Response({'status': 'portal enabled', 'client': ClientSerializer(client).data})

    @action(detail=True, methods=['post'])
    def disable_portal(self, request, pk=None):
        """Disable client portal access for this client."""
        client = self.get_object()
        client.portal_enabled = False
        client.save()
        return Response({'status': 'portal disabled', 'client': ClientSerializer(client).data})


class ClientPortalUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Portal User management.

    Manages client-side users with portal access.
    """
    queryset = ClientPortalUser.objects.all()
    serializer_class = ClientPortalUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['client', 'role']
    search_fields = ['user__username', 'user__email', 'client__company_name']

    def perform_create(self, serializer):
        """Set invited_by to current user."""
        serializer.save(invited_by=self.request.user)


class ClientNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Notes (internal only).

    Notes are NOT visible to clients - for internal team use only.
    """
    queryset = ClientNote.objects.all()
    serializer_class = ClientNoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['client', 'author', 'is_pinned']
    search_fields = ['note', 'client__company_name']

    def get_queryset(self):
        """Optionally filter by client_id query param."""
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client_id')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset


class ClientEngagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Engagements.

    Tracks all contracts/engagements with version history.
    """
    queryset = ClientEngagement.objects.all()
    serializer_class = ClientEngagementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'status']
    ordering_fields = ['start_date', 'version', 'contracted_value']
    ordering = ['-start_date']

    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get all engagements for a specific client."""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response({'error': 'client_id query parameter required'}, status=400)

        engagements = self.queryset.filter(client_id=client_id)
        serializer = self.get_serializer(engagements, many=True)
        return Response(serializer.data)


class ClientProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Projects (read-only).

    Shows projects for the authenticated client portal user.
    Clients can view their projects and tasks, but cannot modify them.
    """
    serializer_class = ClientProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['name', 'start_date', 'end_date']
    ordering = ['-start_date']

    def get_queryset(self):
        """
        Filter projects by authenticated client portal user's client.

        Only returns projects for the client that the portal user belongs to.
        """
        from modules.projects.models import Project

        user = self.request.user

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Check if user has permission to view projects
            if not portal_user.can_view_projects:
                return Project.objects.none()

            # Return projects for this client
            return Project.objects.filter(client=portal_user.client).prefetch_related('tasks_set')

        except ClientPortalUser.DoesNotExist:
            # Not a client portal user - check if firm user
            # Firm users can view all projects (handled by permissions)
            return Project.objects.all()

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """
        Get all tasks for a specific project.

        Returns tasks with client comments.
        """
        project = self.get_object()
        from modules.projects.models import Task
        from modules.clients.serializers import ClientTaskSerializer

        tasks = Task.objects.filter(project=project).order_by('position', '-created_at')
        serializer = ClientTaskSerializer(tasks, many=True)
        return Response(serializer.data)


class ClientCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Comments on Tasks.

    Allows client portal users to comment on tasks in their projects.
    Comments are visible to both firm team and client.
    """
    queryset = ClientComment.objects.all()
    serializer_class = ClientCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'client', 'is_read_by_firm']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter comments based on user type.

        - Client portal users: only see comments for their client
        - Firm users: see all comments
        """
        user = self.request.user
        queryset = super().get_queryset()

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)
            # Filter to only this client's comments
            queryset = queryset.filter(client=portal_user.client)
        except ClientPortalUser.DoesNotExist:
            # Firm user - can see all comments
            pass

        # Filter by task_id if provided in query params
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        return queryset

    def perform_create(self, serializer):
        """
        Create comment with automatic client detection.

        The serializer handles setting author and client from request context.
        """
        serializer.save()

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a client comment as read by firm team.

        Only accessible to firm users (not client portal users).
        """
        comment = self.get_object()

        # Check if user is a firm user (not a client portal user)
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            return Response(
                {'error': 'Only firm team members can mark comments as read'},
                status=403
            )
        except ClientPortalUser.DoesNotExist:
            # Firm user - can mark as read
            from django.utils import timezone
            comment.is_read_by_firm = True
            comment.read_by = request.user
            comment.read_at = timezone.now()
            comment.save()

            return Response({
                'status': 'marked as read',
                'comment': ClientCommentSerializer(comment).data
            })

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get all unread client comments.

        Only accessible to firm users.
        """
        # Check if user is a firm user
        try:
            portal_user = ClientPortalUser.objects.get(user=request.user)
            return Response(
                {'error': 'Only firm team members can access this endpoint'},
                status=403
            )
        except ClientPortalUser.DoesNotExist:
            # Firm user - get unread comments
            unread_comments = self.queryset.filter(is_read_by_firm=False)
            serializer = self.get_serializer(unread_comments, many=True)
            return Response(serializer.data)


class ClientInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Invoices (read-only).

    Shows invoices for the authenticated client portal user.
    Clients can view their invoices but cannot modify them.
    Includes payment link generation for Stripe.
    """
    serializer_class = None  # Will be imported below
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['invoice_number', 'issue_date', 'due_date', 'total_amount']
    ordering = ['-issue_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from modules.clients.serializers import ClientInvoiceSerializer
        self.serializer_class = ClientInvoiceSerializer

    def get_queryset(self):
        """
        Filter invoices by authenticated client portal user's client.

        Only returns invoices for the client that the portal user belongs to.
        """
        from modules.finance.models import Invoice

        user = self.request.user

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Check if user has permission to view billing
            if not portal_user.can_view_billing:
                return Invoice.objects.none()

            # Return invoices for this client
            return Invoice.objects.filter(
                client=portal_user.client
            ).select_related('client', 'project').order_by('-issue_date')

        except ClientPortalUser.DoesNotExist:
            # Not a client portal user - check if firm user
            # Firm users can view all invoices (handled by permissions)
            return Invoice.objects.all().select_related('client', 'project')

    @action(detail=True, methods=['post'])
    def generate_payment_link(self, request, pk=None):
        """
        Generate Stripe payment link for an invoice.

        Returns a Stripe Checkout session URL that the client can use to pay.
        """
        invoice = self.get_object()

        # Verify invoice can be paid
        if invoice.status not in ['sent', 'partial', 'overdue']:
            return Response(
                {'error': 'Invoice cannot be paid online. Status must be sent, partial, or overdue.'},
                status=400
            )

        if invoice.balance_due <= 0:
            return Response(
                {'error': 'Invoice has no outstanding balance.'},
                status=400
            )

        # TODO: Implement Stripe Checkout session creation
        # For now, return a placeholder response
        # In production, this would create a Stripe Checkout session:
        # 1. Create Stripe checkout session with invoice details
        # 2. Return the session URL for redirect
        # 3. Handle webhook for payment confirmation

        payment_link = f"https://checkout.stripe.com/pay/placeholder_{invoice.invoice_number}"

        return Response({
            'status': 'payment_link_generated',
            'payment_url': payment_link,
            'invoice_number': invoice.invoice_number,
            'amount_due': str(invoice.balance_due),
            'currency': invoice.currency,
            'message': 'Stripe integration pending - this is a placeholder URL'
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get invoice summary for the client.

        Returns counts and totals by status.
        """
        user = request.user

        # Get client
        try:
            portal_user = ClientPortalUser.objects.get(user=user)
            client = portal_user.client
        except ClientPortalUser.DoesNotExist:
            return Response(
                {'error': 'Only client portal users can access this endpoint'},
                status=403
            )

        from modules.finance.models import Invoice
        from django.db.models import Sum, Count

        invoices = Invoice.objects.filter(client=client)

        # Get summary statistics
        summary = {
            'total_invoices': invoices.count(),
            'total_billed': invoices.aggregate(total=Sum('total_amount'))['total'] or 0,
            'total_paid': invoices.aggregate(total=Sum('amount_paid'))['total'] or 0,
            'total_outstanding': sum(inv.balance_due for inv in invoices),
            'by_status': {},
        }

        # Count by status
        status_counts = invoices.values('status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )

        for item in status_counts:
            summary['by_status'][item['status']] = {
                'count': item['count'],
                'total': float(item['total']) if item['total'] else 0,
            }

        # Overdue invoices
        overdue_invoices = invoices.filter(status__in=['sent', 'partial'])
        from django.utils import timezone
        today = timezone.now().date()
        overdue_count = sum(1 for inv in overdue_invoices if inv.due_date < today)

        summary['overdue_count'] = overdue_count

        return Response(summary)


class ClientChatThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Chat Threads.

    Manages daily chat threads between clients and firm team.
    Threads auto-rotate daily for organization.
    """
    serializer_class = ClientChatThreadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['client', 'is_active', 'date']
    ordering_fields = ['date', 'last_message_at']
    ordering = ['-date']

    def get_queryset(self):
        """
        Filter threads based on user type.

        - Client portal users: only see their client's threads
        - Firm users: see all threads
        """
        user = self.request.user
        queryset = ClientChatThread.objects.all().prefetch_related('messages')

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Check if user has permission to message team
            if not portal_user.can_message_team:
                return ClientChatThread.objects.none()

            # Filter to only this client's threads
            queryset = queryset.filter(client=portal_user.client)
        except ClientPortalUser.DoesNotExist:
            # Firm user - can see all threads
            pass

        return queryset

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get or create today's active thread for the client.

        Returns the active thread with recent messages.
        """
        user = request.user

        # Get client
        try:
            portal_user = ClientPortalUser.objects.get(user=user)
            client = portal_user.client
        except ClientPortalUser.DoesNotExist:
            return Response(
                {'error': 'Only client portal users can access this endpoint'},
                status=403
            )

        # Get or create today's thread
        from django.utils import timezone
        today = timezone.now().date()

        thread, created = ClientChatThread.objects.get_or_create(
            client=client,
            date=today,
            defaults={'is_active': True}
        )

        serializer = self.get_serializer(thread)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive a chat thread.

        Only accessible to firm users.
        """
        # Check if user is a firm user
        try:
            ClientPortalUser.objects.get(user=request.user)
            return Response(
                {'error': 'Only firm team members can archive threads'},
                status=403
            )
        except ClientPortalUser.DoesNotExist:
            # Firm user - can archive
            thread = self.get_object()
            from django.utils import timezone
            thread.is_active = False
            thread.archived_at = timezone.now()
            thread.save()

            return Response({
                'status': 'thread archived',
                'thread': ClientChatThreadSerializer(thread).data
            })


class ClientMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Client Messages.

    Handles real-time messaging between clients and firm team.
    Messages are organized by daily threads.
    """
    serializer_class = ClientMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['thread', 'is_from_client', 'message_type', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """
        Filter messages based on user type.

        - Client portal users: only see their client's messages
        - Firm users: see all messages
        """
        user = self.request.user
        queryset = ClientMessage.objects.all().select_related('thread', 'sender')

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Check if user has permission to message team
            if not portal_user.can_message_team:
                return ClientMessage.objects.none()

            # Filter to only this client's messages
            queryset = queryset.filter(thread__client=portal_user.client)
        except ClientPortalUser.DoesNotExist:
            # Firm user - can see all messages
            pass

        return queryset

    @action(detail=True, methods=['post'])
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

        return Response({
            'status': 'marked as read',
            'message': ClientMessageSerializer(message).data
        })

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get unread messages for the current user.

        For clients: get unread messages from firm
        For firm: get unread messages from all clients
        """
        user = request.user
        queryset = self.get_queryset()

        # Check if user is a client portal user
        try:
            ClientPortalUser.objects.get(user=user)
            # Client: get unread messages from firm (is_from_client=False)
            unread = queryset.filter(is_read=False, is_from_client=False)
        except ClientPortalUser.DoesNotExist:
            # Firm: get unread messages from clients (is_from_client=True)
            unread = queryset.filter(is_read=False, is_from_client=True)

        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)


class ClientProposalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Proposals (read-only).

    Shows proposals sent to the client.
    Clients can view proposal details but cannot modify them.
    """
    serializer_class = ClientProposalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'proposal_type']
    ordering_fields = ['created_at', 'valid_until']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter proposals by authenticated client portal user's client.

        Only returns proposals for the client that the portal user belongs to.
        """
        from modules.crm.models import Proposal

        user = self.request.user

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Return proposals for this client (update/renewal proposals)
            queryset = Proposal.objects.filter(
                client=portal_user.client
            ).select_related('client', 'prospect')

            return queryset

        except ClientPortalUser.DoesNotExist:
            # Firm user - can view all proposals
            return Proposal.objects.all().select_related('client', 'prospect')

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept a proposal (client-side acceptance).

        This is a placeholder for e-signature integration.
        In production, this would trigger DocuSign/HelloSign workflow.
        """
        proposal = self.get_object()

        # Verify proposal can be accepted
        if proposal.status not in ['sent', 'under_review']:
            return Response(
                {'error': 'Proposal cannot be accepted. Status must be sent or under review.'},
                status=400
            )

        # TODO: Implement e-signature workflow
        # For now, return placeholder response
        return Response({
            'status': 'pending_signature',
            'message': 'E-signature integration pending. This would trigger DocuSign/HelloSign workflow.',
            'proposal_number': proposal.proposal_number,
        })


class ClientContractViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Contracts (read-only).

    Shows active and historical contracts for the client.
    Includes contract document download links.
    """
    serializer_class = ClientContractSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        """
        Filter contracts by authenticated client portal user's client.

        Only returns contracts for the client that the portal user belongs to.
        """
        from modules.crm.models import Contract

        user = self.request.user

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Return contracts for this client
            queryset = Contract.objects.filter(
                client=portal_user.client
            ).select_related('client', 'proposal', 'signed_by')

            return queryset

        except ClientPortalUser.DoesNotExist:
            # Firm user - can view all contracts
            return Contract.objects.all().select_related('client', 'proposal', 'signed_by')

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Get download link for contract document.

        Returns the S3 URL for the signed contract PDF.
        """
        contract = self.get_object()

        if not contract.contract_file_url:
            return Response(
                {'error': 'No contract document available for download.'},
                status=404
            )

        return Response({
            'download_url': contract.contract_file_url,
            'contract_number': contract.contract_number,
            'filename': f"{contract.contract_number}.pdf"
        })


class ClientEngagementHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Client Portal - Engagement History (read-only).

    Shows engagement version history with renewal tracking.
    Displays the full engagement timeline for the client.
    """
    serializer_class = ClientEngagementDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['version', 'start_date']
    ordering = ['-version']

    def get_queryset(self):
        """
        Filter engagements by authenticated client portal user's client.

        Only returns engagements for the client that the portal user belongs to.
        """
        user = self.request.user

        # Check if user is a client portal user
        try:
            portal_user = ClientPortalUser.objects.get(user=user)

            # Return engagements for this client
            queryset = ClientEngagement.objects.filter(
                client=portal_user.client
            ).select_related('client', 'contract', 'parent_engagement').prefetch_related('renewals')

            return queryset

        except ClientPortalUser.DoesNotExist:
            # Firm user - can view all engagements
            return ClientEngagement.objects.all().select_related('client', 'contract', 'parent_engagement').prefetch_related('renewals')

    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """
        Get engagement timeline visualization data.

        Returns all engagements ordered by version for timeline display.
        """
        user = request.user

        # Get client
        try:
            portal_user = ClientPortalUser.objects.get(user=user)
            client = portal_user.client
        except ClientPortalUser.DoesNotExist:
            return Response(
                {'error': 'Only client portal users can access this endpoint'},
                status=403
            )

        engagements = ClientEngagement.objects.filter(
            client=client
        ).select_related('contract').order_by('version')

        serializer = self.get_serializer(engagements, many=True)

        return Response({
            'client_name': client.company_name,
            'total_versions': engagements.count(),
            'timeline': serializer.data
        })
