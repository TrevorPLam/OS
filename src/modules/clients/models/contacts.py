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


class ContactManager(models.Manager):
    """Custom manager for Contact model with state-based filtering."""

    def active(self):
        """Get all active contacts."""
        return self.filter(status='active')

    def unsubscribed(self):
        """Get all unsubscribed contacts."""
        return self.filter(status='unsubscribed')

    def bounced(self):
        """Get all bounced contacts."""
        return self.filter(status='bounced')

    def unconfirmed(self):
        """Get all unconfirmed contacts."""
        return self.filter(status='unconfirmed')

    def inactive(self):
        """Get all inactive contacts."""
        return self.filter(status='inactive')

    def can_receive_emails(self):
        """Get contacts that can receive emails (active and not bounced/unsubscribed)."""
        return self.filter(status__in=['active', 'unconfirmed'])

    def can_receive_marketing(self):
        """Get contacts that can receive marketing emails."""
        return self.filter(
            status='active',
            opt_out_marketing=False,
        )


class Contact(models.Model):
    """
    Individual contact person associated with a client.

    Represents a specific person at a client organization who
    can interact with the firm (e.g., through SMS, portal, email).

    TIER 0: Belongs to exactly one Firm (via client relationship).
    """

    # Contact state choices for lifecycle management
    STATUS_ACTIVE = "active"
    STATUS_UNSUBSCRIBED = "unsubscribed"
    STATUS_BOUNCED = "bounced"
    STATUS_UNCONFIRMED = "unconfirmed"
    STATUS_INACTIVE = "inactive"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_UNSUBSCRIBED, "Unsubscribed"),
        (STATUS_BOUNCED, "Bounced"),
        (STATUS_UNCONFIRMED, "Unconfirmed"),
        (STATUS_INACTIVE, "Inactive"),
    ]

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

    # Location Information (T-010)
    country = models.CharField(max_length=100, blank=True, help_text="Country for this contact")
    state = models.CharField(max_length=100, blank=True, help_text="State or province for this contact")
    city = models.CharField(max_length=100, blank=True, help_text="City for this contact")
    postal_code = models.CharField(max_length=20, blank=True, help_text="Postal or ZIP code for this contact")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude for geographic filtering",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude for geographic filtering",
    )

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

    # Status and Lifecycle
    is_active = models.BooleanField(default=True, help_text="Whether this contact is active (deprecated, use status)")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text="Current lifecycle state of the contact",
    )
    status_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the status was last changed",
    )
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_status_changes",
        help_text="User who last changed the status",
    )
    status_reason = models.TextField(
        blank=True,
        help_text="Reason for status change (e.g., bounce reason, unsubscribe reason)",
    )

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

    # Managers
    objects = ContactManager()  # Custom manager with state-based filtering

    class Meta:
        db_table = "clients_contact"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["client", "is_active"], name="clients_contact_cli_act_idx"),
            models.Index(fields=["client", "is_primary_contact"], name="clients_contact_cli_pri_idx"),
            models.Index(fields=["email"], name="clients_contact_email_idx"),
            models.Index(fields=["phone"], name="clients_contact_phone_idx"),
            models.Index(fields=["client", "status"], name="clients_contact_cli_sta_idx"),
            models.Index(fields=["status"], name="clients_contact_status_idx"),
            models.Index(fields=["country"], name="clients_contact_country_idx"),
            models.Index(fields=["state"], name="clients_contact_state_idx"),
            models.Index(fields=["city"], name="clients_contact_city_idx"),
            models.Index(fields=["postal_code"], name="clients_contact_postal_idx"),
        ]
        unique_together = [["client", "email"]]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.client.company_name})"

    @property
    def full_name(self):
        """Return contact's full name."""
        return f"{self.first_name} {self.last_name}"

    def change_status(self, new_status, reason="", changed_by=None):
        """
        Change contact status with proper state transition tracking.

        Args:
            new_status: New status value (one of STATUS_CHOICES)
            reason: Reason for status change
            changed_by: User making the change (if any)

        Returns:
            bool: True if status was changed, False if already in that status
        """
        from django.utils import timezone

        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")

        if self.status == new_status:
            return False  # Already in this status

        old_status = self.status
        self.status = new_status
        self.status_changed_at = timezone.now()
        self.status_changed_by = changed_by
        self.status_reason = reason

        # Update is_active for backwards compatibility
        self.is_active = new_status == self.STATUS_ACTIVE

        return True

    def mark_as_unsubscribed(self, reason="", changed_by=None):
        """Mark contact as unsubscribed from communications."""
        self.change_status(self.STATUS_UNSUBSCRIBED, reason=reason, changed_by=changed_by)
        self.opt_out_marketing = True

    def mark_as_bounced(self, reason="", changed_by=None):
        """Mark contact email as bounced."""
        self.change_status(self.STATUS_BOUNCED, reason=reason, changed_by=changed_by)

    def mark_as_inactive(self, reason="", changed_by=None):
        """Mark contact as inactive."""
        self.change_status(self.STATUS_INACTIVE, reason=reason, changed_by=changed_by)

    def reactivate(self, reason="", changed_by=None):
        """Reactivate an inactive or unconfirmed contact."""
        if self.status in [self.STATUS_INACTIVE, self.STATUS_UNCONFIRMED]:
            self.change_status(self.STATUS_ACTIVE, reason=reason, changed_by=changed_by)
        elif self.status == self.STATUS_BOUNCED:
            # Can reactivate bounced if email is fixed
            self.change_status(self.STATUS_ACTIVE, reason=reason, changed_by=changed_by)

    def confirm_email(self, changed_by=None):
        """Confirm contact's email address (move from unconfirmed to active)."""
        if self.status == self.STATUS_UNCONFIRMED:
            self.change_status(self.STATUS_ACTIVE, reason="Email confirmed", changed_by=changed_by)
    

