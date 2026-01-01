"""
DRF Serializers for Projects module with enhanced validation.
"""

from django.db import models
from django.utils import timezone
from rest_framework import serializers

from modules.projects.models import Project, ResourceAllocation, ResourceCapacity, Task, TimeEntry


class ResourceAllocationSerializer(serializers.ModelSerializer):
    """Serializer for ResourceAllocation model (Task 3.2)."""
    
    resource_name = serializers.SerializerMethodField()
    project_name = serializers.CharField(source="project.name", read_only=True)
    
    class Meta:
        model = ResourceAllocation
        fields = [
            "id",
            "project",
            "project_name",
            "resource",
            "resource_name",
            "allocation_type",
            "allocation_percentage",
            "hourly_rate",
            "start_date",
            "end_date",
            "role",
            "is_billable",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_resource_name(self, obj):
        """Get resource's full name."""
        return obj.resource.get_full_name()


class ResourceCapacitySerializer(serializers.ModelSerializer):
    """Serializer for ResourceCapacity model (Task 3.2)."""
    
    resource_name = serializers.SerializerMethodField()
    net_available_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = ResourceCapacity
        fields = [
            "id",
            "firm",
            "resource",
            "resource_name",
            "date",
            "available_hours",
            "unavailable_hours",
            "net_available_hours",
            "unavailability_type",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "net_available_hours"]
    
    def get_resource_name(self, obj):
        """Get resource's full name."""
        return obj.resource.get_full_name()


class ProjectSerializer(serializers.ModelSerializer):
    """Enhanced Project serializer with validation."""

    client_name = serializers.CharField(source="client.company_name", read_only=True)
    contract_number = serializers.CharField(source="contract.contract_number", read_only=True, allow_null=True)
    total_hours_logged = serializers.SerializerMethodField()
    total_billed_amount = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "client",
            "client_name",
            "contract",
            "contract_number",
            "project_manager",
            "project_code",
            "name",
            "description",
            "status",
            "billing_type",
            "budget",
            "hourly_rate",
            "start_date",
            "end_date",
            "actual_completion_date",
            "created_at",
            "updated_at",
            "notes",
            "total_hours_logged",
            "total_billed_amount",
            # Client Acceptance fields (Medium Feature 2.8)
            "client_accepted",
            "acceptance_date",
            "accepted_by",
            "acceptance_notes",
        ]
        read_only_fields = ["created_at", "updated_at", "acceptance_date"]

    def get_total_hours_logged(self, obj):
        """Calculate total hours logged for this project."""
        total = obj.time_entries.aggregate(total=models.Sum("hours"))["total"]
        return float(total) if total else 0.0

    def get_total_billed_amount(self, obj):
        """Calculate total billed amount for this project."""
        total = obj.time_entries.filter(is_billable=True).aggregate(total=models.Sum("billed_amount"))["total"]
        return float(total) if total else 0.0

    def validate_budget(self, value):
        """Validate budget is positive."""
        if value and value <= 0:
            raise serializers.ValidationError("Budget must be greater than 0")
        return value

    def validate_hourly_rate(self, value):
        """Validate hourly rate is positive."""
        if value and value <= 0:
            raise serializers.ValidationError("Hourly rate must be greater than 0")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        start_date = attrs.get("start_date") or (self.instance.start_date if self.instance else None)
        end_date = attrs.get("end_date") or (self.instance.end_date if self.instance else None)

        # Validate date range
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date"})

        # Validate contract belongs to same client
        contract = attrs.get("contract")
        client = attrs.get("client") or (self.instance.client if self.instance else None)
        if contract and client and contract.client_id != client.id:
            raise serializers.ValidationError({"contract": "Contract must belong to the same client as the project"})

        # Validate actual_completion_date
        actual_completion_date = attrs.get("actual_completion_date")
        if actual_completion_date:
            if start_date and actual_completion_date < start_date:
                raise serializers.ValidationError(
                    {"actual_completion_date": "Completion date cannot be before start date"}
                )

        return attrs


class TaskSerializer(serializers.ModelSerializer):
    """Enhanced Task serializer with validation."""

    project_name = serializers.CharField(source="project.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.username", read_only=True, allow_null=True)
    hours_logged = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "project_name",
            "assigned_to",
            "assigned_to_name",
            "title",
            "description",
            "status",
            "priority",
            "position",
            "estimated_hours",
            "due_date",
            "completed_at",
            "created_at",
            "updated_at",
            "hours_logged",
        ]
        read_only_fields = ["created_at", "updated_at", "completed_at"]

    def get_hours_logged(self, obj):
        """Calculate total hours logged for this task."""
        total = obj.time_entries.aggregate(total=models.Sum("hours"))["total"]
        return float(total) if total else 0.0

    def validate_estimated_hours(self, value):
        """Validate estimated hours is positive."""
        if value and value <= 0:
            raise serializers.ValidationError("Estimated hours must be greater than 0")
        return value

    def validate(self, attrs):
        """Cross-field validation and auto-set completed_at."""
        # Auto-set completed_at when status changes to 'done'
        if attrs.get("status") == "done" and (not self.instance or not self.instance.completed_at):
            attrs["completed_at"] = timezone.now()

        # Clear completed_at if status changes from 'done' to something else
        if self.instance and self.instance.status == "done" and attrs.get("status") != "done":
            attrs["completed_at"] = None

        return attrs


class TimeEntrySerializer(serializers.ModelSerializer):
    """Enhanced TimeEntry serializer with validation."""

    project_name = serializers.CharField(source="project.name", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True, allow_null=True)

    class Meta:
        model = TimeEntry
        fields = [
            "id",
            "project",
            "project_name",
            "task",
            "task_title",
            "user",
            "user_name",
            "date",
            "hours",
            "description",
            "is_billable",
            "hourly_rate",
            "billed_amount",
            "invoiced",
            "invoice",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "billed_amount"]

    def validate_hours(self, value):
        """Validate hours is positive and reasonable."""
        if value <= 0:
            raise serializers.ValidationError("Hours must be greater than 0")
        if value > 24:
            raise serializers.ValidationError("Hours cannot exceed 24 hours per day")
        return value

    def validate_hourly_rate(self, value):
        """Validate hourly rate is positive."""
        if value < 0:
            raise serializers.ValidationError("Hourly rate cannot be negative")
        return value

    def validate_date(self, value):
        """Validate date is not in the future."""
        if value > timezone.now().date():
            raise serializers.ValidationError("Time entry date cannot be in the future")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        # Validate task belongs to project
        task = attrs.get("task")
        project = attrs.get("project") or (self.instance.project if self.instance else None)
        if task and project and task.project_id != project.id:
            raise serializers.ValidationError({"task": "Task must belong to the same project"})

        # Prevent modification of invoiced time entries
        if self.instance and self.instance.invoiced:
            if any(k in attrs for k in ["hours", "hourly_rate", "is_billable"]):
                raise serializers.ValidationError("Cannot modify invoiced time entries")

        return attrs
