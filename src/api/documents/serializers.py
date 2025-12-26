"""
DRF Serializers for Documents module.
"""

from rest_framework import serializers

from modules.documents.models import Document, Folder, Version
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
