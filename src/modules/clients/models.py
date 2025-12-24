"""
Clients Models - Post-Sale Client Management

This module contains all post-sale client entities.
Clients are created when a Proposal is accepted in the CRM module.

TIER 0: All clients MUST belong to exactly one Firm for tenant isolation.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from modules.firm.utils import FirmScopedManager


class Client(models.Model):
    """
    Post-sale Client entity.

    Created when a CRM Proposal is accepted. Represents an active
    business relationship with a company that has signed a contract.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive - No Active Projects'),
        ('terminated', 'Terminated'),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        'firm.Firm',
        on_delete=models.CASCADE,
        related_name='clients',
        help_text="Firm (workspace) this client belongs to"
    )

    # Origin Tracking (from CRM)
    source_prospect = models.ForeignKey(
        'crm.Prospect',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_clients',
        help_text="The prospect that was converted to this client"
    )
    source_proposal = models.ForeignKey(
        'crm.Proposal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_clients',
        help_text="The proposal that created this client"
    )

    # Company Information
    company_name = models.CharField(max_length=255, unique=True)
    industry = models.CharField(max_length=100, blank=True)

    # Contact Information
    primary_contact_name = models.CharField(max_length=255)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=50, blank=True)

    # Address
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')

    # Business Metadata
    website = models.URLField(blank=True)
    employee_count = models.IntegerField(null=True, blank=True)

    # Client Status (Post-Sale Only)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Assigned Team
    account_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_clients',
        help_text="Primary account manager for this client"
    )
    assigned_team = models.ManyToManyField(
        User,
        related_name='assigned_clients',
        blank=True,
        help_text="Team members assigned to this client"
    )

    # Portal Access
    portal_enabled = models.BooleanField(
        default=False,
        help_text="Whether client portal access is enabled"
    )

    # Financial Tracking
    total_lifetime_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total revenue from this client across all engagements"
    )

    # Activity Tracking
    active_projects_count = models.IntegerField(
        default=0,
        help_text="Number of currently active projects"
    )
    client_since = models.DateField(
        help_text="Date of first engagement"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(
        blank=True,
        help_text="Internal notes (not visible to client)"
    )

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = 'clients_client'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['firm', 'status']),  # TIER 0: Firm scoping
            models.Index(fields=['firm', '-created_at']),  # TIER 0: Firm scoping
            models.Index(fields=['account_manager']),
            models.Index(fields=['company_name']),
        ]
        # TIER 0: Company names must be unique within a firm (not globally)
        unique_together = [['firm', 'company_name']]

    def __str__(self):
        return f"{self.company_name} ({self.firm.name})"


