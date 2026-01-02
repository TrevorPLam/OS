"""
Public API views for Documents module (no authentication required).

These views handle public access to upload-only file requests and share links.
"""

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from modules.core.notifications import EmailNotification
from modules.documents.models import (
    Document,
    ExternalShare,
    FileRequest,
    ShareAccess,
    Version,
)
from modules.documents.services import S3Service


class PublicFileRequestViewSet(viewsets.ViewSet):
    """
    Public ViewSet for file upload requests (FILE-1).

    Handles anonymous file uploads via upload-only share links.
    No authentication required - access controlled by share token.
    """

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def retrieve(self, request, pk=None):
        """
        Get file request details by share token.

        GET /api/public/file-requests/{token}/

        Returns request details and upload instructions.
        """
        try:
            # Get external share by token
            share = ExternalShare.objects.select_related(
                'file_request',
                'file_request__destination_folder',
                'file_request__client'
            ).get(share_token=pk, access_type='upload')

            # Check if share/request is active
            if share.revoked:
                return Response(
                    {"error": "This upload link has been revoked."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if share.is_expired:
                return Response(
                    {"error": "This upload link has expired."},
                    status=status.HTTP_410_GONE
                )

            # Get associated file request
            try:
                file_request = share.file_request
            except FileRequest.DoesNotExist:
                return Response(
                    {"error": "File request not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if file_request.is_expired:
                return Response(
                    {"error": "This file request has expired."},
                    status=status.HTTP_410_GONE
                )

            if file_request.is_file_limit_reached:
                return Response(
                    {"error": "File upload limit has been reached."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Log access
            ShareAccess.log_access(
                firm_id=share.firm_id,
                external_share=share,
                action="view",
                success=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )

            # Return request details
            return Response({
                "title": file_request.title,
                "description": file_request.description,
                "template_type": file_request.template_type,
                "recipient_name": file_request.recipient_name,
                "max_files": file_request.max_files,
                "uploaded_file_count": file_request.uploaded_file_count,
                "allowed_file_types": file_request.allowed_file_types,
                "required_file_names": file_request.required_file_names if file_request.require_specific_files else [],
                "expires_at": file_request.expires_at,
                "status": file_request.status,
            }, status=status.HTTP_200_OK)

        except ExternalShare.DoesNotExist:
            return Response(
                {"error": "Invalid upload link."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None):
        """
        Upload file(s) to a file request.

        POST /api/public/file-requests/{token}/upload/

        Accepts file uploads and stores them in the destination folder.
        """
        try:
            # Get external share by token
            share = ExternalShare.objects.select_related(
                'file_request',
                'file_request__destination_folder',
                'file_request__client'
            ).get(share_token=pk, access_type='upload')

            # Verify password if required
            if share.require_password:
                password = request.data.get('password', '')
                if not share.verify_password(password):
                    ShareAccess.log_access(
                        firm_id=share.firm_id,
                        external_share=share,
                        action="failed_password",
                        success=False,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    )
                    return Response(
                        {"error": "Invalid password."},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

            # Check if share/request is active
            if share.revoked:
                ShareAccess.log_access(
                    firm_id=share.firm_id,
                    external_share=share,
                    action="failed_revoked",
                    success=False,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
                return Response(
                    {"error": "This upload link has been revoked."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if share.is_expired:
                ShareAccess.log_access(
                    firm_id=share.firm_id,
                    external_share=share,
                    action="failed_expired",
                    success=False,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
                return Response(
                    {"error": "This upload link has expired."},
                    status=status.HTTP_410_GONE
                )

            # Get file request
            try:
                file_request = share.file_request
            except FileRequest.DoesNotExist:
                return Response(
                    {"error": "File request not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if file_request.is_expired:
                return Response(
                    {"error": "This file request has expired."},
                    status=status.HTTP_410_GONE
                )

            if file_request.is_file_limit_reached:
                return Response(
                    {"error": "File upload limit has been reached."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get uploaded file
            file_obj = request.FILES.get("file")
            if not file_obj:
                return Response(
                    {"error": "No file provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file type if restrictions exist
            if file_request.allowed_file_types:
                if file_obj.content_type not in file_request.allowed_file_types:
                    return Response(
                        {"error": f"File type {file_obj.content_type} is not allowed."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Upload to S3
            s3_service = S3Service()
            folder_path = f"firm-{share.firm_id}/client-{file_request.client_id if file_request.client_id else 'external'}/file-requests/{file_request.id}"
            upload_result = s3_service.upload_file(file_obj, folder=folder_path)

            # Create document record
            document = Document.objects.create(
                firm_id=share.firm_id,
                folder=file_request.destination_folder,
                client_id=file_request.client_id,
                name=file_obj.name,
                description=f"Uploaded via file request: {file_request.title}",
                visibility="internal",
                file_type=file_obj.content_type,
                file_size_bytes=file_obj.size,
                s3_key=upload_result["s3_key"],
                s3_bucket=upload_result["s3_bucket"],
                current_version=1,
                uploaded_by=None,  # Anonymous upload
            )

            # Create initial version
            Version.objects.create(
                firm_id=share.firm_id,
                document=document,
                version_number=1,
                file_type=file_obj.content_type,
                file_size_bytes=file_obj.size,
                s3_key=upload_result["s3_key"],
                s3_bucket=upload_result["s3_bucket"],
                uploaded_by=None,  # Anonymous upload
                change_summary="Initial upload via file request",
            )

            # Update file request
            file_request.increment_upload_count()
            file_request.mark_as_uploaded()

            # Log successful upload
            ShareAccess.log_access(
                firm_id=share.firm_id,
                external_share=share,
                action="download",  # Using "download" for upload tracking
                success=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    "file_name": file_obj.name,
                    "file_size": file_obj.size,
                    "file_type": file_obj.content_type,
                    "document_id": document.id,
                }
            )

            # Send notification if enabled
            if file_request.notify_on_upload:
                self._send_upload_notification(file_request, document, file_obj)

            return Response({
                "message": "File uploaded successfully",
                "file_name": file_obj.name,
                "uploaded_count": file_request.uploaded_file_count,
                "max_files": file_request.max_files,
            }, status=status.HTTP_201_CREATED)

        except ExternalShare.DoesNotExist:
            return Response(
                {"error": "Invalid upload link."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log failed upload
            try:
                ShareAccess.log_access(
                    firm_id=share.firm_id if 'share' in locals() else None,
                    external_share=share if 'share' in locals() else None,
                    action="failed_limit",
                    success=False,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    metadata={"error": str(e)}
                )
            except:
                pass

            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _send_upload_notification(self, file_request, document, file_obj):
        """Send email notification about file upload (FILE-4)."""
        try:
            # Collect notification recipients
            recipients = []

            # Add created_by user
            if file_request.created_by and file_request.created_by.email:
                recipients.append(file_request.created_by.email)

            # Add additional notification emails
            if file_request.notification_emails:
                recipients.extend(file_request.notification_emails)

            if not recipients:
                return

            # Send notification
            email_service = EmailNotification()
            subject = f"File Uploaded: {file_request.title}"
            message = f"""
            A new file has been uploaded to your file request.

            Request: {file_request.title}
            File Name: {file_obj.name}
            File Size: {file_obj.size} bytes
            Uploaded By: {file_request.recipient_name or file_request.recipient_email}

            Total Files Uploaded: {file_request.uploaded_file_count}

            Please log in to review the uploaded file.
            """

            for recipient in recipients:
                email_service.send(
                    to_email=recipient,
                    subject=subject,
                    body=message.strip(),
                )
        except Exception as e:
            # Don't fail the upload if notification fails
            print(f"Failed to send upload notification: {e}")
