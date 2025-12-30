"""
Projects Models: Project, Task, TimeEntry.

Implements project execution and time tracking for management consulting.
All relationships are enforced at the database level with foreign keys.

TIER 0: Projects belong to a Firm (through Client).
Tasks and TimeEntry inherit firm context through Project.
"""

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from modules.crm.models import Contract
from modules.firm.utils import FirmScopedManager


class Expense(models.Model):
    """
    Expense tracking for projects (TIER 4+: Simple feature 1.5).

    Tracks project-related expenses that can be billed to clients
    or recorded as internal costs.

    TIER 0: Belongs to a Firm through Project.
    """

    CATEGORY_CHOICES = [
        ("travel", "Travel"),
        ("meals", "Meals & Entertainment"),
        ("supplies", "Office Supplies"),
        ("software", "Software & Tools"),
        ("subcontractor", "Subcontractor"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("invoiced", "Invoiced"),
    ]

    # Relationships
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="expenses", help_text="Project this expense belongs to"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_expenses",
        help_text="User who submitted this expense",
    )

    # Expense Details
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    description = models.TextField(help_text="Description of the expense")
    date = models.DateField(help_text="Date expense was incurred")
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], help_text="Expense amount"
    )
    currency = models.CharField(max_length=3, default="USD")

    # Billing
    is_billable = models.BooleanField(default=True, help_text="Whether this expense should be billed to the client")
    markup_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Markup percentage for billable expenses (e.g., 10.00 for 10%)",
    )
    billable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Amount to bill to client (amount + markup)",
    )

    # Approval & Status (Medium Feature 2.4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
        help_text="User who approved this expense",
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="When expense was approved")

    # Rejection Tracking (Medium Feature 2.4)
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_expenses",
        help_text="User who rejected this expense",
    )
    rejected_at = models.DateTimeField(null=True, blank=True, help_text="When expense was rejected")
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection (if rejected)")

    # Invoicing
    invoiced = models.BooleanField(default=False, help_text="Has this expense been included in an invoice?")
    invoice = models.ForeignKey(
        "finance.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
        help_text="The invoice that includes this expense",
    )

    # Receipt/Attachment
    receipt_url = models.URLField(blank=True, help_text="URL to receipt document in S3")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers (inherit firm context through project)
    objects = models.Manager()  # Default manager

    class Meta:
        db_table = "projects_expenses"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"], name="projects_pro_sta_idx"),
            models.Index(fields=["submitted_by", "status"], name="projects_sub_sta_idx"),
            models.Index(fields=["date"], name="projects_dat_idx"),
        ]
        verbose_name_plural = "Expenses"

    def __str__(self) -> str:
        return f"{self.category} - ${self.amount} - {self.project.project_code}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Calculate billable amount before saving."""
        self.full_clean()  # Run validation before save
        self.billable_amount = self.calculate_billable_amount()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate expense data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Validate approval workflow
        if self.status == "approved" and not self.approved_by_id:
            errors["status"] = "Cannot set status to 'approved' without an approver."
        if self.status == "rejected" and not self.rejected_by_id:
            errors["status"] = "Cannot set status to 'rejected' without specifying who rejected."
        if self.status == "rejected" and not self.rejection_reason:
            errors["rejection_reason"] = "Rejection reason is required when rejecting an expense."

        # Cannot invoice unapproved expenses
        if self.invoiced and self.status != "approved":
            errors["invoiced"] = "Only approved expenses can be invoiced."

        if errors:
            raise ValidationError(errors)

    def calculate_billable_amount(self) -> Decimal:
        """Calculate billable amount with markup."""
        if not self.is_billable:
            return Decimal("0.00")
        markup = self.amount * (self.markup_percentage / Decimal("100.00"))
        return self.amount + markup


