"""
Clients Models - Post-Sale Client Management

This module contains all post-sale client entities.
Clients are created when a Proposal is accepted in the CRM module.

TIER 0: All clients MUST belong to exactly one Firm for tenant isolation.
TIER 2.6: Organizations allow optional cross-client collaboration within a firm.
"""

from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from modules.core.validators import validate_safe_url
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
            models.Index(fields=["firm", "name"]),  # TIER 0: Firm scoping, name="clients_fir_nam_idx")
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
    # SECURITY: company_name is unique per firm, not globally (ASSESS-D4.4b)
    company_name = models.CharField(max_length=255)
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
    website = models.URLField(blank=True, validators=[validate_safe_url])
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
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping, name="clients_fir_sta_idx")
            models.Index(fields=["firm", "-created_at"]),  # TIER 0: Firm scoping, name="clients_fir_cre_idx")
            models.Index(fields=["organization"]),  # TIER 2.6: Org scoping, name="clients_org_idx")
            models.Index(fields=["account_manager"], name="clients_acc_idx"),
            models.Index(fields=["company_name"], name="clients_com_idx"),
        ]
        # TIER 0: Company names must be unique within a firm (not globally)
        unique_together = [["firm", "company_name"]]

    def __str__(self):
        return f"{self.company_name} ({self.firm.name})"

    def clean(self):
        """
        Validate Client data integrity.

        Validates:
        - Organization firm consistency: organization.firm == self.firm
        - Numeric constraints: employee_count >= 0
        - Autopay consistency: autopay_enabled requires payment_method_id
        - Retainer balance non-negative
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Organization firm consistency
        if self.organization_id and self.firm_id:
            if hasattr(self, "organization") and self.organization.firm_id != self.firm_id:
                errors["organization"] = "Client's organization must belong to the same firm."

        # Employee count validation
        if self.employee_count is not None and self.employee_count < 0:
            errors["employee_count"] = "Employee count cannot be negative."

        # Autopay consistency
        if self.autopay_enabled and not self.autopay_payment_method_id:
            errors["autopay_payment_method_id"] = "Payment method is required when autopay is enabled."

        # Retainer balance non-negative
        if self.retainer_balance < 0:
            errors["retainer_balance"] = "Retainer balance cannot be negative."
        if self.retainer_hours_balance < 0:
            errors["retainer_hours_balance"] = "Retainer hours balance cannot be negative."

        if errors:
            raise ValidationError(errors)


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
            models.Index(fields=["client", "-created_at"], name="clients_cli_cre_idx"),
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
            models.Index(fields=["client", "-start_date"], name="clients_cli_sta_idx"),
            models.Index(fields=["status"], name="clients_sta_idx"),
            models.Index(fields=["firm", "status"]),  # TIER 4: Firm scoping, name="clients_fir_sta_idx")
            models.Index(fields=["firm", "-start_date"]),  # TIER 4: Firm scoping, name="clients_fir_sta_idx")
        ]
        unique_together = [["client", "version"]]

    def __str__(self):
        return f"{self.client.company_name} - Engagement v{self.version}"

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

    def clean(self):
        """
        Validate ClientEngagement data integrity.

        Validates:
        - Date range: start_date < end_date
        - Actual end date: actual_end_date >= start_date (if set)
        - Firm consistency: client.firm == self.firm (if firm manually set)
        - Pricing mode invariants (from save method)
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Date range validation
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            errors["end_date"] = "End date must be after start date."

        # Actual end date validation
        if self.actual_end_date and self.start_date and self.actual_end_date < self.start_date:
            errors["actual_end_date"] = "Actual end date cannot be before start date."

        # Firm consistency (if manually set)
        if self.firm_id and self.client_id:
            if hasattr(self, "client") and self.client.firm_id != self.firm_id:
                errors["firm"] = "Engagement firm must match client's firm."

        # Validate pricing mode requirements (duplicated validation, also in save)
        if self.pricing_mode in ["package", "mixed"] and not self.package_fee:
            errors["package_fee"] = f"Package fee is required for pricing mode '{self.pricing_mode}'."

        if self.pricing_mode in ["hourly", "mixed"] and not self.hourly_rate_default:
            errors["hourly_rate_default"] = f"Hourly rate is required for pricing mode '{self.pricing_mode}'."

        if errors:
            raise ValidationError(errors)

    def renew(
        self,
        new_package_fee: Decimal | None = None,
        new_hourly_rate: Decimal | None = None,
        new_pricing_mode: str | None = None,
        renewal_start_date: date | None = None,
        renewal_end_date: date | None = None,
    ) -> "ClientEngagement":
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
                "old_package_fee": str(self.package_fee or 0),  # Maintain precision as string
                "new_package_fee": str(renewal.package_fee or 0),
                "old_hourly_rate": str(self.hourly_rate_default or 0),
                "new_hourly_rate": str(renewal.hourly_rate_default or 0),
                "pricing_mode": renewal.pricing_mode,
            },
        )

        return renewal


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
            models.Index(fields=["task", "-created_at"], name="clients_tas_cre_idx"),
            models.Index(fields=["client", "-created_at"], name="clients_cli_cre_idx"),
            models.Index(fields=["is_read_by_firm"], name="clients_is__idx"),
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
            models.Index(fields=["client", "-date"], name="clients_cli_dat_idx"),
            models.Index(fields=["is_active"], name="clients_is__idx"),
            models.Index(fields=["-last_message_at"], name="clients_las_idx"),
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
            models.Index(fields=["thread", "created_at"], name="clients_thr_cre_idx"),
            models.Index(fields=["sender", "-created_at"], name="clients_sen_cre_idx"),
            models.Index(fields=["is_read"], name="clients_is__idx"),
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


