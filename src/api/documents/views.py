"""
DRF ViewSets for Documents module with S3 upload functionality.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from modules.clients.permissions import DenyPortalAccess
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from modules.documents.models import Folder, Document, Version
from modules.documents.services import S3Service
from modules.firm.utils import FirmScopedMixin, get_request_firm
from modules.firm.permissions import IsFirmOwner
from modules.firm.models import AuditEvent, create_audit_event
from .serializers import FolderSerializer, DocumentSerializer, VersionSerializer


class FolderViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Folder model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Folder
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'project', 'parent', 'visibility']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('client', 'project', 'parent', 'created_by')


class DocumentViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Document model with S3 upload functionality.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Document
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'folder', 'project', 'visibility', 'file_type']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('folder', 'client', 'project', 'uploaded_by')

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload a new document to S3.

        POST /api/documents/documents/upload/

        TIER 0: Automatically includes firm context from request.
        """
        try:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # TIER 0: Get firm from request context
            firm = get_request_firm(request)

            # Get form data
            folder_id = request.data.get('folder')
            client_id = request.data.get('client')
            name = request.data.get('name', file_obj.name)
            description = request.data.get('description', '')
            visibility = request.data.get('visibility', 'internal')
            project_id = request.data.get('project')

            # Upload to S3 (scoped by firm)
            s3_service = S3Service()
            folder_path = f"firm-{firm.id}/client-{client_id}/documents"
            upload_result = s3_service.upload_file(file_obj, folder=folder_path)

            # Create document record
            document_data = {
                'firm': firm.id,  # TIER 0: Add firm context
                'folder': folder_id,
                'client': client_id,
                'name': name,
                'description': description,
                'visibility': visibility,
                'file_type': file_obj.content_type,
                'file_size_bytes': file_obj.size,
                's3_key': upload_result['s3_key'],
                's3_bucket': upload_result['s3_bucket'],
                'current_version': 1,
                'uploaded_by': request.user.id,
            }

            if project_id:
                document_data['project'] = project_id

            serializer = self.get_serializer(data=document_data)
            serializer.is_valid(raise_exception=True)
            document = serializer.save()

            # Create initial version
            Version.objects.create(
                firm=firm,  # TIER 0: Add firm context
                document=document,
                version_number=1,
                file_type=file_obj.content_type,
                file_size_bytes=file_obj.size,
                s3_key=upload_result['s3_key'],
                s3_bucket=upload_result['s3_bucket'],
                uploaded_by=request.user,
                change_summary='Initial upload'
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Generate a presigned URL for document download.

        GET /api/documents/documents/{id}/download/

        TIER 0: get_object() automatically verifies firm access.
        """
        try:
            document = self.get_object()
            if document.is_purged:
                return Response(
                    {'error': 'Document content has been purged.'},
                    status=status.HTTP_410_GONE
                )
            s3_service = S3Service()
            presigned_url = s3_service.generate_presigned_url(document.s3_key, expiration=3600)

            return Response({
                'download_url': presigned_url,
                'expires_in': 3600
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsFirmOwner])
    def purge(self, request, pk=None):
        """
        Purge document content while preserving metadata.

        Requires firm owner approval, confirmation, and reason.
        """
        document = self.get_object()
        reason = (request.data.get('reason') or '').strip()
        confirm = request.data.get('confirm')
        is_confirmed = str(confirm).lower() in {'true', '1', 'yes'}

        if not is_confirmed:
            return Response(
                {'error': 'Confirmation required to purge content.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reason:
            return Response(
                {'error': 'Reason is required to purge content.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if document.is_purged:
            return Response(
                {'status': 'already_purged', 'document': DocumentSerializer(document).data},
                status=status.HTTP_200_OK
            )

        document.purge(reason=reason, actor=request.user)

        create_audit_event(
            firm=request.firm,
            category=AuditEvent.CATEGORY_PURGE,
            action='document.purge',
            actor=request.user,
            actor_ip=request.META.get('REMOTE_ADDR'),
            actor_user_agent=request.META.get('HTTP_USER_AGENT', ''),
            target_object=document,
            target_description=f"Document {document.id}",
            client=document.client,
            reason=reason,
            severity=AuditEvent.SEVERITY_CRITICAL,
            metadata={
                'document_id': document.id,
                'folder_id': document.folder_id,
                'version_count': document.versions.count(),
            }
        )

        return Response(
            {'status': 'purged', 'document': DocumentSerializer(document).data},
            status=status.HTTP_200_OK
        )


class VersionViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Version model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    model = Version
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document']
    search_fields = ['change_summary']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related('document', 'uploaded_by')

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Generate a presigned URL for version download.

        GET /api/documents/versions/{id}/download/

        TIER 0: get_object() automatically verifies firm access.
        """
        try:
            version = self.get_object()
            if version.is_purged:
                return Response(
                    {'error': 'Document version content has been purged.'},
                    status=status.HTTP_410_GONE
                )
            s3_service = S3Service()
            presigned_url = s3_service.generate_presigned_url(version.s3_key, expiration=3600)

            return Response({
                'download_url': presigned_url,
                'expires_in': 3600
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
