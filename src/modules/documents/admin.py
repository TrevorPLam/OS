"""
Django Admin configuration for Documents models.
"""
from django.contrib import admin
from .models import Folder, Document, Version


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'client',
        'project',
        'parent',
        'visibility',
        'created_at'
    ]
    list_filter = ['visibility', 'created_at', 'client']
    search_fields = ['name', 'client__company_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Folder Information', {
            'fields': ('name', 'description', 'client', 'project', 'parent', 'visibility')
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'folder',
        'client',
        'file_type',
        'file_size_bytes',
        'current_version',
        'visibility',
        'created_at'
    ]
    list_filter = ['visibility', 'file_type', 'created_at']
    search_fields = ['name', 'client__company_name', 's3_key']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Document Information', {
            'fields': ('name', 'description', 'folder', 'client', 'project', 'visibility')
        }),
        ('File Details', {
            'fields': ('file_type', 'file_size_bytes', 'current_version')
        }),
        ('S3 Storage', {
            'fields': ('s3_bucket', 's3_key')
        }),
        ('Audit', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = [
        'document',
        'version_number',
        'file_type',
        'file_size_bytes',
        'uploaded_by',
        'created_at'
    ]
    list_filter = ['created_at', 'file_type']
    search_fields = ['document__name', 'change_summary']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Version Information', {
            'fields': ('document', 'version_number', 'change_summary')
        }),
        ('File Details', {
            'fields': ('file_type', 'file_size_bytes')
        }),
        ('S3 Storage', {
            'fields': ('s3_bucket', 's3_key')
        }),
        ('Audit', {
            'fields': ('uploaded_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