class ContactImport(models.Model):
    """
    Track contact import operations for audit and error tracking.
    
    TIER 0: Belongs to exactly one Firm (via firm relationship).
    """
    
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_PARTIALLY_COMPLETED = "partially_completed"
    
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_PARTIALLY_COMPLETED, "Partially Completed"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="contact_imports",
        help_text="Firm this import belongs to",
    )
    
    # Import metadata
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Current status of the import",
    )
    filename = models.CharField(
        max_length=255,
        help_text="Original filename of the imported file",
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Storage path of the uploaded file",
    )
    
    # Statistics
    total_rows = models.IntegerField(
        default=0,
        help_text="Total number of rows in the import file",
    )
    successful_imports = models.IntegerField(
        default=0,
        help_text="Number of contacts successfully imported",
    )
    failed_imports = models.IntegerField(
        default=0,
        help_text="Number of contacts that failed to import",
    )
    skipped_rows = models.IntegerField(
        default=0,
        help_text="Number of rows skipped (headers, duplicates, etc.)",
    )
    duplicates_found = models.IntegerField(
        default=0,
        help_text="Number of duplicate contacts detected",
    )
    
    # Field mapping configuration (JSON)
    field_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Field mapping configuration from CSV columns to Contact model fields",
    )
    
    # Duplicate handling strategy
    DUPLICATE_SKIP = "skip"
    DUPLICATE_UPDATE = "update"
    DUPLICATE_CREATE_NEW = "create_new"
    
    DUPLICATE_STRATEGY_CHOICES = [
        (DUPLICATE_SKIP, "Skip Duplicates"),
        (DUPLICATE_UPDATE, "Update Existing"),
        (DUPLICATE_CREATE_NEW, "Create New"),
    ]
    
    duplicate_strategy = models.CharField(
        max_length=20,
        choices=DUPLICATE_STRATEGY_CHOICES,
        default=DUPLICATE_SKIP,
        help_text="How to handle duplicate contacts",
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="General error message if import failed",
    )
    error_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed error information per row",
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_contact_imports",
        help_text="User who initiated this import",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the import was completed",
    )
    
    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries
    
    class Meta:
        db_table = "clients_contact_import"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="clients_cimp_fir_sta_idx"),
            models.Index(fields=["firm", "-created_at"], name="clients_cimp_fir_cre_idx"),
            models.Index(fields=["created_by"], name="clients_cimp_cby_idx"),
        ]
    
    def __str__(self):
        return f"Import {self.id}: {self.filename} - {self.status}"
    
    def mark_as_processing(self):
        """Mark import as currently processing."""
        self.status = self.STATUS_PROCESSING
        self.save(update_fields=["status", "updated_at"])
    
    def mark_as_completed(self):
        """Mark import as successfully completed."""
        from django.utils import timezone
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])
    
    def mark_as_failed(self, error_message):
        """Mark import as failed with error message."""
        from django.utils import timezone
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at", "updated_at"])
    
    def mark_as_partially_completed(self):
        """Mark import as partially completed (some failures)."""
        from django.utils import timezone
        self.status = self.STATUS_PARTIALLY_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])


class ContactBulkUpdate(models.Model):
    """
    Track bulk update operations on contacts.
    
    TIER 0: Belongs to exactly one Firm (via firm relationship).
    """
    
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]
    
    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="contact_bulk_updates",
        help_text="Firm this bulk update belongs to",
    )
    
    # Update metadata
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Current status of the bulk update",
    )
    operation_type = models.CharField(
        max_length=50,
        help_text="Type of bulk operation (e.g., 'update_status', 'assign_tags')",
    )
    
    # Update configuration
    update_data = models.JSONField(
        default=dict,
        help_text="Data to be updated (field: value pairs)",
    )
    filter_criteria = models.JSONField(
        default=dict,
        help_text="Criteria used to filter contacts for update",
    )
    
    # Statistics
    total_contacts = models.IntegerField(
        default=0,
        help_text="Total number of contacts to be updated",
    )
    successful_updates = models.IntegerField(
        default=0,
        help_text="Number of contacts successfully updated",
    )
    failed_updates = models.IntegerField(
        default=0,
        help_text="Number of contacts that failed to update",
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text="General error message if update failed",
    )
    error_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detailed error information per contact",
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_contact_bulk_updates",
        help_text="User who initiated this bulk update",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the bulk update was completed",
    )
    
    # TIER 0: Managers
    objects = models.Manager()  # Default manager
    firm_scoped = FirmScopedManager()  # Firm-scoped queries
    
    class Meta:
        db_table = "clients_contact_bulk_update"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="clients_cbup_fir_sta_idx"),
            models.Index(fields=["firm", "-created_at"], name="clients_cbup_fir_cre_idx"),
        ]
    
    def __str__(self):
        return f"Bulk Update {self.id}: {self.operation_type} - {self.status}"