class Project(models.Model):
    """
    Project entity.

    Represents a consulting engagement or deliverable.
    Linked to a post-sale Client (modules.clients.Client) and optionally a Contract.

    TIER 0: Belongs to a Firm through Client relationship.
    Note: Firm is accessed via project.client.firm for tenant isolation.
    """

    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("in_progress", "In Progress"),
        ("on_hold", "On Hold"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    BILLING_TYPE_CHOICES = [
        ("fixed_price", "Fixed Price"),
        ("time_and_materials", "Time & Materials"),
        ("retainer", "Retainer"),
        ("non_billable", "Non-Billable"),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="projects",
        help_text="Firm (workspace) this project belongs to",
    )

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.CASCADE,
        related_name="projects",
        help_text="The post-sale client this project belongs to",
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text="The contract governing this project (if applicable)",
    )
    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_projects",
        help_text="The lead consultant managing this project",
    )

    # Project Details
    project_code = models.CharField(max_length=50)  # TIER 0: Unique per firm (see Meta)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")

    # Financial Tracking
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default="time_and_materials")
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total project budget",
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Default hourly rate for time tracking",
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    actual_completion_date = models.DateField(null=True, blank=True)

    # Milestone Tracking
    milestones = models.JSONField(
        default=list,
        help_text="List of project milestones: [{name, description, due_date, completed, completed_at}, ...]",
    )

    # WIP (Work in Progress) Tracking (Simple feature 1.9)
    wip_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Unbilled hours accumulated (Work in Progress)",
    )
    wip_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Unbilled amount accumulated (Work in Progress)",
    )
    wip_last_calculated = models.DateTimeField(null=True, blank=True, help_text="When WIP was last calculated")
    last_billed_date = models.DateField(null=True, blank=True, help_text="Date of last invoice for this project")
    
    # Client Acceptance Gate (Medium Feature 2.8)
    client_accepted = models.BooleanField(
        default=False,
        help_text="Whether the client has accepted the project deliverables",
    )
    acceptance_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when client accepted the project",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_projects",
        help_text="User (client portal user or staff) who marked the project as accepted",
    )
    acceptance_notes = models.TextField(
        blank=True,
        help_text="Notes or feedback from client acceptance",
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "projects_projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping, name="projects_fir_sta_idx")
            models.Index(fields=["firm", "client", "status"]),  # TIER 0: Firm scoping, name="projects_fir_cli_sta_idx")
            models.Index(fields=["firm", "project_manager"]),  # TIER 0: Firm scoping, name="projects_fir_pro_idx")
            models.Index(fields=["firm", "project_code"]),  # TIER 0: Firm scoping, name="projects_fir_pro_idx")
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping, name="projects_fir_cre_idx")
        ]
        # TIER 0: Project codes must be unique within a firm (not globally)
        unique_together = [["firm", "project_code"]]

    def __str__(self) -> str:
        return f"{self.project_code} - {self.name}"
    
    def mark_client_accepted(self, user, notes: str = "") -> None:
        """
        Mark project as client-accepted (Medium Feature 2.8).
        
        This establishes a gate for invoice generation - projects must be
        client-accepted before final invoicing.
        
        Args:
            user: The user marking acceptance (staff or portal user)
            notes: Optional acceptance notes or feedback
        """
        from django.utils import timezone
        
        if self.client_accepted:
            from django.core.exceptions import ValidationError
            raise ValidationError("Project has already been accepted by client.")
        
        self.client_accepted = True
        self.acceptance_date = timezone.now().date()
        self.accepted_by = user
        self.acceptance_notes = notes
        self.save(update_fields=["client_accepted", "acceptance_date", "accepted_by", "acceptance_notes", "updated_at"])
    
    def can_generate_invoice(self) -> tuple[bool, str]:
        """
        Check if project can generate invoices (Medium Feature 2.8).
        
        Returns:
            Tuple of (can_invoice: bool, reason: str)
            - can_invoice: True if project can be invoiced
            - reason: Empty string if can invoice, otherwise explanation of why not
        """
        if self.status == "cancelled":
            return False, "Cannot invoice cancelled project"
        
        if self.status == "planning":
            return False, "Cannot invoice project still in planning phase"
        
        # Client acceptance gate (if project is completed)
        if self.status == "completed" and not self.client_accepted:
            return False, "Project must be client-accepted before final invoicing"
        
        return True, ""
    
    def calculate_utilization_metrics(self, start_date=None, end_date=None):
        """
        Calculate project utilization metrics (Medium Feature 2.9).
        
        Returns dictionary with:
        - total_hours: Total hours logged on project
        - billable_hours: Billable hours logged
        - non_billable_hours: Non-billable hours logged
        - utilization_rate: Percentage of hours that are billable
        - hours_vs_budget: Hours logged vs budgeted hours (if budget exists)
        - team_members: Count of unique users with time entries
        - avg_hours_per_user: Average hours per team member
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
        """
        from django.db.models import Sum, Count, Q, F
        
        # Build queryset with date filters and optimization
        time_entries = self.time_entries.select_related('user').all()
        if start_date:
            time_entries = time_entries.filter(date__gte=start_date)
        if end_date:
            time_entries = time_entries.filter(date__lte=end_date)
        
        # Calculate aggregates
        stats = time_entries.aggregate(
            total_hours=Sum("hours"),
            billable_hours=Sum("hours", filter=Q(is_billable=True)),
            non_billable_hours=Sum("hours", filter=Q(is_billable=False)),
            team_members=Count("user", distinct=True),
        )
        
        total_hours = stats["total_hours"] or Decimal("0.00")
        billable_hours = stats["billable_hours"] or Decimal("0.00")
        non_billable_hours = stats["non_billable_hours"] or Decimal("0.00")
        team_members = stats["team_members"] or 0
        
        # Calculate utilization rate
        utilization_rate = (
            (billable_hours / total_hours * 100) if total_hours > 0 else Decimal("0.00")
        )
        
        # Calculate hours vs budget
        budgeted_hours = None
        hours_variance = None
        if self.budget and self.hourly_rate and self.hourly_rate > 0:
            budgeted_hours = self.budget / self.hourly_rate
            hours_variance = total_hours - budgeted_hours
        
        # Calculate avg hours per user
        avg_hours_per_user = (
            (total_hours / team_members) if team_members > 0 else Decimal("0.00")
        )
        
        return {
            "total_hours": float(total_hours),
            "billable_hours": float(billable_hours),
            "non_billable_hours": float(non_billable_hours),
            "utilization_rate": float(utilization_rate),
            "budgeted_hours": float(budgeted_hours) if budgeted_hours else None,
            "hours_variance": float(hours_variance) if hours_variance else None,
            "team_members": team_members,
            "avg_hours_per_user": float(avg_hours_per_user),
        }

    def clean(self) -> None:
        """Validate project data integrity."""
        from django.core.exceptions import ValidationError

        errors = {}

        # Validate date range
        if self.start_date and self.end_date and self.end_date < self.start_date:
            errors["end_date"] = "End date must be after start date."

        # Validate actual completion date
        if self.actual_completion_date and self.start_date:
            if self.actual_completion_date < self.start_date:
                errors["actual_completion_date"] = "Actual completion date cannot be before start date."

        # Validate client belongs to same firm
        if self.client_id and self.firm_id:
            if hasattr(self, "client") and self.client.firm_id != self.firm_id:
                errors["client"] = "Client must belong to the same firm as the project."

        if errors:
            raise ValidationError(errors)
    
    @classmethod
    def calculate_user_utilization(cls, firm, user, start_date, end_date):
        """
        Calculate utilization metrics for a specific user (Medium Feature 2.9).
        
        Calculates across all projects for a user within a date range.
        
        Returns dictionary with:
        - total_hours: Total hours logged by user
        - billable_hours: Billable hours logged
        - non_billable_hours: Non-billable hours  
        - utilization_rate: Percentage billable
        - projects_worked: Count of unique projects
        - available_hours: Expected working hours in period (assumes 40hr/week)
        - capacity_utilization: Percentage of available hours used
        
        Args:
            firm: Firm to scope query
            user: User to calculate metrics for
            start_date: Period start date
            end_date: Period end date
        """
        from django.db.models import Sum, Count, Q
        from datetime import timedelta
        
        # Get all time entries for user in date range
        time_entries = TimeEntry.objects.filter(
            project__firm=firm,
            user=user,
            date__gte=start_date,
            date__lte=end_date,
        )
        
        # Calculate aggregates
        stats = time_entries.aggregate(
            total_hours=Sum("hours"),
            billable_hours=Sum("hours", filter=Q(is_billable=True)),
            non_billable_hours=Sum("hours", filter=Q(is_billable=False)),
            projects_worked=Count("project", distinct=True),
        )
        
        total_hours = stats["total_hours"] or Decimal("0.00")
        billable_hours = stats["billable_hours"] or Decimal("0.00")
        non_billable_hours = stats["non_billable_hours"] or Decimal("0.00")
        projects_worked = stats["projects_worked"] or 0
        
        # Calculate utilization rate
        utilization_rate = (
            (billable_hours / total_hours * 100) if total_hours > 0 else Decimal("0.00")
        )
        
        # Calculate available hours (assumes 40-hour work week, 5 days/week)
        days_in_period = (end_date - start_date).days + 1
        weeks_in_period = Decimal(str(days_in_period / 7))
        available_hours = weeks_in_period * Decimal("40.00")
        
        # Calculate capacity utilization
        capacity_utilization = (
            (total_hours / available_hours * 100) if available_hours > 0 else Decimal("0.00")
        )
        
        return {
            "user_id": user.id,
            "user_email": user.email,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_hours": float(total_hours),
            "billable_hours": float(billable_hours),
            "non_billable_hours": float(non_billable_hours),
            "utilization_rate": float(utilization_rate),
            "projects_worked": projects_worked,
            "available_hours": float(available_hours),
            "capacity_utilization": float(capacity_utilization),
        }


