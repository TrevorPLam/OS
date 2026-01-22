import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager
from .clients import Client


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

    # Client relationship
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="engagements",
        help_text="Client this engagement belongs to",
    )

    # Contract reference
    contract = models.ForeignKey(
        "crm.Contract",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="engagements",
        help_text="Contract this engagement is based on",
    )

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


