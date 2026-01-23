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


