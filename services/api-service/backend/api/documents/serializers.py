"""
DRF Serializers for Documents module.
"""

from rest_framework import serializers

from modules.documents.models import (
    Document,
    ExternalShare,
    FileRequest,
    FileRequestReminder,
    Folder,
    ShareAccess,
    SharePermission,
    Version,
)
from modules.firm.utils import has_active_break_glass_session


class FolderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = Folder
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class DocumentSerializer(serializers.ModelSerializer):
    folder_name = serializers.CharField(source="folder.name", read_only=True)
    client_name = serializers.CharField(source="client.company_name", read_only=True)

    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if self._include_content(request):
            data["s3_key"] = instance.decrypted_s3_key()
            data["s3_bucket"] = instance.decrypted_s3_bucket()
        else:
            data.pop("s3_key", None)
            data.pop("s3_bucket", None)
        return data

    def _include_content(self, request):
        if not request or not getattr(request, "user", None):
            return True

        user = request.user
        if not user.is_authenticated:
            return True

        profile = getattr(user, "platform_profile", None)
        if profile and profile.is_platform_active:
            firm = getattr(request, "firm", None)
            return has_active_break_glass_session(firm) if firm else False
        return True


class VersionSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source="document.name", read_only=True)

    class Meta:
        model = Version
        fields = "__all__"
        read_only_fields = ["created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if self._include_content(request):
            data["s3_key"] = instance.decrypted_s3_key()
            data["s3_bucket"] = instance.decrypted_s3_bucket()
        else:
            data.pop("s3_key", None)
            data.pop("s3_bucket", None)
        return data

    def _include_content(self, request):
        if not request or not getattr(request, "user", None):
            return True

        user = request.user
        if not user.is_authenticated:
            return True

        profile = getattr(user, "platform_profile", None)
        if profile and profile.is_platform_active:
            firm = getattr(request, "firm", None)
            return has_active_break_glass_session(firm) if firm else False
        return True


class ExternalShareSerializer(serializers.ModelSerializer):
    """Serializer for ExternalShare model (Task 3.10)."""
    
    document_name = serializers.CharField(source="document.name", read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_download_limit_reached = serializers.BooleanField(read_only=True)
    share_url = serializers.SerializerMethodField()
    
    # Password field for setting (write-only)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = ExternalShare
        fields = [
            "id",
            "document",
            "document_name",
            "share_token",
            "access_type",
            "require_password",
            "password",  # write-only
            "expires_at",
            "max_downloads",
            "download_count",
            "revoked",
            "revoked_at",
            "revoked_by",
            "revoke_reason",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
            "is_expired",
            "is_download_limit_reached",
            "share_url",
        ]
        read_only_fields = [
            "share_token",
            "download_count",
            "revoked_at",
            "revoked_by",
            "revoke_reason",
            "created_at",
            "updated_at",
        ]
    
    def get_share_url(self, obj):
        """Generate the full share URL."""
        if obj.share_token:
            request = self.context.get("request")
            if request:
                # Use request to build absolute URI
                return request.build_absolute_uri(f"/api/public/shares/{obj.share_token}/")
            return f"/api/public/shares/{obj.share_token}/"
        return None
    
    def create(self, validated_data):
        """Handle password setting during creation."""
        password = validated_data.pop("password", None)
        share = super().create(validated_data)
        
        if password:
            share.set_password(password)
            share.save()
        
        return share
    
    def update(self, instance, validated_data):
        """Handle password updates."""
        password = validated_data.pop("password", None)
        
        # If password is provided, update it
        if password:
            instance.set_password(password)
        # If password is empty string and require_password is False, clear it
        elif password == "" and not validated_data.get("require_password", instance.require_password):
            instance.password_hash = ""
            instance.require_password = False
        
        return super().update(instance, validated_data)
    
    def validate(self, data):
        """Validate external share data."""
        # If require_password is True, password must be provided on creation
        if data.get("require_password") and not self.instance:
            if not data.get("password"):
                raise serializers.ValidationError({
                    "password": "Password is required when password protection is enabled."
                })
        
        # Validate max_downloads
        if "max_downloads" in data and data["max_downloads"] is not None:
            if data["max_downloads"] < 0:
                raise serializers.ValidationError({
                    "max_downloads": "Max downloads must be non-negative."
                })
        
        return data


class SharePermissionSerializer(serializers.ModelSerializer):
    """Serializer for SharePermission model (Task 3.10)."""
    
    class Meta:
        model = SharePermission
        fields = [
            "id",
            "external_share",
            "allow_print",
            "allow_copy",
            "apply_watermark",
            "watermark_text",
            "watermark_settings",
            "allowed_ip_addresses",
            "notify_on_access",
            "notification_emails",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
    
    def validate(self, data):
        """Validate share permission data."""
        # If watermark is enabled, text must be provided
        if data.get("apply_watermark"):
            if not data.get("watermark_text"):
                raise serializers.ValidationError({
                    "watermark_text": "Watermark text is required when watermark is enabled."
                })
        
        return data


class ShareAccessSerializer(serializers.ModelSerializer):
    """Serializer for ShareAccess model (Task 3.10)."""
    
    document_name = serializers.CharField(
        source="external_share.document.name",
        read_only=True
    )
    
    class Meta:
        model = ShareAccess
        fields = [
            "id",
            "external_share",
            "document_name",
            "action",
            "success",
            "accessed_at",
            "ip_address",
            "user_agent",
            "referer",
            "metadata",
        ]
        read_only_fields = ["accessed_at"]


class FileRequestSerializer(serializers.ModelSerializer):
    """Serializer for FileRequest model (FILE-1)."""

    client_name = serializers.CharField(source="client.company_name", read_only=True, allow_null=True)
    destination_folder_name = serializers.CharField(source="destination_folder.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True, allow_null=True)
    share_url = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_file_limit_reached = serializers.BooleanField(read_only=True)

    # Nested external share data (read-only)
    external_share_token = serializers.UUIDField(source="external_share.share_token", read_only=True)

    class Meta:
        model = FileRequest
        fields = [
            "id",
            "firm",
            "client",
            "client_name",
            "external_share",
            "external_share_token",
            "destination_folder",
            "destination_folder_name",
            "title",
            "description",
            "template_type",
            "status",
            "recipient_email",
            "recipient_name",
            "expires_at",
            "max_files",
            "uploaded_file_count",
            "require_specific_files",
            "required_file_names",
            "allowed_file_types",
            "enable_reminders",
            "reminder_sent_count",
            "last_reminder_sent_at",
            "notify_on_upload",
            "notification_emails",
            "completed_at",
            "reviewed_by",
            "reviewed_at",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "share_url",
            "is_active",
            "is_expired",
            "is_file_limit_reached",
        ]
        read_only_fields = [
            "uploaded_file_count",
            "reminder_sent_count",
            "last_reminder_sent_at",
            "completed_at",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]

    def get_share_url(self, obj):
        """Generate the full upload URL."""
        if obj.external_share and obj.external_share.share_token:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(f"/api/public/file-requests/{obj.external_share.share_token}/")
            return f"/api/public/file-requests/{obj.external_share.share_token}/"
        return None

    def validate(self, data):
        """Validate file request data."""
        # Validate specific file requirements
        if data.get("require_specific_files"):
            if not data.get("required_file_names"):
                raise serializers.ValidationError({
                    "required_file_names": "Required file names must be specified when specific files are required."
                })

        # Validate max_files
        if "max_files" in data and data["max_files"] is not None:
            if data["max_files"] < 0:
                raise serializers.ValidationError({
                    "max_files": "Max files must be non-negative."
                })

        return data


class FileRequestReminderSerializer(serializers.ModelSerializer):
    """Serializer for FileRequestReminder model (FILE-2)."""

    file_request_title = serializers.CharField(source="file_request.title", read_only=True)

    class Meta:
        model = FileRequestReminder
        fields = [
            "id",
            "firm",
            "file_request",
            "file_request_title",
            "reminder_type",
            "days_after_creation",
            "subject",
            "message",
            "escalate_to_team",
            "escalation_emails",
            "scheduled_for",
            "sent_at",
            "status",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "sent_at",
            "status",
            "failure_reason",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        """Validate reminder data."""
        # Escalation validation
        if data.get("escalate_to_team"):
            if not data.get("escalation_emails"):
                raise serializers.ValidationError({
                    "escalation_emails": "Escalation emails must be specified when escalating to team."
                })

        # Validate days_after_creation
        if "days_after_creation" in data and data["days_after_creation"] < 0:
            raise serializers.ValidationError({
                "days_after_creation": "Days after creation must be non-negative."
            })

        return data
