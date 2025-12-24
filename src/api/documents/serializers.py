"""
DRF Serializers for Documents module.
"""
from rest_framework import serializers
from modules.documents.models import (
    Folder,
    Document,
    DocumentContent,
    Version,
    VersionContent,
)


class FolderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = Folder
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    s3_key = serializers.SerializerMethodField()
    s3_bucket = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_s3_key(self, obj):
        try:
            return obj.content.s3_key
        except (AttributeError, DocumentContent.DoesNotExist):
            return None

    def get_s3_bucket(self, obj):
        try:
            return obj.content.s3_bucket
        except (AttributeError, DocumentContent.DoesNotExist):
            return None

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            fields.pop('s3_key', None)
            fields.pop('s3_bucket', None)
            fields.pop('description', None)
        return fields


class VersionSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source='document.name', read_only=True)
    s3_key = serializers.SerializerMethodField()
    s3_bucket = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = '__all__'
        read_only_fields = ['created_at']

    def get_s3_key(self, obj):
        try:
            return obj.content.s3_key
        except (AttributeError, VersionContent.DoesNotExist):
            return None

    def get_s3_bucket(self, obj):
        try:
            return obj.content.s3_bucket
        except (AttributeError, VersionContent.DoesNotExist):
            return None

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and getattr(request, 'platform_role', None) == 'operator':
            fields.pop('s3_key', None)
            fields.pop('s3_bucket', None)
            fields.pop('change_summary', None)
        return fields
