"""
DRF ViewSets for Documents module with S3 upload functionality.
"""
from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from modules.documents.models import Folder, Document, DocumentContent, Version, VersionContent
from modules.documents.services import S3Service
from modules.firm.viewsets import FirmScopedViewSetMixin
from config.permissions import PlatformContentPermission
from .serializers import FolderSerializer, DocumentSerializer, VersionSerializer


class FolderViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Folder model."""
    queryset = Folder.objects.select_related('client', 'project', 'parent', 'created_by')
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'project', 'parent', 'visibility']
    search_fields = ['name', 'client__company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DocumentViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Document model with S3 upload functionality.
    """
    queryset = Document.objects.select_related(
        'folder',
        'client',
        'project',
        'uploaded_by',
        'content',
    )
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, PlatformContentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'folder', 'project', 'visibility', 'file_type']
    search_fields = ['name', 'client__company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload a new document to S3.

        POST /api/documents/documents/upload/
        """
        try:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get form data
            folder_id = request.data.get('folder')
            client_id = request.data.get('client')
            name = request.data.get('name', file_obj.name)
            description = request.data.get('description', '')
            visibility = request.data.get('visibility', 'internal')
            project_id = request.data.get('project')

            folder = Folder.objects.filter(id=folder_id, firm=request.firm).first()
            if not folder:
                return Response(
                    {'error': 'Folder not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            if client_id and str(folder.client_id) != str(client_id):
                return Response(
                    {'error': 'Client does not match folder'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            client_id = folder.client_id

            # Upload to S3
            s3_service = S3Service()
            folder_path = f"client-{client_id}/documents"
            upload_result = s3_service.upload_file(file_obj, folder=folder_path)

            # Create document record
            document_data = {
                'folder': folder.id,
                'firm': request.firm.id,
                'client': client_id,
                'name': name,
                'description': description,
                'visibility': visibility,
                'file_type': file_obj.content_type,
                'file_size_bytes': file_obj.size,
                'current_version': 1,
                'uploaded_by': request.user.id,
            }

            if project_id:
                document_data['project'] = project_id

            serializer = self.get_serializer(data=document_data)
            serializer.is_valid(raise_exception=True)
            document = serializer.save()
            DocumentContent.objects.create(
                document=document,
                s3_key=upload_result['s3_key'],
                s3_bucket=upload_result['s3_bucket'],
            )

            # Create initial version
            version = Version.objects.create(
                document=document,
                firm=request.firm,
                version_number=1,
                file_type=file_obj.content_type,
                file_size_bytes=file_obj.size,
                uploaded_by=request.user,
                change_summary='Initial upload'
            )
            VersionContent.objects.create(
                version=version,
                s3_key=upload_result['s3_key'],
                s3_bucket=upload_result['s3_bucket'],
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
        """
        try:
            document = self.get_object()
            s3_service = S3Service()
            try:
                content = document.content
            except DocumentContent.DoesNotExist:
                content = None
            if not content:
                return Response(
                    {'error': 'Document content not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            presigned_url = s3_service.generate_presigned_url(content.s3_key, expiration=3600)

            return Response({
                'download_url': presigned_url,
                'expires_in': 3600
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VersionViewSet(FirmScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for Version model."""
    queryset = Version.objects.select_related('document', 'uploaded_by', 'content')
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated, PlatformContentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document']
    search_fields = ['document__name', 'change_summary']
    ordering_fields = ['version_number', 'created_at']
    ordering = ['-version_number']

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Generate a presigned URL for version download.

        GET /api/documents/versions/{id}/download/
        """
        try:
            version = self.get_object()
            s3_service = S3Service()
            try:
                content = version.content
            except VersionContent.DoesNotExist:
                content = None
            if not content:
                return Response(
                    {'error': 'Document version content not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            presigned_url = s3_service.generate_presigned_url(content.s3_key, expiration=3600)

            return Response({
                'download_url': presigned_url,
                'expires_in': 3600
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
