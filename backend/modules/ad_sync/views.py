"""
Active Directory Synchronization Views

REST API views for managing AD sync configuration and triggering syncs.
"""

import logging

from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.ad_sync.connector import ActiveDirectoryConnector
from modules.ad_sync.models import (
    ADGroupMapping,
    ADProvisioningRule,
    ADSyncConfig,
    ADSyncLog,
    ADUserMapping,
)
from modules.ad_sync.serializers import (
    ADConnectionTestSerializer,
    ADGroupMappingSerializer,
    ADProvisioningRuleSerializer,
    ADSyncConfigSerializer,
    ADSyncLogSerializer,
    ADSyncTriggerSerializer,
    ADUserMappingSerializer,
)
from modules.ad_sync.sync_service import ADSyncService
from modules.firm.models import Firm

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(description="List AD sync configurations"),
    retrieve=extend_schema(description="Get AD sync configuration details"),
    create=extend_schema(description="Create AD sync configuration"),
    update=extend_schema(description="Update AD sync configuration"),
    partial_update=extend_schema(description="Partially update AD sync configuration"),
    destroy=extend_schema(description="Delete AD sync configuration"),
)
class ADSyncConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Active Directory sync configuration.
    
    Provides CRUD operations for AD sync settings.
    """
    
    serializer_class = ADSyncConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter configurations by user's firm."""
        user = self.request.user
        # Get firms the user belongs to
        firm_ids = user.firm_memberships.filter(is_active=True).values_list('firm_id', flat=True)
        return ADSyncConfig.objects.filter(firm_id__in=firm_ids)
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        request=ADSyncTriggerSerializer,
        responses={200: ADSyncLogSerializer},
        description="Trigger manual AD synchronization"
    )
    @action(detail=True, methods=['post'])
    def trigger_sync(self, request, pk=None):
        """
        Trigger manual AD synchronization.
        
        AD-4: Manual on-demand sync capability.
        """
        config = self.get_object()
        
        if not config.is_enabled:
            return Response(
                {'error': 'AD sync is not enabled for this firm'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ADSyncTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sync_type = serializer.validated_data.get('sync_type', 'manual')
        
        try:
            # Trigger sync
            logger.info(f"Manual AD sync triggered by {request.user} for firm {config.firm}")
            
            sync_service = ADSyncService(firm=config.firm)
            sync_log = sync_service.sync(sync_type=sync_type, triggered_by=request.user)
            
            # Return sync log
            log_serializer = ADSyncLogSerializer(sync_log)
            return Response(log_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Manual AD sync failed: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        request=ADConnectionTestSerializer,
        responses={
            200: {'type': 'object', 'properties': {
                'success': {'type': 'boolean'},
                'message': {'type': 'string'}
            }}
        },
        description="Test AD connection with provided credentials"
    )
    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """
        Test AD connection without saving configuration.
        
        Useful for validating credentials before saving.
        """
        serializer = ADConnectionTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            connector = ActiveDirectoryConnector(
                server_url=serializer.validated_data['server_url'],
                service_account_dn=serializer.validated_data['service_account_dn'],
                password=serializer.validated_data['password'],
                base_dn=serializer.validated_data['base_dn']
            )
            
            success, message = connector.test_connection()
            connector.close()
            
            return Response({
                'success': success,
                'message': message
            }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"AD connection test failed: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': f"Connection test failed: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(description="List AD sync logs"),
    retrieve=extend_schema(description="Get AD sync log details"),
)
class ADSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing AD sync logs.
    
    Read-only access to sync history and results.
    """
    
    serializer_class = ADSyncLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter logs by user's firms."""
        user = self.request.user
        firm_ids = user.firm_memberships.filter(is_active=True).values_list('firm_id', flat=True)
        return ADSyncLog.objects.filter(firm_id__in=firm_ids).order_by('-started_at')


@extend_schema_view(
    list=extend_schema(description="List AD provisioning rules"),
    retrieve=extend_schema(description="Get AD provisioning rule details"),
    create=extend_schema(description="Create AD provisioning rule"),
    update=extend_schema(description="Update AD provisioning rule"),
    partial_update=extend_schema(description="Partially update AD provisioning rule"),
    destroy=extend_schema(description="Delete AD provisioning rule"),
)
class ADProvisioningRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AD provisioning rules.
    
    AD-3: Provisioning rules engine.
    """
    
    serializer_class = ADProvisioningRuleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter rules by user's firms."""
        user = self.request.user
        firm_ids = user.firm_memberships.filter(is_active=True).values_list('firm_id', flat=True)
        return ADProvisioningRule.objects.filter(firm_id__in=firm_ids).order_by('priority', 'name')
    
    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)


@extend_schema_view(
    list=extend_schema(description="List AD group mappings"),
    retrieve=extend_schema(description="Get AD group mapping details"),
    create=extend_schema(description="Create AD group mapping"),
    update=extend_schema(description="Update AD group mapping"),
    partial_update=extend_schema(description="Partially update AD group mapping"),
    destroy=extend_schema(description="Delete AD group mapping"),
)
class ADGroupMappingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AD group mappings.
    
    AD-5: Group sync functionality.
    """
    
    serializer_class = ADGroupMappingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter mappings by user's firms."""
        user = self.request.user
        firm_ids = user.firm_memberships.filter(is_active=True).values_list('firm_id', flat=True)
        return ADGroupMapping.objects.filter(firm_id__in=firm_ids)


@extend_schema_view(
    list=extend_schema(description="List AD user mappings"),
    retrieve=extend_schema(description="Get AD user mapping details"),
)
class ADUserMappingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing AD user mappings.
    
    Read-only access to AD-synchronized users.
    """
    
    serializer_class = ADUserMappingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter mappings by user's firms."""
        user = self.request.user
        firm_ids = user.firm_memberships.filter(is_active=True).values_list('firm_id', flat=True)
        return ADUserMapping.objects.filter(firm_id__in=firm_ids).select_related('user')
