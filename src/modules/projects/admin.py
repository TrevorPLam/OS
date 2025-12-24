"""
Django Admin configuration for Projects models.
"""
from django.contrib import admin
from .models import Project, Task, TimeEntry


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'project_code',
        'name',
        'client',
        'status',
        'billing_type',
        'project_manager',
        'start_date',
        'end_date'
    ]
    list_filter = ['status', 'billing_type', 'created_at']
    search_fields = ['project_code', 'name', 'client__company_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_code', 'name', 'description', 'client', 'contract', 'project_manager', 'status')
        }),
        ('Financial', {
            'fields': ('billing_type', 'budget', 'hourly_rate')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'actual_completion_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'project',
        'status',
        'priority',
        'assigned_to',
        'due_date',
        'estimated_hours'
    ]
    list_filter = ['status', 'priority', 'project', 'created_at']
    search_fields = ['title', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    fieldsets = (
        ('Task Information', {
            'fields': ('project', 'title', 'description', 'status', 'priority', 'assigned_to')
        }),
        ('Kanban', {
            'fields': ('position',)
        }),
        ('Timeline', {
            'fields': ('estimated_hours', 'due_date', 'completed_at')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'user',
        'project',
        'task',
        'hours',
        'is_billable',
        'hourly_rate',
        'billed_amount',
        'invoiced'
    ]
    list_filter = ['is_billable', 'invoiced', 'date', 'project']
    search_fields = ['user__username', 'project__name', 'description']
    readonly_fields = ['billed_amount', 'created_at', 'updated_at']
    fieldsets = (
        ('Time Information', {
            'fields': ('date', 'user', 'project', 'task', 'hours', 'description')
        }),
        ('Billing', {
            'fields': ('is_billable', 'hourly_rate', 'billed_amount')
        }),
        ('Invoicing', {
            'fields': ('invoiced', 'invoice')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
