"""
Admin interface for snippets module.

Provides Django admin configuration for snippet management.
"""

from django.contrib import admin
from modules.snippets.models import (
    Snippet,
    SnippetUsageLog,
    SnippetFolder,
)


@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    """Admin for Snippet model."""

    list_display = [
        'shortcut',
        'name',
        'firm',
        'created_by',
        'is_shared',
        'context',
        'usage_count',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'firm',
        'is_shared',
        'is_active',
        'context',
        'created_at',
    ]
    search_fields = [
        'shortcut',
        'name',
        'content',
        'created_by__username',
        'created_by__email',
    ]
    readonly_fields = [
        'usage_count',
        'last_used_at',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['created_by', 'folder']

    fieldsets = (
        (
            'Basic Information',
            {
                'fields': (
                    'firm',
                    'shortcut',
                    'name',
                    'content',
                )
            }
        ),
        (
            'Sharing & Visibility',
            {
                'fields': (
                    'created_by',
                    'is_shared',
                    'shared_with_roles',
                    'folder',
                )
            }
        ),
        (
            'Context & Usage',
            {
                'fields': (
                    'context',
                    'is_active',
                    'usage_count',
                    'last_used_at',
                )
            }
        ),
        (
            'Metadata',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                ),
                'classes': ('collapse',)
            }
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('firm', 'created_by', 'folder')


@admin.register(SnippetUsageLog)
class SnippetUsageLogAdmin(admin.ModelAdmin):
    """Admin for SnippetUsageLog model."""

    list_display = [
        'snippet',
        'used_by',
        'context',
        'context_object_type',
        'rendered_length',
        'used_at',
    ]
    list_filter = [
        'context',
        'context_object_type',
        'used_at',
    ]
    search_fields = [
        'snippet__shortcut',
        'snippet__name',
        'used_by__username',
        'used_by__email',
        'context_object_id',
    ]
    readonly_fields = [
        'snippet',
        'used_by',
        'context',
        'context_object_type',
        'context_object_id',
        'variables_used',
        'rendered_length',
        'used_at',
    ]
    raw_id_fields = ['snippet', 'used_by']

    fieldsets = (
        (
            'Usage Information',
            {
                'fields': (
                    'snippet',
                    'used_by',
                    'used_at',
                )
            }
        ),
        (
            'Context',
            {
                'fields': (
                    'context',
                    'context_object_type',
                    'context_object_id',
                )
            }
        ),
        (
            'Details',
            {
                'fields': (
                    'variables_used',
                    'rendered_length',
                )
            }
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('snippet', 'used_by')

    def has_add_permission(self, request):
        """Usage logs are created automatically, not manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Usage logs are read-only."""
        return False


@admin.register(SnippetFolder)
class SnippetFolderAdmin(admin.ModelAdmin):
    """Admin for SnippetFolder model."""

    list_display = [
        'name',
        'firm',
        'created_by',
        'is_shared',
        'get_snippet_count',
        'created_at',
    ]
    list_filter = [
        'firm',
        'is_shared',
        'created_at',
    ]
    search_fields = [
        'name',
        'description',
        'created_by__username',
        'created_by__email',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'get_snippet_count',
    ]
    raw_id_fields = ['created_by']

    fieldsets = (
        (
            'Basic Information',
            {
                'fields': (
                    'firm',
                    'name',
                    'description',
                )
            }
        ),
        (
            'Sharing',
            {
                'fields': (
                    'created_by',
                    'is_shared',
                )
            }
        ),
        (
            'Metadata',
            {
                'fields': (
                    'get_snippet_count',
                    'created_at',
                    'updated_at',
                ),
                'classes': ('collapse',)
            }
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('firm', 'created_by')

    def get_snippet_count(self, obj):
        """Get count of snippets in folder."""
        return obj.snippet_count()
    get_snippet_count.short_description = 'Snippets'