class Task(models.Model):
    """
    Task entity (Kanban-style).

    Represents a work item within a project.
    Supports basic Kanban workflow (To Do -> In Progress -> Done).

    TIER 0: Belongs to a Firm through Project (task.project.firm).
    """

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("in_progress", "In Progress"),
        ("blocked", "Blocked"),
        ("review", "In Review"),
        ("done", "Done"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks"
    )

    # Task Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")

    # Kanban Ordering
    position = models.IntegerField(default=0, help_text="Position in the Kanban column (lower = higher priority)")

    # Time Estimation
    estimated_hours = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))]
    )

    # Task Dependencies
    depends_on = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="blocking_tasks",
        help_text="Tasks that must be completed before this task can start",
    )

    # Timeline
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Template Traceability (DOC-12.1: Required for template instantiation)
    template_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of DeliveryTemplate this task was created from",
    )
    template_version = models.IntegerField(
        null=True,
        blank=True,
        help_text="Version of template at instantiation",
    )
    template_node_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Node ID within template",
    )
    instantiation_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of TemplateInstantiation batch",
    )

    # Tags (for template-based categorization)
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Tags/labels for this task",
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_tasks"
        ordering = ["position", "-created_at"]
        indexes = [
            models.Index(fields=["project", "status"], name="projects_pro_sta_idx"),
            models.Index(fields=["assigned_to"], name="projects_ass_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.project.project_code}] {self.title}"


class TimeEntry(models.Model):
    """
    TimeEntry entity.

    Tracks billable and non-billable time spent on projects/tasks.
    Critical for Time & Materials billing and productivity analysis.

    TIER 0: Belongs to a Firm through Project (time_entry.project.firm).
    """

    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="time_entries")
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
        help_text="Optional: link to specific task",
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="time_entries")

    # Time Details
    date = models.DateField()
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Hours worked (e.g., 1.5 for 90 minutes)",
    )
    description = models.TextField(help_text="What was accomplished during this time")

    # Billing
    is_billable = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Rate at time of entry (may differ from project default)",
    )
    billed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Calculated: hours * hourly_rate",
    )

    # TIER 4: Approval Gate (time entries NOT billable by default)
    approved = models.BooleanField(
        default=False, help_text="Time entry approved for billing (default: False per Tier 4)"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_time_entries",
        help_text="Staff/Admin who approved this time entry for billing",
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="When time entry was approved for billing")

    # Invoicing
    invoiced = models.BooleanField(default=False, help_text="Has this time been included in an invoice?")
    invoice = models.ForeignKey(
        "finance.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
        help_text="The invoice that includes this time entry",
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_time_entries"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["project", "user", "date"], name="projects_pro_use_dat_idx"),
            models.Index(fields=["invoiced"], name="projects_inv_idx"),
            # Composite indexes for common filtering patterns
            models.Index(fields=["project", "approved", "invoiced"]),  # Unbilled approved entries, name="projects_pro_app_inv_idx")
            models.Index(fields=["project", "-date"]),  # Time entries by project sorted by date, name="projects_pro_dat_idx")
            models.Index(fields=["user", "-date"]),  # User's recent time entries, name="projects_use_dat_idx")
        ]
        verbose_name_plural = "Time Entries"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.project.project_code} - {self.date} ({self.hours}h)"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Calculate billed_amount and enforce approval gates before saving.

        TIER 4 Billing Invariants:
        - Time entries cannot be invoiced unless approved
        - Approval cannot be revoked if already invoiced
        """
        from django.core.exceptions import ValidationError

        # Calculate billed amount
        self.billed_amount = self.hours * self.hourly_rate

        # TIER 4: Enforce approval gate
        if self.invoiced and not self.approved:
            raise ValidationError("Time entry cannot be invoiced unless approved. " "Approval required before billing.")

        # TIER 4: Prevent approval revocation after invoicing
        if self.pk:  # Existing record
            old_instance = TimeEntry.objects.filter(pk=self.pk).first()
            if old_instance:
                if old_instance.invoiced:
                    immutable_fields = {
                        "project_id": (old_instance.project_id, self.project_id),
                        "task_id": (old_instance.task_id, self.task_id),
                        "user_id": (old_instance.user_id, self.user_id),
                        "date": (old_instance.date, self.date),
                        "hours": (old_instance.hours, self.hours),
                        "description": (old_instance.description, self.description),
                        "is_billable": (old_instance.is_billable, self.is_billable),
                        "hourly_rate": (old_instance.hourly_rate, self.hourly_rate),
                        "approved": (old_instance.approved, self.approved),
                        "approved_by_id": (old_instance.approved_by_id, self.approved_by_id),
                        "approved_at": (old_instance.approved_at, self.approved_at),
                        "invoice_id": (old_instance.invoice_id, self.invoice_id),
                        "invoiced": (old_instance.invoiced, self.invoiced),
                    }
                    changed_fields = [
                        field for field, (old_value, new_value) in immutable_fields.items() if old_value != new_value
                    ]
                    if changed_fields:
                        raise ValidationError(
                            "Cannot modify invoiced time entries "
                            f"(immutable fields changed: {', '.join(changed_fields)})."
                        )

                if old_instance.invoiced and old_instance.approved and not self.approved:
                    raise ValidationError(
                        "Cannot revoke approval for time entry that has been invoiced. "
                        "Approval is immutable after billing."
                    )

        super().save(*args, **kwargs)


class ProjectTemplate(models.Model):
    """
    Project Template entity (Medium Feature 2.2).

    Stores reusable project templates that can be cloned to create new projects.
    Useful for standardizing SOPs, checklists, and recurring project types.

    TIER 0: Belongs to a Firm (tenant boundary).
    """

    # TIER 0: Firm tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="project_templates",
        help_text="Firm (workspace) this template belongs to",
    )

    # Template Details
    template_name = models.CharField(
        max_length=255, help_text="Name of the template (e.g., 'Standard Tax Return', 'Audit Engagement')"
    )
    template_code = models.CharField(max_length=50, help_text="Template code/identifier")
    description = models.TextField(blank=True, help_text="Template description and usage notes")
    category = models.CharField(
        max_length=100, blank=True, help_text="Template category for organization (e.g., 'Tax', 'Audit', 'Consulting')"
    )

    # Default Project Settings
    default_billing_type = models.CharField(
        max_length=20, choices=Project.BILLING_TYPE_CHOICES, default="time_and_materials"
    )
    default_duration_days = models.IntegerField(null=True, blank=True, help_text="Default project duration in days")
    default_hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Default hourly rate for projects created from this template",
    )

    # Template Milestones
    template_milestones = models.JSONField(
        default=list, help_text="Default milestones: [{name, description, days_from_start}, ...]"
    )

    # Template Configuration
    is_active = models.BooleanField(default=True, help_text="Whether this template is available for use")

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_project_templates",
        help_text="User who created this template",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "projects_templates"
        ordering = ["category", "template_name"]
        indexes = [
            models.Index(fields=["firm", "is_active"], name="projects_fir_is__idx"),
            models.Index(fields=["firm", "category"], name="projects_fir_cat_idx"),
        ]
        unique_together = [["firm", "template_code"]]

    def __str__(self) -> str:
        return f"{self.template_code} - {self.template_name}"

    def clone_to_project(
        self,
        client: Any,
        project_code: str,
        name: str | None = None,
        start_date: Any = None,
        project_manager: Any = None,
        **kwargs: Any,
    ) -> Any:
        """
        Clone this template to create a new project.

        Args:
            client: The Client instance for the new project
            project_code: Unique project code
            name: Project name (defaults to template name)
            start_date: Project start date (defaults to today)
            project_manager: User to assign as project manager
            **kwargs: Additional project fields to override

        Returns:
            Project: The newly created project
        """
        from datetime import date, timedelta

        if start_date is None:
            start_date = date.today()

        # Calculate end date
        if self.default_duration_days:
            end_date = start_date + timedelta(days=self.default_duration_days)
        else:
            end_date = start_date + timedelta(days=90)  # Default 90 days

        # Create the project
        project = Project.objects.create(
            firm=self.firm,
            client=client,
            project_code=project_code,
            name=name or self.template_name,
            description=self.description,
            status="planning",
            billing_type=self.default_billing_type,
            hourly_rate=self.default_hourly_rate,
            start_date=start_date,
            end_date=end_date,
            project_manager=project_manager,
            **kwargs,
        )

        # Clone milestones
        if self.template_milestones:
            milestones = []
            for template_milestone in self.template_milestones:
                milestone_due = start_date + timedelta(days=template_milestone.get("days_from_start", 0))
                milestones.append(
                    {
                        "name": template_milestone.get("name"),
                        "description": template_milestone.get("description", ""),
                        "due_date": milestone_due.isoformat(),
                        "completed": False,
                        "completed_at": None,
                    }
                )
            project.milestones = milestones
            project.save(update_fields=["milestones"])

        # Clone template tasks
        task_templates = self.task_templates.all().order_by("position")
        task_mapping = {}  # Map template task ID to new task

        for task_template in task_templates:
            task = task_template.clone_to_task(project)
            task_mapping[task_template.id] = task

        # Set up task dependencies
        for task_template in task_templates:
            if task_template.depends_on_templates.exists():
                new_task = task_mapping[task_template.id]
                for dep_template in task_template.depends_on_templates.all():
                    if dep_template.id in task_mapping:
                        new_task.depends_on.add(task_mapping[dep_template.id])

        return project


class TaskTemplate(models.Model):
    """
    Task Template entity (Medium Feature 2.2).

    Stores template tasks that are cloned when a project is created from a template.

    TIER 0: Belongs to a Firm through ProjectTemplate.
    """

    # Relationships
    project_template = models.ForeignKey(
        ProjectTemplate,
        on_delete=models.CASCADE,
        related_name="task_templates",
        help_text="The project template this task belongs to",
    )

    # Task Template Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    default_status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default="todo")
    default_priority = models.CharField(max_length=10, choices=Task.PRIORITY_CHOICES, default="medium")

    # Positioning
    position = models.IntegerField(default=0, help_text="Order in template (lower = higher priority)")

    # Time Estimation
    estimated_hours = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))]
    )

    # Dependencies (within template)
    depends_on_templates = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="blocking_templates",
        help_text="Template tasks that must be completed first",
    )

    # Scheduling
    days_from_project_start = models.IntegerField(
        null=True, blank=True, help_text="Due date offset from project start (days)"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_task_templates"
        ordering = ["project_template", "position"]
        indexes = [
            models.Index(fields=["project_template", "position"], name="projects_pro_pos_idx"),
        ]

    def __str__(self) -> str:
        return f"[{self.project_template.template_code}] {self.title}"

    def clone_to_task(self, project: Any) -> Any:
        """
        Clone this template to create a task in the given project.

        Args:
            project: The Project instance to create the task in

        Returns:
            Task: The newly created task
        """
        from datetime import timedelta

        due_date = None
        if self.days_from_project_start is not None:
            due_date = project.start_date + timedelta(days=self.days_from_project_start)

        task = Task.objects.create(
            project=project,
            title=self.title,
            description=self.description,
            status=self.default_status,
            priority=self.default_priority,
            position=self.position,
            estimated_hours=self.estimated_hours,
            due_date=due_date,
        )

        return task
