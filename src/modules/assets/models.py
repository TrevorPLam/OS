"""
Assets Models: Asset, MaintenanceLog.

Implements asset tracking for consulting firms.
Tracks company-owned equipment, software licenses, and resources.

TIER 0: All assets belong to exactly one Firm for tenant isolation.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from modules.firm.utils import FirmScopedManager


class Asset(models.Model):
    """
    Asset entity.

    Represents company-owned equipment, software, or resources.
    Supports depreciation tracking and assignment to users.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("in_repair", "In Repair"),
        ("retired", "Retired"),
        ("lost", "Lost/Stolen"),
        ("disposed", "Disposed"),
    ]

    CATEGORY_CHOICES = [
        ("computer", "Computer Equipment"),
        ("software", "Software License"),
        ("furniture", "Furniture"),
        ("vehicle", "Vehicle"),
        ("other", "Other"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm", on_delete=models.CASCADE, related_name="assets", help_text="Firm (workspace) this asset belongs to"
    )

    # Asset Details
    asset_tag = models.CharField(max_length=50, help_text="Unique identifier per firm (e.g., barcode, serial number)")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Ownership & Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_assets",
        help_text="The user currently using this asset",
    )

    # Financial Information
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Original purchase price",
    )
    purchase_date = models.DateField()
    vendor = models.CharField(max_length=255, blank=True, help_text="Where was this purchased?")

    # Depreciation
    useful_life_years = models.IntegerField(default=3, help_text="Expected useful life for depreciation calculation")
    salvage_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Expected value at end of useful life",
    )

    # Physical Details (optional)
    manufacturer = models.CharField(max_length=255, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)

    # Location
    location = models.CharField(max_length=255, blank=True, help_text="Physical location (e.g., office, warehouse)")

    # Warranty
    warranty_expiration = models.DateField(null=True, blank=True)

    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "assets_assets"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "asset_tag"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "category", "status"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "assigned_to"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping
        ]
        # TIER 0: Asset tags must be unique within a firm (not globally)
        unique_together = [["firm", "asset_tag"]]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"


class MaintenanceLog(models.Model):
    """
    MaintenanceLog entity.

    Tracks maintenance, repairs, and servicing of assets.
    Helps with cost tracking and maintenance scheduling.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    Firm is inherited through Asset, but included directly for efficient queries.
    """

    MAINTENANCE_TYPE_CHOICES = [
        ("repair", "Repair"),
        ("preventive", "Preventive Maintenance"),
        ("upgrade", "Upgrade"),
        ("inspection", "Inspection"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    # TIER 0: Firm tenancy (REQUIRED for efficient queries)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="maintenance_logs",
        help_text="Firm (workspace) this maintenance log belongs to",
    )

    # Relationships
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="maintenance_logs")

    # Maintenance Details
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    description = models.TextField(help_text="What maintenance was performed?")

    # Timeline
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)

    # Service Provider
    performed_by = models.CharField(max_length=255, help_text="Technician name or company")
    vendor = models.CharField(max_length=255, blank=True, help_text="Service provider company")

    # Cost
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Cost of maintenance/repair",
    )

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_maintenance_logs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries

    class Meta:
        db_table = "assets_maintenance_logs"
        ordering = ["-scheduled_date", "-created_at"]
        indexes = [
            models.Index(fields=["firm", "asset", "status"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "scheduled_date"]),  # TIER 0: Firm scoping
            models.Index(fields=["firm", "status"]),  # TIER 0: Firm scoping
        ]

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.maintenance_type} ({self.scheduled_date})"
