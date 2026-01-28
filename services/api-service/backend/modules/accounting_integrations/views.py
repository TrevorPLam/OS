"""Views for Accounting Integrations API."""

import uuid
import logging
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from modules.firm.utils import get_request_firm
from modules.finance.models import Invoice
from modules.clients.models import Client

from .models import AccountingOAuthConnection, InvoiceSyncMapping, CustomerSyncMapping
from .serializers import (
    AccountingOAuthConnectionSerializer,
    InvoiceSyncMappingSerializer,
    CustomerSyncMappingSerializer,
)
from .quickbooks_service import QuickBooksService
from .xero_service import XeroService
from .sync_service import AccountingSyncService

logger = logging.getLogger(__name__)


class AccountingOAuthConnectionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing accounting OAuth connections.
    
    Provides CRUD operations for QuickBooks and Xero connections.
    """

    serializer_class = AccountingOAuthConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get connections for user's firm."""
        firm = get_request_firm(self.request)
        return AccountingOAuthConnection.objects.filter(firm=firm)

    @action(detail=False, methods=['post'])
    def initiate_oauth(self, request):
        """
        Initiate OAuth flow for accounting provider.
        
        Body:
            provider: 'quickbooks' or 'xero'
        
        Returns:
            authorization_url: URL to redirect user to
            state_token: CSRF protection token
        """
        provider = request.data.get('provider')
        if provider not in ['quickbooks', 'xero']:
            return Response(
                {'error': 'Invalid provider'},
                status=status.HTTP_400_BAD_REQUEST
            )

        firm = get_request_firm(request)

        # Initialize service
        if provider == 'quickbooks':
            service = QuickBooksService()
        else:
            service = XeroService()

        # Generate state token
        state_token = str(uuid.uuid4())

        # Store state in session
        request.session[f'accounting_oauth_state_{state_token}'] = {
            'provider': provider,
            'firm_id': firm.firm_id,
            'user_id': request.user.id,
            'expires_at': (timezone.now() + timedelta(minutes=10)).isoformat(),
        }

        # Get authorization URL
        authorization_url = service.get_authorization_url(state_token)

        return Response({
            'authorization_url': authorization_url,
            'state_token': state_token,
        })

    @action(detail=False, methods=['post'])
    def oauth_callback(self, request):
        """
        Handle OAuth callback from accounting provider.
        
        Body:
            code: Authorization code
            state: State token
            realm_id: QuickBooks company ID (QuickBooks only)
        
        Returns:
            connection: Created connection data
        """
        code = request.data.get('code')
        state = request.data.get('state')
        realm_id = request.data.get('realm_id')  # QuickBooks specific

        if not code or not state:
            return Response(
                {'error': 'Missing code or state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate state token
        state_key = f'accounting_oauth_state_{state}'
        state_data = request.session.get(state_key)

        if not state_data:
            return Response(
                {'error': 'Invalid or expired state token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Clean up state from session
        del request.session[state_key]

        provider = state_data['provider']
        firm_id = state_data['firm_id']
        user_id = state_data['user_id']

        # Initialize service
        if provider == 'quickbooks':
            service = QuickBooksService()
        else:
            service = XeroService()

        # Exchange code for tokens
        result = service.authenticate(code)

        if not result.get('success'):
            return Response(
                {'error': result.get('error', 'Authentication failed')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For Xero, get tenant connections
        tenant_id = realm_id
        company_name = ''

        if provider == 'xero':
            connections_result = service.get_connections(result['access_token'])
            if connections_result.get('success') and connections_result['data']:
                # Use first connection
                tenant_id = connections_result['data'][0]['tenantId']
                company_name = connections_result['data'][0]['tenantName']

        # Create or update connection
        with transaction.atomic():
            connection, created = AccountingOAuthConnection.objects.update_or_create(
                firm_id=firm_id,
                provider=provider,
                defaults={
                    'user_id': user_id,
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token', ''),
                    'token_expires_at': timezone.now() + timedelta(seconds=result.get('expires_in', 3600)),
                    'provider_company_id': tenant_id or realm_id or '',
                    'provider_company_name': company_name,
                    'status': 'active',
                    'error_message': '',
                }
            )

        serializer = self.get_serializer(connection)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """
        Disconnect and delete accounting connection.
        
        Returns:
            success: True if disconnected
        """
        connection = self.get_object()
        connection.delete()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def sync_invoice(self, request, pk=None):
        """
        Sync a specific invoice to accounting system.
        
        Body:
            invoice_id: Invoice ID to sync
        
        Returns:
            success: True if synced
            mapping: Sync mapping data
        """
        connection = self.get_object()
        invoice_id = request.data.get('invoice_id')

        if not invoice_id:
            return Response(
                {'error': 'Missing invoice_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        firm = get_request_firm(request)
        invoice = get_object_or_404(Invoice, pk=invoice_id, firm=firm)

        # Perform sync
        sync_service = AccountingSyncService(connection)
        result = sync_service.sync_invoice(invoice)

        if result.get('success'):
            mapping = result.get('mapping')
            serializer = InvoiceSyncMappingSerializer(mapping)
            return Response({
                'success': True,
                'mapping': serializer.data,
                'already_synced': result.get('already_synced', False)
            })
        else:
            return Response(
                {'error': result.get('error', 'Sync failed')},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def sync_customer(self, request, pk=None):
        """
        Sync a specific customer to accounting system.
        
        Body:
            client_id: Client ID to sync
        
        Returns:
            success: True if synced
            mapping: Sync mapping data
        """
        connection = self.get_object()
        client_id = request.data.get('client_id')

        if not client_id:
            return Response(
                {'error': 'Missing client_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        firm = get_request_firm(request)
        client = get_object_or_404(Client, pk=client_id, firm=firm)

        # Perform sync
        sync_service = AccountingSyncService(connection)
        result = sync_service.sync_customer(client)

        if result.get('success'):
            mapping = result.get('mapping')
            serializer = CustomerSyncMappingSerializer(mapping)
            return Response({
                'success': True,
                'mapping': serializer.data
            })
        else:
            return Response(
                {'error': result.get('error', 'Sync failed')},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def sync_payments(self, request, pk=None):
        """
        Pull payments from accounting system.
        
        Returns:
            success: True if synced
            payment_count: Number of payments processed
        """
        connection = self.get_object()

        # Perform sync
        sync_service = AccountingSyncService(connection)
        result = sync_service.sync_payments()

        if result.get('success'):
            return Response({
                'success': True,
                'payment_count': result.get('payment_count', 0)
            })
        else:
            return Response(
                {'error': result.get('error', 'Sync failed')},
                status=status.HTTP_400_BAD_REQUEST
            )


class InvoiceSyncMappingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for viewing invoice sync mappings.
    
    Read-only access to sync status and history.
    """

    serializer_class = InvoiceSyncMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get mappings for user's firm."""
        firm = get_request_firm(self.request)
        return InvoiceSyncMapping.objects.filter(firm=firm)


class CustomerSyncMappingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for viewing customer sync mappings.
    
    Read-only access to sync status and history.
    """

    serializer_class = CustomerSyncMappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get mappings for user's firm."""
        firm = get_request_firm(self.request)
        return CustomerSyncMapping.objects.filter(firm=firm)
