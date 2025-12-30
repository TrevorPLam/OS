"""
Serializers for snippets module.

Provides DRF serializers for snippet models.
"""

from rest_framework import serializers
from modules.snippets.models import (
    Snippet,
    SnippetUsageLog,
    SnippetFolder,
)


class SnippetFolderSerializer(serializers.ModelSerializer):
    """Serializer for SnippetFolder."""

    snippet_count = serializers.IntegerField(read_only=True, source='snippet_count')
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = SnippetFolder
        fields = [
            'id',
            'firm',
            'name',
            'description',
            'created_by',
            'created_by_name',
            'is_shared',
            'snippet_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'snippet_count',
            'created_by_name',
        ]


class SnippetSerializer(serializers.ModelSerializer):
    """Serializer for Snippet."""

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    available_variables = serializers.SerializerMethodField()
    extracted_variables = serializers.SerializerMethodField()

    class Meta:
        model = Snippet
        fields = [
            'id',
            'firm',
            'created_by',
            'created_by_name',
            'is_shared',
            'shared_with_roles',
            'shortcut',
            'name',
            'content',
            'context',
            'usage_count',
            'last_used_at',
            'is_active',
            'folder',
            'folder_name',
            'available_variables',
            'extracted_variables',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'usage_count',
            'last_used_at',
            'created_at',
            'updated_at',
            'created_by_name',
            'folder_name',
            'available_variables',
            'extracted_variables',
        ]

    def get_available_variables(self, obj):
        """Get list of available variables for this snippet."""
        return obj.get_available_variables()

    def get_extracted_variables(self, obj):
        """Get list of variables extracted from snippet content."""
        return obj.extract_variables()


class SnippetUsageLogSerializer(serializers.ModelSerializer):
    """Serializer for SnippetUsageLog."""

    snippet_shortcut = serializers.CharField(source='snippet.shortcut', read_only=True)
    snippet_name = serializers.CharField(source='snippet.name', read_only=True)
    used_by_name = serializers.CharField(source='used_by.get_full_name', read_only=True)

    class Meta:
        model = SnippetUsageLog
        fields = [
            'id',
            'snippet',
            'snippet_shortcut',
            'snippet_name',
            'used_by',
            'used_by_name',
            'context',
            'context_object_type',
            'context_object_id',
            'variables_used',
            'rendered_length',
            'used_at',
        ]
        read_only_fields = [
            'id',
            'used_at',
            'snippet_shortcut',
            'snippet_name',
            'used_by_name',
        ]


class SnippetRenderSerializer(serializers.Serializer):
    """Serializer for rendering a snippet with variables."""

    context_data = serializers.JSONField(
        help_text='Dictionary of variable values to replace in snippet'
    )

    def validate_context_data(self, value):
        """Validate context_data is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('context_data must be a dictionary')
        return value


class SnippetUseSerializer(serializers.Serializer):
    """Serializer for logging snippet usage."""

    context = serializers.CharField(
        max_length=20,
        required=False,
        help_text='Where the snippet was used (email, ticket, message, note)'
    )
    context_object_type = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text='Type of object (e.g., "ticket", "email")'
    )
    context_object_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='ID of the object where snippet was used'
    )
    variables_used = serializers.JSONField(
        required=False,
        default=dict,
        help_text='Variables that were replaced in this usage'
    )
