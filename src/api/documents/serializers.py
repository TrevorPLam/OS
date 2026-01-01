"""
DRF Serializers for Documents module.
"""

from rest_framework import serializers

from modules.documents.models import (
    Document,
    ExternalShare,
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
