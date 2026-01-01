"""
Django Admin configuration for Projects models.
"""

from django.contrib import admin

from .models import Project, ResourceAllocation, ResourceCapacity, Task, TimeEntry


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "project_code",
        "name",
        "client",
        "status",
        "billing_type",
        "project_manager",
        "start_date",
        "end_date",
    ]
    list_filter = ["status", "billing_type", "created_at"]
    search_fields = ["project_code", "name", "client__company_name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("project_code", "name", "description", "client", "contract", "project_manager", "status")},
        ),
        ("Financial", {"fields": ("billing_type", "budget", "hourly_rate")}),
        ("Timeline", {"fields": ("start_date", "end_date", "actual_completion_date")}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "project", "status", "priority", "assigned_to", "due_date", "estimated_hours"]
    list_filter = ["status", "priority", "project", "created_at"]
    search_fields = ["title", "description", "project__name"]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    fieldsets = (
        ("Task Information", {"fields": ("project", "title", "description", "status", "priority", "assigned_to")}),
        ("Kanban", {"fields": ("position",)}),
        ("Timeline", {"fields": ("estimated_hours", "due_date", "completed_at")}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "user",
        "project",
        "task",
        "hours",
        "is_billable",
        "hourly_rate",
        "billed_amount",
        "invoiced",
    ]
    list_filter = ["is_billable", "invoiced", "date", "project"]
    search_fields = ["user__username", "project__name", "description"]
    readonly_fields = ["billed_amount", "created_at", "updated_at"]
    fieldsets = (
        ("Time Information", {"fields": ("date", "user", "project", "task", "hours", "description")}),
        ("Billing", {"fields": ("is_billable", "hourly_rate", "billed_amount")}),
        ("Invoicing", {"fields": ("invoiced", "invoice")}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(ResourceAllocation)
class ResourceAllocationAdmin(admin.ModelAdmin):
    list_display = [
        "resource",
        "project",
        "allocation_percentage",
        "role",
        "start_date",
        "end_date",
        "status",
        "is_billable",
    ]
    list_filter = ["status", "allocation_type", "is_billable", "start_date"]
    search_fields = ["resource__username", "resource__first_name", "resource__last_name", "project__name", "role"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["project", "resource", "created_by"]
    
    fieldsets = (
        ("Allocation", {
            "fields": ("project", "resource", "allocation_type", "allocation_percentage", "role")
        }),
        ("Timeline", {
            "fields": ("start_date", "end_date", "status")
        }),
        ("Financial", {
            "fields": ("hourly_rate", "is_billable")
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(ResourceCapacity)
class ResourceCapacityAdmin(admin.ModelAdmin):
    list_display = [
        "resource",
        "date",
        "available_hours",
        "unavailable_hours",
        "net_available_hours",
        "unavailability_type",
    ]
    list_filter = ["date", "unavailability_type", "firm"]
    search_fields = ["resource__username", "resource__first_name", "resource__last_name"]
    readonly_fields = ["created_at", "updated_at", "net_available_hours"]
    raw_id_fields = ["resource", "firm"]
    
    fieldsets = (
        ("Resource & Date", {
            "fields": ("firm", "resource", "date")
        }),
        ("Capacity", {
            "fields": ("available_hours", "unavailable_hours", "net_available_hours", "unavailability_type")
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