class ClientPortalUser(models.Model):
    """
    Client-side users with portal access.

    Links Django User accounts to Clients with specific permissions.
    """
    ROLE_CHOICES = [
        ('admin', 'Client Admin'),
        ('member', 'Client Member'),
        ('viewer', 'View Only'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='portal_users'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_portal_access'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )

    # Permissions
    can_upload_documents = models.BooleanField(default=True)
    can_view_billing = models.BooleanField(default=True)
    can_message_team = models.BooleanField(default=True)
    can_view_projects = models.BooleanField(default=True)

    # Audit
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invited_portal_users',
        help_text="Firm user who invited this client user"
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'clients_portal_user'
        unique_together = [['client', 'user']]
        ordering = ['-invited_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.client.company_name} ({self.role})"


class ClientNote(models.Model):
    """
    Internal notes about a client.

    NOT visible to the client through the portal.
    Used for team collaboration and client history tracking.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='internal_notes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_client_notes'
    )
    note = models.TextField()
    is_pinned = models.BooleanField(
        default=False,
        help_text="Pinned notes appear at top"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_note'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]

    def __str__(self):
        return f"Note by {self.author} for {self.client.company_name}"


class ClientEngagement(models.Model):
    """
    Tracks all engagements/contracts with a client.

    Provides version control and renewal tracking for client contracts.
    """
    STATUS_CHOICES = [
        ('current', 'Current Engagement'),
        ('completed', 'Completed'),
        ('renewed', 'Renewed'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='engagements'
    )
    contract = models.ForeignKey(
        'crm.Contract',
        on_delete=models.CASCADE,
        related_name='client_engagements'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='current'
    )

    # Version Control
    version = models.IntegerField(
        default=1,
        help_text="Version number for this engagement (1, 2, 3...)"
    )
    parent_engagement = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewals',
        help_text="Previous engagement if this is a renewal"
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual completion date if different from planned"
    )

    # Financial Summary
    contracted_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    actual_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Actual revenue generated (may differ from contracted)"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'clients_engagement'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['client', '-start_date']),
            models.Index(fields=['status']),
        ]
        unique_together = [['client', 'version']]

    def __str__(self):
        return f"{self.client.company_name} - Engagement v{self.version}"


class ClientComment(models.Model):
    """
    Comments from clients on project tasks.

    Allows client portal users to comment on tasks in their projects.
    Visible to both firm team and client.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='task_comments',
        help_text="Client who owns this comment"
    )
    task = models.ForeignKey(
        'projects.Task',
        on_delete=models.CASCADE,
        related_name='client_comments',
        help_text="Task being commented on"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_task_comments',
        help_text="Portal user who wrote this comment"
    )

    # Comment Content
    comment = models.TextField()

    # Attachments (optional)
    has_attachment = models.BooleanField(
        default=False,
        help_text="Whether this comment has file attachments"
    )

    # Read Status (for firm team)
    is_read_by_firm = models.BooleanField(
        default=False,
        help_text="Whether firm team has read this client comment"
    )
    read_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_client_comments',
        help_text="Firm team member who read this comment"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the comment was read by firm"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_comment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['task', '-created_at']),
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['is_read_by_firm']),
        ]

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on task {self.task.title}"


class ClientChatThread(models.Model):
    """
    Daily chat thread between client and firm team.

    Threads rotate daily (00:00 UTC) to keep conversations organized.
    Archived threads are stored in ClientChatArchive.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='chat_threads',
        help_text="Client this thread belongs to"
    )
    date = models.DateField(
        help_text="Date of this thread (YYYY-MM-DD)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this is the current active thread"
    )
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this thread was archived"
    )

    # Statistics
    message_count = models.IntegerField(
        default=0,
        help_text="Total messages in this thread"
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last message"
    )
    last_message_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_chat_message_threads',
        help_text="User who sent last message"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_chat_thread'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['client', '-date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-last_message_at']),
        ]
        unique_together = [['client', 'date']]

    def __str__(self):
        return f"{self.client.company_name} - Chat Thread {self.date}"


class ClientMessage(models.Model):
    """
    Individual message in a client chat thread.

    Messages are sent between client portal users and firm team members.
    Supports text messages and file attachments.
    """
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text Message'),
        ('file', 'File Attachment'),
        ('system', 'System Notification'),
    ]

    thread = models.ForeignKey(
        ClientChatThread,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Thread this message belongs to"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_client_messages',
        help_text="User who sent this message"
    )
    is_from_client = models.BooleanField(
        default=False,
        help_text="Whether sender is a client portal user"
    )

    # Message Content
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    content = models.TextField(
        help_text="Message text content"
    )

    # File Attachment (optional)
    attachment_url = models.URLField(
        blank=True,
        help_text="S3 URL for file attachment (if message_type=file)"
    )
    attachment_filename = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename of attachment"
    )
    attachment_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )

    # Read Status
    is_read = models.BooleanField(
        default=False,
        help_text="Whether message has been read by recipient"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When message was read"
    )
    read_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_client_messages',
        help_text="User who read this message"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        sender_name = self.sender.get_full_name() or self.sender.username
        return f"Message from {sender_name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        """Update thread statistics when message is saved."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update thread statistics
            self.thread.message_count = self.thread.messages.count()
            self.thread.last_message_at = self.created_at
            self.thread.last_message_by = self.sender
            self.thread.save()
