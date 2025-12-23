"""
DRF ViewSets for Documents module with S3 upload functionality.
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from modules.documents.models import Folder, Document, Version
from modules.documents.services import S3Service
from .serializers import FolderSerializer, DocumentSerializer, VersionSerializer


class FolderViewSet(viewsets.ModelViewSet):
    """ViewSet for Folder model."""
    queryset = Folder.objects.select_related('client', 'project', 'parent', 'created_by')
    serializer_class = FolderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'project', 'parent', 'visibility']
    search_fields = ['name', 'client__company_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document model with S3 upload functionality.
    """
    queryset = Document.objects.select_related('folder', 'client', 'project', 'uploaded_by')
    serializer_class = DocumentSerializer
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

            # Upload to S3
            s3_service = S3Service()
            folder_path = f"client-{client_id}/documents"
            upload_result = s3_service.upload_file(file_obj, folder=folder_path)

            # Create document record
            document_data = {
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
        """
        try:
            document = self.get_object()
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


class VersionViewSet(viewsets.ModelViewSet):
    """ViewSet for Version model."""
    queryset = Version.objects.select_related('document', 'uploaded_by')
    serializer_class = VersionSerializer
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
