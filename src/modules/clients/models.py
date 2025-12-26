"""
Clients Models - Post-Sale Client Management

This module contains all post-sale client entities.
Clients are created when a Proposal is accepted in the CRM module.

TIER 0: All clients MUST belong to exactly one Firm for tenant isolation.
TIER 2.6: Organizations allow optional cross-client collaboration within a firm.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from modules.firm.utils import FirmScopedManager


class Organization(models.Model):
    """
    Organization entity for grouping clients within a firm.

    TIER 2.6: Organizations enable intentional cross-client collaboration.

    Key Rules:
    - Organizations are optional context/grouping, NOT a security boundary
    - Firm remains the top-level tenant boundary
    - Cross-client access is allowed ONLY within the same organization
    - Organizations must belong to exactly one firm

    Use Cases:
    - Multiple subsidiary companies under one parent organization
    - Different divisions/departments of the same company
    - Related entities that need to share data (projects, documents, etc.)
    """

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="organizations",
        help_text="Firm this organization belongs to",
    )

    # Organization Information
    name = models.CharField(max_length=255, help_text="Organization name (e.g., 'Acme Corp')")
    description = models.TextField(blank=True, help_text="Description of this organization")

    # Settings
    enable_cross_client_visibility = models.BooleanField(
        default=True, help_text="Whether clients in this org can see each other's data (where appropriate)"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
        help_text="Firm user who created this organization",
    )

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "clients_organization"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "name"]),  # TIER 0: Firm scoping
        ]
        # TIER 2.6: Organization names must be unique within a firm
        unique_together = [["firm", "name"]]

    def __str__(self):
        return f"{self.name} ({self.firm.name})"


class Client(models.Model):
    """
    Post-sale Client entity.

    Created when a CRM Proposal is accepted. Represents an active
    business relationship with a company that has signed a contract.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive - No Active Projects"),
        ("terminated", "Terminated"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="clients",
        help_text="Firm (workspace) this client belongs to",
    )

    # TIER 2.6: Organization grouping (OPTIONAL)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
        help_text="Optional organization for cross-client collaboration",
    )

    # Origin Tracking (from CRM)
    source_prospect = models.ForeignKey(
        "crm.Prospect",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converted_clients",
        help_text="The prospect that was converted to this client",
    )
    source_proposal = models.ForeignKey(
        "crm.Proposal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="converted_clients",
        help_text="The proposal that created this client",
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
    country = models.CharField(max_length=100, default="USA")

    # Business Metadata
    website = models.URLField(blank=True)
    employee_count = models.IntegerField(null=True, blank=True)

    # Client Status (Post-Sale Only)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Assigned Team
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_clients",
        help_text="Primary account manager for this client",
    )
    assigned_team = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_clients",
        blank=True,
        help_text="Team members assigned to this client",
    )

    # Portal Access
    portal_enabled = models.BooleanField(default=False, help_text="Whether client portal access is enabled")

    # Financial Tracking
    total_lifetime_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total revenue from this client across all engagements",
    )

    # Retainer Balance Tracking (Simple feature 1.6)
    retainer_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current retainer balance (prepaid hours/amount)",
    )
    retainer_hours_balance = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0.00"), help_text="Prepaid hours remaining in retainer"
    )
    retainer_last_updated = models.DateTimeField(
        null=True, blank=True, help_text="When retainer balance was last updated"
    )

    # TIER 4: Autopay Settings
    autopay_enabled = models.BooleanField(default=False, help_text="Enable automatic payment of invoices")
    autopay_payment_method_id = models.CharField(
        max_length=255, blank=True, help_text="Stripe payment method ID for autopay"
    )
    autopay_activated_at = models.DateTimeField(null=True, blank=True, help_text="When autopay was enabled")
    autopay_activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="autopay_activations",
        help_text="Who enabled autopay",
    )

    # Activity Tracking
    active_projects_count = models.IntegerField(default=0, help_text="Number of currently active projects")
    client_since = models.DateField(help_text="Date of first engagement")

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes (not visible to client)")

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "clients_client"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping
            models.Index(fields=["organization"]),  # TIER 2.6: Org scoping
            models.Index(fields=["account_manager"]),
            models.Index(fields=["company_name"]),
        ]
        # TIER 0: Company names must be unique within a firm (not globally)
        unique_together = [["firm", "company_name"]]

    def __str__(self):
        return f"{self.company_name} ({self.firm.name})"


