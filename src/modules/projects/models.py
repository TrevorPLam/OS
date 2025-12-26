"""
Projects Models: Project, Task, TimeEntry.

Implements project execution and time tracking for management consulting.
All relationships are enforced at the database level with foreign keys.

TIER 0: Projects belong to a Firm (through Client).
Tasks and TimeEntry inherit firm context through Project.
"""
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
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
        ('travel', 'Travel'),
        ('meals', 'Meals & Entertainment'),
        ('supplies', 'Office Supplies'),
        ('software', 'Software & Tools'),
        ('subcontractor', 'Subcontractor'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('invoiced', 'Invoiced'),
    ]
    
    # Relationships
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='expenses',
        help_text="Project this expense belongs to"
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_expenses',
        help_text="User who submitted this expense"
    )
    
    # Expense Details
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    description = models.TextField(
        help_text="Description of the expense"
    )
    date = models.DateField(
        help_text="Date expense was incurred"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Expense amount"
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Billing
    is_billable = models.BooleanField(
        default=True,
        help_text="Whether this expense should be billed to the client"
    )
    markup_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Markup percentage for billable expenses (e.g., 10.00 for 10%)"
    )
    billable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Amount to bill to client (amount + markup)"
    )
    
    # Approval & Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        help_text="User who approved this expense"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When expense was approved"
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Reason for rejection (if rejected)"
    )
    
    # Invoicing
    invoiced = models.BooleanField(
        default=False,
        help_text="Has this expense been included in an invoice?"
    )
    invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        help_text="The invoice that includes this expense"
    )
    
    # Receipt/Attachment
    receipt_url = models.URLField(
        blank=True,
        help_text="URL to receipt document in S3"
    )
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects_expenses'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['submitted_by', 'status']),
            models.Index(fields=['date']),
        ]
        verbose_name_plural = 'Expenses'
    
    def calculate_billable_amount(self):
        """Calculate billable amount with markup."""
        if not self.is_billable:
            return Decimal('0.00')
        markup = self.amount * (self.markup_percentage / Decimal('100.00'))
        return self.amount + markup
    
    def save(self, *args, **kwargs):
        """Calculate billable amount before saving."""
        self.billable_amount = self.calculate_billable_amount()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category} - ${self.amount} - {self.project.project_code}"


class Project(models.Model):
    """
    Project entity.

    Represents a consulting engagement or deliverable.
    Linked to a post-sale Client (modules.clients.Client) and optionally a Contract.

    TIER 0: Belongs to a Firm through Client relationship.
    Note: Firm is accessed via project.client.firm for tenant isolation.
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    BILLING_TYPE_CHOICES = [
        ('fixed_price', 'Fixed Price'),
        ('time_and_materials', 'Time & Materials'),
        ('retainer', 'Retainer'),
        ('non_billable', 'Non-Billable'),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='projects',
        help_text="Firm (workspace) this project belongs to"
    )

    # Relationships - UPDATED to reference clients.Client
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='projects',
        help_text="The post-sale client this project belongs to"
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        help_text="The contract governing this project (if applicable)"
    )
    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_projects',
        help_text="The lead consultant managing this project"
    )

    # Project Details
    project_code = models.CharField(max_length=50)  # TIER 0: Unique per firm (see Meta)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')

    # Financial Tracking
    billing_type = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        default='time_and_materials'
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total project budget"
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Default hourly rate for time tracking"
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    actual_completion_date = models.DateField(null=True, blank=True)

    # Milestone Tracking
    milestones = models.JSONField(
        default=list,
        help_text="List of project milestones: [{name, description, due_date, completed, completed_at}, ...]"
    )
    
    # WIP (Work in Progress) Tracking (Simple feature 1.9)
    wip_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Unbilled hours accumulated (Work in Progress)"
    )
    wip_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Unbilled amount accumulated (Work in Progress)"
    )
    wip_last_calculated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When WIP was last calculated"
    )
    last_billed_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last invoice for this project"
    )
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'projects_projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'client', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'project_manager']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', 'project_code']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', '-created_at']),  # TIER 0: Firm scoping
        ]
        # TIER 0: Project codes must be unique within a firm (not globally)
        unique_together = [['firm', 'project_code']]

    def __str__(self):
        return f"{self.project_code} - {self.name}"


class Task(models.Model):
    """
    Task entity (Kanban-style).

    Represents a work item within a project.
    Supports basic Kanban workflow (To Do -> In Progress -> Done).

    TIER 0: Belongs to a Firm through Project (task.project.firm).
    """
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('review', 'In Review'),
        ('done', 'Done'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )

    # Task Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Kanban Ordering
    position = models.IntegerField(
        default=0,
        help_text="Position in the Kanban column (lower = higher priority)"
    )

    # Time Estimation
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Task Dependencies
    depends_on = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='blocking_tasks',
        help_text="Tasks that must be completed before this task can start"
    )

    # Timeline
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_tasks'
        ordering = ['position', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"[{self.project.project_code}] {self.title}"


class TimeEntry(models.Model):
    """
    TimeEntry entity.

    Tracks billable and non-billable time spent on projects/tasks.
    Critical for Time & Materials billing and productivity analysis.

    TIER 0: Belongs to a Firm through Project (time_entry.project.firm).
    """
    # Relationships
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        help_text="Optional: link to specific task"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_entries'
    )

    # Time Details
    date = models.DateField()
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Hours worked (e.g., 1.5 for 90 minutes)"
    )
    description = models.TextField(
        help_text="What was accomplished during this time"
    )

    # Billing
    is_billable = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Rate at time of entry (may differ from project default)"
    )
    billed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Calculated: hours * hourly_rate"
    )

    # TIER 4: Approval Gate (time entries NOT billable by default)
    approved = models.BooleanField(
        default=False,
        help_text="Time entry approved for billing (default: False per Tier 4)"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_time_entries',
        help_text="Staff/Admin who approved this time entry for billing"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When time entry was approved for billing"
    )

    # Invoicing
    invoiced = models.BooleanField(
        default=False,
        help_text="Has this time been included in an invoice?"
    )
    invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        help_text="The invoice that includes this time entry"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_time_entries'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['project', 'user', 'date']),
            models.Index(fields=['invoiced']),
        ]
        verbose_name_plural = 'Time Entries'

    def save(self, *args, **kwargs):
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
            raise ValidationError(
                "Time entry cannot be invoiced unless approved. "
                "Approval required before billing."
            )

        # TIER 4: Prevent approval revocation after invoicing
        if self.pk:  # Existing record
            old_instance = TimeEntry.objects.filter(pk=self.pk).first()
            if old_instance and old_instance.invoiced and old_instance.approved and not self.approved:
                raise ValidationError(
                    "Cannot revoke approval for time entry that has been invoiced. "
                    "Approval is immutable after billing."
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.project.project_code} - {self.date} ({self.hours}h)"