class Contact(models.Model):
    """
    Individual contact person associated with a client.

    Represents a specific person at a client organization who
    can interact with the firm (e.g., through SMS, portal, email).

    TIER 0: Belongs to exactly one Firm (via client relationship).
    """

    # Client relationship
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="contacts",
        help_text="Client this contact belongs to",
    )

    # Personal Information
    first_name = models.CharField(max_length=100, help_text="Contact's first name")
    last_name = models.CharField(max_length=100, help_text="Contact's last name")
    email = models.EmailField(help_text="Contact's email address")
    phone = models.CharField(max_length=50, blank=True, help_text="Contact's phone number")
    mobile_phone = models.CharField(max_length=50, blank=True, help_text="Contact's mobile phone number")

    # Professional Information
    job_title = models.CharField(max_length=200, blank=True, help_text="Job title at the client organization")
    department = models.CharField(max_length=100, blank=True, help_text="Department within the organization")

    # Contact Preferences
    is_primary_contact = models.BooleanField(
        default=False, help_text="Whether this is the primary contact for the client"
    )
    can_approve_invoices = models.BooleanField(default=False, help_text="Can approve invoices on behalf of client")
    receives_billing_emails = models.BooleanField(default=False, help_text="Receives billing-related emails")
    receives_project_updates = models.BooleanField(default=True, help_text="Receives project update notifications")

    # Portal Access
    portal_user = models.ForeignKey(
        ClientPortalUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_profile",
        help_text="Associated portal user account (if any)",
    )

    # Communication Preferences
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("email", "Email"),
            ("phone", "Phone"),
            ("sms", "SMS"),
            ("portal", "Portal"),
        ],
        default="email",
        help_text="Preferred method of contact",
    )
    opt_out_marketing = models.BooleanField(default=False, help_text="Opted out of marketing communications")
    opt_out_sms = models.BooleanField(default=False, help_text="Opted out of SMS communications")

    # Status
    is_active = models.BooleanField(default=True, help_text="Whether this contact is active")

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_contacts",
        help_text="User who created this contact",
    )
    notes = models.TextField(blank=True, help_text="Internal notes about this contact")

    class Meta:
        db_table = "clients_contact"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["client", "is_active"], name="clients_contact_cli_act_idx"),
            models.Index(fields=["client", "is_primary_contact"], name="clients_contact_cli_pri_idx"),
            models.Index(fields=["email"], name="clients_contact_email_idx"),
            models.Index(fields=["phone"], name="clients_contact_phone_idx"),
        ]
        unique_together = [["client", "email"]]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client.company_name})"

    @property
    def full_name(self):
        """Return contact's full name."""
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        """
        Validate Contact data integrity.

        Validates:
        - Portal user consistency: portal_user.client == self.client
        - Only one primary contact per client
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Portal user consistency
        if self.portal_user_id and self.client_id:
            if hasattr(self, "portal_user") and self.portal_user.client_id != self.client_id:
                errors["portal_user"] = "Contact's portal user must belong to the same client."

        # Ensure only one primary contact per client
        if self.is_primary_contact and self.client_id:
            existing_primary = (
                Contact.objects.filter(client=self.client, is_primary_contact=True).exclude(pk=self.pk).first()
            )
            if existing_primary:
                errors["is_primary_contact"] = (
                    f"Client already has a primary contact: {existing_primary.full_name}"
                )

        if errors:
            raise ValidationError(errors)


class EngagementLine(models.Model):
    """
    Line item within a client engagement.

    Represents a specific service, deliverable, or product within an engagement.
    Used for detailed billing, tracking, and delivery template instantiation.

    TIER 0: Belongs to exactly one Firm (via engagement relationship).
    """

    LINE_TYPE_CHOICES = [
        ("service", "Service"),
        ("product", "Product"),
        ("deliverable", "Deliverable"),
        ("retainer", "Retainer"),
        ("milestone", "Milestone"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("on_hold", "On Hold"),
        ("cancelled", "Cancelled"),
    ]

    # TIER 0: Firm tenancy (auto-populated from engagement)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="engagement_lines",
        help_text="Firm this engagement line belongs to (auto-populated from engagement)",
    )

    # Engagement relationship
    engagement = models.ForeignKey(
        ClientEngagement,
        on_delete=models.CASCADE,
        related_name="lines",
        help_text="Parent engagement this line belongs to",
    )

    # Line item details
    line_number = models.IntegerField(help_text="Line number within the engagement (1, 2, 3...)")
    line_type = models.CharField(max_length=20, choices=LINE_TYPE_CHOICES, default="service", help_text="Type of line")
    description = models.CharField(max_length=500, help_text="Description of this line item")
    detailed_description = models.TextField(blank=True, help_text="Detailed description or scope")

    # Service/Product code (optional)
    service_code = models.CharField(max_length=100, blank=True, help_text="Service or product code")

    # Quantity and pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Quantity (hours, units, etc.)",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Price per unit",
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Total price (quantity * unit_price)",
    )

    # Discount (optional)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Discount percentage (0-100)",
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Discount amount (calculated from discount_percent or manual)",
    )

    # Final amount
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Net amount after discount (total_price - discount_amount)",
    )

    # Timeline
    start_date = models.DateField(null=True, blank=True, help_text="When work on this line starts")
    end_date = models.DateField(null=True, blank=True, help_text="When work on this line ends")

    # Status tracking
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", help_text="Current status of this line"
    )
    completion_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Completion percentage (0-100)",
    )

    # Delivery template linkage (optional)
    delivery_template_code = models.CharField(
        max_length=100, blank=True, help_text="Delivery template code (if applicable)"
    )

    # Billing
    is_billable = models.BooleanField(default=True, help_text="Whether this line is billable to the client")
    invoice_schedule = models.CharField(
        max_length=50, blank=True, help_text="Invoice schedule (e.g., 'Monthly', 'Upon Completion', 'Milestone')"
    )

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Internal notes about this line")

    class Meta:
        db_table = "clients_engagement_line"
        ordering = ["engagement", "line_number"]
        indexes = [
            models.Index(fields=["firm", "engagement"], name="clients_engline_frm_eng_idx"),
            models.Index(fields=["engagement", "line_number"], name="clients_engline_eng_lnum_idx"),
            models.Index(fields=["engagement", "status"], name="clients_engline_eng_stat_idx"),
            models.Index(fields=["service_code"], name="clients_engline_svc_idx"),
            models.Index(fields=["delivery_template_code"], name="clients_engline_tpl_idx"),
        ]
        unique_together = [["engagement", "line_number"]]

    def __str__(self):
        return f"{self.engagement} - Line {self.line_number}: {self.description}"

    def save(self, *args, **kwargs):
        """
        Auto-calculate derived fields and auto-populate firm.

        Calculations:
        - total_price = quantity * unit_price
        - discount_amount = total_price * (discount_percent / 100)
        - net_amount = total_price - discount_amount

        Auto-population:
        - firm is auto-populated from engagement.firm if not set
        """
        # Auto-populate firm from engagement
        if not self.firm_id and self.engagement_id:
            self.firm = self.engagement.firm

        # Calculate total_price
        self.total_price = self.quantity * self.unit_price

        # Calculate discount_amount if discount_percent is set
        if self.discount_percent > 0:
            self.discount_amount = self.total_price * (self.discount_percent / Decimal("100"))

        # Calculate net_amount
        self.net_amount = self.total_price - self.discount_amount

        super().save(*args, **kwargs)

    def clean(self):
        """
        Validate EngagementLine data integrity.

        Validates:
        - Date range: start_date <= end_date (if both set)
        - Firm consistency: engagement.firm == self.firm (if firm manually set)
        - Discount validation: discount_percent <= 100
        - Completion percentage: 0 <= completion_percentage <= 100
        """
        from django.core.exceptions import ValidationError

        errors = {}

        # Date range validation
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors["end_date"] = "End date must be on or after start date."

        # Firm consistency (if manually set)
        if self.firm_id and self.engagement_id:
            if hasattr(self, "engagement") and self.engagement.firm_id != self.firm_id:
                errors["firm"] = "Engagement line firm must match engagement's firm."

        # Discount validation
        if self.discount_percent > 100:
            errors["discount_percent"] = "Discount percentage cannot exceed 100%."

        if errors:
            raise ValidationError(errors)