class ClientPortalUser(models.Model):
    """
    Client-side users with portal access.

    Links Django User accounts to Clients with specific permissions.
    """

    ROLE_CHOICES = [
        ("admin", "Client Admin"),
        ("member", "Client Member"),
        ("viewer", "View Only"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="portal_users")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_portal_access")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    # Permissions
    can_upload_documents = models.BooleanField(default=True)
    can_view_billing = models.BooleanField(default=True)
    can_message_team = models.BooleanField(default=True)
    can_view_projects = models.BooleanField(default=True)

    # Audit
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="invited_portal_users",
        help_text="Firm user who invited this client user",
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "clients_portal_user"
        unique_together = [["client", "user"]]
        ordering = ["-invited_at"]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.client.company_name} ({self.role})"


class ClientNote(models.Model):
    """
    Internal notes about a client.

    NOT visible to the client through the portal.
    Used for team collaboration and client history tracking.
    """

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="internal_notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="authored_client_notes"
    )
    note = models.TextField()
    is_pinned = models.BooleanField(default=False, help_text="Pinned notes appear at top")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_note"
        ordering = ["-is_pinned", "-created_at"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
        ]

    def __str__(self):
        return f"Note by {self.author} for {self.client.company_name}"


class ClientEngagement(models.Model):
    """
    Tracks all engagements/contracts with a client.

    Provides version control and renewal tracking for client contracts.

    TIER 4: Defines pricing mode (package, hourly, mixed) for billing.
    """

    STATUS_CHOICES = [
        ("current", "Current Engagement"),
        ("completed", "Completed"),
        ("renewed", "Renewed"),
    ]

    # TIER 4: Pricing Mode Choices
    PRICING_MODE_CHOICES = [
        ("package", "Package/Fixed Fee"),
        ("hourly", "Hourly/Time & Materials"),
        ("mixed", "Mixed (Package + Hourly)"),
    ]

    # TIER 4: Firm tenancy (for efficient queries, auto-populated from client)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="client_engagements",
        help_text="Firm this engagement belongs to (auto-populated from client)",
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="engagements")
    contract = models.ForeignKey("crm.Contract", on_delete=models.CASCADE, related_name="client_engagements")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="current")

    # TIER 4: Pricing Mode
    pricing_mode = models.CharField(
        max_length=20, choices=PRICING_MODE_CHOICES, default="package", help_text="Pricing model for this engagement"
    )

    # TIER 4: Package Fee (if pricing_mode = 'package' or 'mixed')
    package_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Fixed package fee (required for package/mixed mode)",
    )
    package_fee_schedule = models.CharField(
        max_length=50, blank=True, help_text="Payment schedule (e.g., 'Monthly', 'Quarterly', 'One-time')"
    )

    # TIER 4: Hourly Billing (if pricing_mode = 'hourly' or 'mixed')
    allow_hourly_billing = models.BooleanField(default=False, help_text="Allow hourly billing for this engagement")
    hourly_rate_default = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Default hourly rate (if hourly billing allowed)",
    )

    # Version Control
    version = models.IntegerField(default=1, help_text="Version number for this engagement (1, 2, 3...)")
    parent_engagement = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="renewals",
        help_text="Previous engagement if this is a renewal",
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    actual_end_date = models.DateField(
        null=True, blank=True, help_text="Actual completion date if different from planned"
    )

    # Financial Summary
    contracted_value = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    actual_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Actual revenue generated (may differ from contracted)",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "clients_engagement"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["client", "-start_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["firm", "status"]),  # TIER 4: Firm scoping
            models.Index(fields=["firm", "-start_date"]),  # TIER 4: Firm scoping
        ]
        unique_together = [["client", "version"]]

    def save(self, *args, **kwargs):
        """
        Enforce TIER 4 pricing mode invariants, engagement immutability, and auto-populate firm.

        Validation:
        - If pricing_mode='package' or 'mixed': package_fee required
        - If pricing_mode='hourly' or 'mixed': hourly_rate_default required
        - If pricing_mode='mixed': both package_fee AND hourly_rate required
        - IMMUTABILITY: Completed/renewed engagements cannot modify critical fields (TIER 3)
        - IMMUTABILITY: Engagements with invoices cannot change pricing terms (TIER 3)

        Auto-population:
        - firm is auto-populated from client.firm if not set
        """
        from django.core.exceptions import ValidationError

        # Auto-populate firm from client
        if not self.firm_id and self.client_id:
            self.firm = self.client.firm

        # TIER 3: Engagement immutability validation (prevent historical modification)
        if self.pk:  # Existing engagement
            try:
                old_instance = ClientEngagement.objects.get(pk=self.pk)

                # Critical fields that cannot be modified once engagement is completed/renewed
                IMMUTABLE_FIELDS_WHEN_CLOSED = [
                    "pricing_mode",
                    "package_fee",
                    "hourly_rate_default",
                    "contracted_value",
                    "start_date",
                    "end_date",
                ]

                # Prevent modification of completed/renewed engagements
                if old_instance.status in ["completed", "renewed"]:
                    # Allow only specific updates (update_fields pattern)
                    update_fields = kwargs.get("update_fields", [])
                    if not update_fields:
                        # No update_fields specified, check if any critical field changed
                        for field in IMMUTABLE_FIELDS_WHEN_CLOSED:
                            if getattr(old_instance, field) != getattr(self, field):
                                raise ValidationError(
                                    f"Cannot modify '{field}' on {old_instance.status} engagement. "
                                    f"Engagement v{old_instance.version} is immutable after completion."
                                )

                # Prevent pricing changes if engagement has invoices (signed engagement)
                if old_instance.invoices.exists():
                    pricing_fields = ["pricing_mode", "package_fee", "hourly_rate_default"]
                    for field in pricing_fields:
                        if getattr(old_instance, field) != getattr(self, field):
                            invoice_count = old_instance.invoices.count()
                            raise ValidationError(
                                f"Cannot modify '{field}': engagement has {invoice_count} invoice(s). "
                                f"Pricing terms are immutable once invoicing has begun."
                            )

            except ClientEngagement.DoesNotExist:
                # New record or concurrent delete, proceed
                pass

        # Validate package mode
        if self.pricing_mode in ["package", "mixed"]:
            if not self.package_fee:
                raise ValidationError(f"Package fee is required for pricing mode '{self.pricing_mode}'")

        # Validate hourly mode
        if self.pricing_mode in ["hourly", "mixed"]:
            if not self.hourly_rate_default:
                raise ValidationError(f"Hourly rate is required for pricing mode '{self.pricing_mode}'")
            # Auto-enable hourly billing for hourly/mixed modes
            self.allow_hourly_billing = True

        super().save(*args, **kwargs)

    def renew(
        self,
        new_package_fee=None,
        new_hourly_rate=None,
        new_pricing_mode=None,
        renewal_start_date=None,
        renewal_end_date=None,
    ):
        """
        Create renewal engagement (TIER 4: Task 4.8).

        Renewals create new engagements without mutating old ones.
        Old engagement invoices remain untouched.
        New billing terms apply only going forward.

        Args:
            new_package_fee: New package fee (if changing, otherwise inherits)
            new_hourly_rate: New hourly rate (if changing, otherwise inherits)
            new_pricing_mode: New pricing mode (if changing, otherwise inherits)
            renewal_start_date: Start date for renewal (defaults to day after current end_date)
            renewal_end_date: End date for renewal (defaults to 1 year from start)

        Returns:
            New ClientEngagement instance (renewal)

        Raises:
            ValidationError: If engagement cannot be renewed (e.g., already renewed)
        """
        from datetime import timedelta

        from django.core.exceptions import ValidationError

        # Prevent duplicate renewals
        if self.status == "renewed":
            raise ValidationError(
                f"Engagement v{self.version} has already been renewed. " f"Cannot renew the same engagement twice."
            )

        # Mark current engagement as completed
        self.status = "completed"
        self.save(update_fields=["status"])

        # Determine renewal dates
        if renewal_start_date is None:
            renewal_start_date = self.end_date + timedelta(days=1)
        if renewal_end_date is None:
            renewal_end_date = renewal_start_date + timedelta(days=365)  # 1 year renewal

        # Determine pricing terms (inherit or override)
        renewal_pricing_mode = new_pricing_mode or self.pricing_mode
        renewal_package_fee = new_package_fee or self.package_fee
        renewal_hourly_rate = new_hourly_rate or self.hourly_rate_default

        # Create renewal engagement
        renewal = ClientEngagement.objects.create(
            firm=self.firm,
            client=self.client,
            contract=self.contract,  # Same contract or could accept new_contract param
            parent_engagement=self,
            version=self.version + 1,
            pricing_mode=renewal_pricing_mode,
            package_fee=renewal_package_fee,
            package_fee_schedule=self.package_fee_schedule,  # Inherit schedule
            allow_hourly_billing=self.allow_hourly_billing,
            hourly_rate_default=renewal_hourly_rate,
            start_date=renewal_start_date,
            end_date=renewal_end_date,
            contracted_value=self.contracted_value,  # Could be recalculated
            status="current",
        )

        # Update old engagement status to 'renewed'
        self.status = "renewed"
        self.save(update_fields=["status"])

        # Create audit event
        from modules.firm.audit import audit

        audit.log_billing_event(
            firm=self.firm,
            action="engagement_renewed",
            actor=None,  # System event, or pass in user if available
            metadata={
                "old_engagement_id": self.id,
                "old_engagement_version": self.version,
                "new_engagement_id": renewal.id,
                "new_engagement_version": renewal.version,
                "old_package_fee": float(self.package_fee or 0),
                "new_package_fee": float(renewal.package_fee or 0),
                "old_hourly_rate": float(self.hourly_rate_default or 0),
                "new_hourly_rate": float(renewal.hourly_rate_default or 0),
                "pricing_mode": renewal.pricing_mode,
            },
        )

        return renewal

    def __str__(self):
        return f"{self.client.company_name} - Engagement v{self.version}"


