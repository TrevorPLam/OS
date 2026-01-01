"""
DRF ViewSets for Documents module with S3 upload functionality.

TIER 0: All ViewSets use FirmScopedMixin for automatic tenant isolation.
TIER 2: All ViewSets have explicit permission classes.
TIER 2.5: Portal users are explicitly denied access to firm admin endpoints.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.filters import BoundedSearchFilter
from config.query_guards import QueryTimeoutMixin
from modules.clients.permissions import DenyPortalAccess
from modules.documents.models import (
    Document,
    ExternalShare,
    Folder,
    ShareAccess,
    SharePermission,
    Version,
)
from modules.documents.services import S3Service
from modules.firm.utils import FirmScopedMixin, get_request_firm

from .serializers import (
    DocumentSerializer,
    ExternalShareSerializer,
    FolderSerializer,
    ShareAccessSerializer,
    SharePermissionSerializer,
    VersionSerializer,
)


class FolderViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Folder model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Folder
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["client", "project", "parent", "visibility"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("client", "project", "parent", "created_by")


class DocumentViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Document model with S3 upload functionality.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Document
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["client", "folder", "project", "visibility", "file_type"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("folder", "client", "project", "uploaded_by")

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload a new document to S3.

        POST /api/documents/documents/upload/

        TIER 0: Automatically includes firm context from request.
        """
        try:
            file_obj = request.FILES.get("file")
            if not file_obj:
                return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

            # TIER 0: Get firm from request context
            firm = get_request_firm(request)

            # Get form data
            folder_id = request.data.get("folder")
            client_id = request.data.get("client")
            name = request.data.get("name", file_obj.name)
            description = request.data.get("description", "")
            visibility = request.data.get("visibility", "internal")
            project_id = request.data.get("project")

            # Upload to S3 (scoped by firm)
            s3_service = S3Service()
            folder_path = f"firm-{firm.id}/client-{client_id}/documents"
            upload_result = s3_service.upload_file(file_obj, folder=folder_path)

            # Create document record
            document_data = {
                "firm": firm.id,  # TIER 0: Add firm context
                "folder": folder_id,
                "client": client_id,
                "name": name,
                "description": description,
                "visibility": visibility,
                "file_type": file_obj.content_type,
                "file_size_bytes": file_obj.size,
                "s3_key": upload_result["s3_key"],
                "s3_bucket": upload_result["s3_bucket"],
                "current_version": 1,
                "uploaded_by": request.user.id,
            }

            if project_id:
                document_data["project"] = project_id

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
                s3_key=upload_result["s3_key"],
                s3_bucket=upload_result["s3_bucket"],
                uploaded_by=request.user,
                change_summary="Initial upload",
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Generate a presigned URL for document download.

        GET /api/documents/documents/{id}/download/

        TIER 0: get_object() automatically verifies firm access.
        """
        try:
            document = self.get_object()
            s3_service = S3Service()
            presigned_url = s3_service.generate_presigned_url(
                document.decrypted_s3_key(),
                bucket=document.decrypted_s3_bucket(),
                expiration=3600,
            )

            return Response({"download_url": presigned_url, "expires_in": 3600})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=["post"])
    def submit_for_review(self, request, pk=None):
        """
        Submit document for review (draft → review).
        
        POST /api/documents/documents/{id}/submit_for_review/
        
        Workflow action: transitions document from draft to review status.
        """
        try:
            document = self.get_object()
            document.submit_for_review(request.user)
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """
        Approve document (review → approved).
        
        POST /api/documents/documents/{id}/approve/
        Body: { "notes": "Optional review notes" }
        
        Workflow action: approves document under review.
        """
        try:
            document = self.get_object()
            notes = request.data.get("notes", "")
            document.approve(request.user, notes=notes)
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """
        Reject document and return to draft (review → draft).
        
        POST /api/documents/documents/{id}/reject/
        Body: { "notes": "Required rejection notes" }
        
        Workflow action: rejects document under review with notes.
        """
        try:
            document = self.get_object()
            notes = request.data.get("notes", "")
            if not notes:
                return Response(
                    {"error": "Rejection notes are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            document.reject(request.user, notes=notes)
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """
        Publish document (approved → published).
        
        POST /api/documents/documents/{id}/publish/
        
        Workflow action: publishes approved document.
        """
        try:
            document = self.get_object()
            document.publish(request.user)
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"])
    def deprecate(self, request, pk=None):
        """
        Deprecate document (published → deprecated).
        
        POST /api/documents/documents/{id}/deprecate/
        Body: { "reason": "Required deprecation reason" }
        
        Workflow action: deprecates published document with reason.
        """
        try:
            document = self.get_object()
            reason = request.data.get("reason", "")
            if not reason:
                return Response(
                    {"error": "Deprecation reason is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            document.deprecate(request.user, reason=reason)
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """
        Archive document (any status → archived).
        
        POST /api/documents/documents/{id}/archive/
        
        Workflow action: archives document from any status.
        """
        try:
            document = self.get_object()
            document.archive()
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VersionViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for Version model.

    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """

    model = Version
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]  # TIER 2.5: Deny portal access
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["document"]
    search_fields = ["change_summary"]
    ordering_fields = ["version_number", "created_at"]
    ordering = ["-version_number"]

    def get_queryset(self):
        """Override to add select_related for performance."""
        base_queryset = super().get_queryset()
        return base_queryset.select_related("document", "uploaded_by")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Generate a presigned URL for version download.

        GET /api/documents/versions/{id}/download/

        TIER 0: get_object() automatically verifies firm access.
        """
        try:
            version = self.get_object()
            s3_service = S3Service()
            presigned_url = s3_service.generate_presigned_url(
                version.decrypted_s3_key(),
                bucket=version.decrypted_s3_bucket(),
                expiration=3600,
            )

            return Response({"download_url": presigned_url, "expires_in": 3600})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExternalShareViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for ExternalShare model (Task 3.10).
    
    Provides CRUD operations for creating and managing external document shares.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    TIER 2: Requires authentication and denies portal access.
    """
    
    model = ExternalShare
    serializer_class = ExternalShareSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, BoundedSearchFilter, filters.OrderingFilter]
    filterset_fields = ["document", "access_type", "revoked", "created_by"]
    search_fields = ["document__name", "share_token"]
    ordering_fields = ["created_at", "expires_at", "download_count"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        from modules.documents.models import ExternalShare
        base_queryset = super().get_queryset()
        return base_queryset.select_related(
            "document",
            "document__folder",
            "document__client",
            "created_by",
            "revoked_by"
        )
    
    def perform_create(self, serializer):
        """Set firm and created_by on creation."""
        firm = get_request_firm(self.request)
        serializer.save(
            firm=firm,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """
        Revoke a share.
        
        POST /api/documents/external-shares/{id}/revoke/
        Body: { "reason": "Optional revocation reason" }
        
        Immediately revokes the share and prevents further access.
        """
        try:
            share = self.get_object()
            reason = request.data.get("reason", "")
            share.revoke(user=request.user, reason=reason)
            serializer = self.get_serializer(share)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["get"])
    def statistics(self, request, pk=None):
        """
        Get access statistics for a share.
        
        GET /api/documents/external-shares/{id}/statistics/
        
        Returns access counts, success/failure rates, and recent activity.
        """
        try:
            share = self.get_object()
            from modules.documents.models import ShareAccess
            
            # Get all access logs for this share
            access_logs = ShareAccess.objects.filter(
                firm=share.firm,
                external_share=share
            )
            
            # Calculate statistics
            total_accesses = access_logs.count()
            successful_accesses = access_logs.filter(success=True).count()
            failed_accesses = access_logs.filter(success=False).count()
            
            # Group by action
            action_counts = {}
            for action, _ in ShareAccess.ACTION_CHOICES:
                count = access_logs.filter(action=action).count()
                if count > 0:
                    action_counts[action] = count
            
            # Recent activity (last 10)
            recent_activity = ShareAccessSerializer(
                access_logs[:10],
                many=True,
                context={"request": request}
            ).data
            
            return Response({
                "share_id": share.id,
                "share_token": str(share.share_token),
                "document_name": share.document.name,
                "statistics": {
                    "total_accesses": total_accesses,
                    "successful_accesses": successful_accesses,
                    "failed_accesses": failed_accesses,
                    "download_count": share.download_count,
                    "max_downloads": share.max_downloads,
                    "action_counts": action_counts,
                },
                "status": {
                    "is_active": share.is_active,
                    "is_expired": share.is_expired,
                    "is_revoked": share.revoked,
                    "is_download_limit_reached": share.is_download_limit_reached,
                },
                "recent_activity": recent_activity,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SharePermissionViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ModelViewSet):
    """
    ViewSet for SharePermission model (Task 3.10).
    
    Manages detailed permissions for external shares.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    
    model = SharePermission
    serializer_class = SharePermissionSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["external_share", "allow_print", "allow_copy", "apply_watermark"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        from modules.documents.models import SharePermission
        base_queryset = super().get_queryset()
        return base_queryset.select_related(
            "external_share",
            "external_share__document"
        )
    
    def perform_create(self, serializer):
        """Set firm on creation."""
        firm = get_request_firm(self.request)
        serializer.save(firm=firm)


class ShareAccessViewSet(QueryTimeoutMixin, FirmScopedMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ShareAccess model (Task 3.10).
    
    Provides read-only access to share access logs for audit purposes.
    
    TIER 0: Automatically scoped to request.firm via FirmScopedMixin.
    """
    
    model = ShareAccess
    serializer_class = ShareAccessSerializer
    permission_classes = [IsAuthenticated, DenyPortalAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["external_share", "action", "success", "ip_address"]
    ordering_fields = ["accessed_at"]
    ordering = ["-accessed_at"]
    
    def get_queryset(self):
        """Override to add select_related for performance."""
        from modules.documents.models import ShareAccess
        base_queryset = super().get_queryset()
        return base_queryset.select_related(
            "external_share",
            "external_share__document"
        )
