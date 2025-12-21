"""
Projects Models: Project, Task, TimeEntry.

Implements project execution and time tracking for management consulting.
All relationships are enforced at the database level with foreign keys.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from modules.crm.models import Contract


class Project(models.Model):
    """
    Project entity.

    Represents a consulting engagement or deliverable.
    Linked to a post-sale Client (modules.clients.Client) and optionally a Contract.
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_projects',
        help_text="The lead consultant managing this project"
    )

    # Project Details
    project_code = models.CharField(max_length=50, unique=True)
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

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'projects_projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['project_manager']),
            models.Index(fields=['project_code']),
        ]

    def __str__(self):
        return f"{self.project_code} - {self.name}"


class Task(models.Model):
    """
    Task entity (Kanban-style).

    Represents a work item within a project.
    Supports basic Kanban workflow (To Do -> In Progress -> Done).
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
        User,
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
        User,
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
        """Calculate billed_amount before saving."""
        self.billed_amount = self.hours * self.hourly_rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.project.project_code} - {self.date} ({self.hours}h)"