class ClientComment(models.Model):
    """
    Comments from clients on project tasks.

    Allows client portal users to comment on tasks in their projects.
    Visible to both firm team and client.
    """

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="task_comments", help_text="Client who owns this comment"
    )
    task = models.ForeignKey(
        "projects.Task", on_delete=models.CASCADE, related_name="client_comments", help_text="Task being commented on"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_task_comments",
        help_text="Portal user who wrote this comment",
    )

    # Comment Content
    comment = models.TextField()

    # Attachments (optional)
    has_attachment = models.BooleanField(default=False, help_text="Whether this comment has file attachments")

    # Read Status (for firm team)
    is_read_by_firm = models.BooleanField(default=False, help_text="Whether firm team has read this client comment")
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="read_client_comments",
        help_text="Firm team member who read this comment",
    )
    read_at = models.DateTimeField(null=True, blank=True, help_text="When the comment was read by firm")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_comment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "-created_at"]),
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["is_read_by_firm"]),
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
        Client, on_delete=models.CASCADE, related_name="chat_threads", help_text="Client this thread belongs to"
    )
    date = models.DateField(help_text="Date of this thread (YYYY-MM-DD)")
    is_active = models.BooleanField(default=True, help_text="Whether this is the current active thread")
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When this thread was archived")

    # Statistics
    message_count = models.IntegerField(default=0, help_text="Total messages in this thread")
    last_message_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last message")
    last_message_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_chat_message_threads",
        help_text="User who sent last message",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_chat_thread"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["client", "-date"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["-last_message_at"]),
        ]
        unique_together = [["client", "date"]]

    def __str__(self):
        return f"{self.client.company_name} - Chat Thread {self.date}"


class ClientMessage(models.Model):
    """
    Individual message in a client chat thread.

    Messages are sent between client portal users and firm team members.
    Supports text messages and file attachments.
    """

    MESSAGE_TYPE_CHOICES = [
        ("text", "Text Message"),
        ("file", "File Attachment"),
        ("system", "System Notification"),
    ]

    thread = models.ForeignKey(
        ClientChatThread, on_delete=models.CASCADE, related_name="messages", help_text="Thread this message belongs to"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_client_messages",
        help_text="User who sent this message",
    )
    is_from_client = models.BooleanField(default=False, help_text="Whether sender is a client portal user")

    # Message Content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default="text")
    content = models.TextField(help_text="Message text content")

    # File Attachment (optional)
    attachment_url = models.URLField(blank=True, help_text="S3 URL for file attachment (if message_type=file)")
    attachment_filename = models.CharField(max_length=255, blank=True, help_text="Original filename of attachment")
    attachment_size_bytes = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")

    # Read Status
    is_read = models.BooleanField(default=False, help_text="Whether message has been read by recipient")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When message was read")
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="read_client_messages",
        help_text="User who read this message",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["is_read"]),
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
