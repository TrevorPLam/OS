"""
DRF Serializers for Documents module.
"""
from rest_framework import serializers
from modules.documents.models import Folder, Document, Version


class FolderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = Folder
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    client_name = serializers.CharField(source='client.company_name', read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class VersionSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source='document.name', read_only=True)

    class Meta:
        model = Version
        fields = '__all__'
        read_only_fields = ['created_at']
