"""
Django Admin configuration for Projects models.
"""

from django.contrib import admin

from .models import (
    Project,
    ProjectTimeline,
    ResourceAllocation,
    ResourceCapacity,
    Task,
    TaskDependency,
    TaskSchedule,
    TimeEntry,
)


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


@admin.register(ProjectTimeline)
class ProjectTimelineAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "planned_start_date",
        "planned_end_date",
        "completion_percentage_display",
        "critical_path_duration_days",
        "milestone_count",
        "is_on_critical_path_risk",
    ]
    list_filter = ["planned_start_date", "planned_end_date", "created_at"]
    search_fields = ["project__project_code", "project__name"]
    readonly_fields = ["created_at", "updated_at", "completion_percentage_display", "last_calculated_at"]
    raw_id_fields = ["project"]
    
    fieldsets = (
        ("Project", {
            "fields": ("project",)
        }),
        ("Timeline Dates", {
            "fields": ("planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date")
        }),
        ("Critical Path", {
            "fields": ("critical_path_task_ids", "critical_path_duration_days")
        }),
        ("Statistics", {
            "fields": ("total_tasks", "completed_tasks", "milestone_count", "completion_percentage_display")
        }),
        ("Calculation", {
            "fields": ("last_calculated_at", "calculation_metadata"),
            "classes": ("collapse",)
        }),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    
    def completion_percentage_display(self, obj):
        """Display completion percentage."""
        return f"{obj.completion_percentage:.1f}%"
    completion_percentage_display.short_description = "Completion %"


@admin.register(TaskSchedule)
class TaskScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "task",
        "planned_start_date",
        "planned_end_date",
        "planned_duration_days",
        "completion_percentage",
        "is_on_critical_path",
        "is_milestone",
        "is_behind_schedule",
    ]
    list_filter = ["is_on_critical_path", "is_milestone", "constraint_type", "planned_start_date"]
    search_fields = ["task__title", "task__project__name"]
    readonly_fields = ["created_at", "updated_at", "is_behind_schedule", "days_remaining"]
    raw_id_fields = ["task"]
    
    fieldsets = (
        ("Task", {
            "fields": ("task",)
        }),
        ("Planned Schedule", {
            "fields": ("planned_start_date", "planned_end_date", "planned_duration_days")
        }),
        ("Actual Schedule", {
            "fields": ("actual_start_date", "actual_end_date", "actual_duration_days")
        }),
        ("Constraints", {
            "fields": ("constraint_type", "constraint_date")
        }),
        ("Critical Path Analysis", {
            "fields": (
                "is_on_critical_path",
                "total_slack_days",
                "free_slack_days",
                "early_start_date",
                "early_finish_date",
                "late_start_date",
                "late_finish_date",
            ),
            "classes": ("collapse",)
        }),
        ("Progress", {
            "fields": ("completion_percentage", "is_behind_schedule", "days_remaining")
        }),
        ("Milestone", {
            "fields": ("is_milestone", "milestone_date"),
            "classes": ("collapse",)
        }),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = [
        "predecessor",
        "successor",
        "dependency_type",
        "lag_days",
        "same_project_check",
    ]
    list_filter = ["dependency_type", "created_at"]
    search_fields = [
        "predecessor__title",
        "successor__title",
        "predecessor__project__name",
        "successor__project__name",
    ]
    readonly_fields = ["created_at", "updated_at", "same_project_check"]
    raw_id_fields = ["predecessor", "successor"]
    
    fieldsets = (
        ("Dependency", {
            "fields": ("predecessor", "successor", "dependency_type", "lag_days")
        }),
        ("Validation", {
            "fields": ("same_project_check",),
            "classes": ("collapse",)
        }),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    
    def same_project_check(self, obj):
        """Display if tasks are in the same project."""
        if obj.predecessor and obj.successor:
            if obj.predecessor.project == obj.successor.project:
                return f"✓ Same project: {obj.predecessor.project.project_code}"
            return "✗ Different projects (invalid)"
        return "N/A"
    same_project_check.short_description = "Project Check"
