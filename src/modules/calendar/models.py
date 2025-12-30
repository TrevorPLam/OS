"""
Calendar Models.

Implements appointment types, availability profiles, booking links, and appointments.
Complies with docs/34 CALENDAR_SPEC.
"""

import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from modules.firm.utils import FirmScopedManager


class AppointmentType(models.Model):
    """
    AppointmentType model (per docs/34 section 2.1).

    Defines a bookable meeting type with duration, buffers, and routing policy.
    """

    LOCATION_MODE_CHOICES = [
        ("video", "Video Call"),
        ("phone", "Phone Call"),
        ("in_person", "In Person"),
        ("custom", "Custom"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    # Identity
    appointment_type_id = models.BigAutoField(primary_key=True)

    # Tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="appointment_types",
        help_text="Firm this appointment type belongs to",
    )

    # Basic info
    name = models.CharField(max_length=255, help_text="Display name for this appointment type")
    description = models.TextField(blank=True, help_text="Description shown to bookers")

    # Duration and buffers (per docs/34 section 2.1)
    duration_minutes = models.IntegerField(help_text="Meeting duration in minutes")
    buffer_before_minutes = models.IntegerField(
        default=0, help_text="Buffer time before meeting (minutes)"
    )
    buffer_after_minutes = models.IntegerField(
        default=0, help_text="Buffer time after meeting (minutes)"
    )

    # Location
    location_mode = models.CharField(
        max_length=20,
        choices=LOCATION_MODE_CHOICES,
        default="video",
        help_text="How the meeting will be conducted",
    )
    location_details = models.TextField(
        blank=True, help_text="Additional location info (e.g., Zoom link, address)"
    )

    # Booking channels (per docs/34 section 2.1)
    allow_portal_booking = models.BooleanField(
        default=True, help_text="Can portal users book this type?"
    )
    allow_staff_booking = models.BooleanField(
        default=True, help_text="Can staff book this type?"
    )
    allow_public_prospect_booking = models.BooleanField(
        default=False, help_text="Can public prospects book this type?"
    )

    # Approval workflow
    requires_approval = models.BooleanField(
        default=False, help_text="Does this appointment need approval before confirmation?"
    )

    # Routing policy (per docs/34 section 2.4)
    ROUTING_POLICY_CHOICES = [
        ("fixed_staff", "Fixed Staff Member"),
        ("round_robin_pool", "Round Robin Pool"),
        ("engagement_owner", "Engagement Owner"),
        ("service_line_owner", "Service Line Owner"),
    ]
    routing_policy = models.CharField(
        max_length=30,
        choices=ROUTING_POLICY_CHOICES,
        default="fixed_staff",
        help_text="How to route appointments to staff",
    )
    fixed_staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fixed_appointment_types",
        help_text="If routing_policy = fixed_staff, this is the assigned user",
    )

    # Intake questions (JSON)
    intake_questions = models.JSONField(
        default=list,
        blank=True,
        help_text="List of intake questions to ask during booking (JSON array)",
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", help_text="Active or inactive"
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_appointment_types",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_appointment_types"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min)"

    def clean(self):
        """Validate AppointmentType data integrity."""
        errors = {}

        if self.duration_minutes <= 0:
            errors["duration_minutes"] = "Duration must be positive"

        if self.buffer_before_minutes < 0:
            errors["buffer_before_minutes"] = "Buffer cannot be negative"

        if self.buffer_after_minutes < 0:
            errors["buffer_after_minutes"] = "Buffer cannot be negative"

        if self.routing_policy == "fixed_staff" and not self.fixed_staff_user:
            errors["fixed_staff_user"] = "Fixed staff routing requires a staff user"

        if errors:
            raise ValidationError(errors)


class AvailabilityProfile(models.Model):
    """
    AvailabilityProfile model (per docs/34 section 2.2).

    Defines availability rules for a staff user.
    """

    OWNER_TYPE_CHOICES = [
        ("staff", "Staff Member"),
        ("team", "Team Pool"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    # Identity
    availability_profile_id = models.BigAutoField(primary_key=True)

    # Tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="availability_profiles",
        help_text="Firm this profile belongs to",
    )

    # Owner (per docs/34 section 2.2)
    owner_type = models.CharField(
        max_length=20, choices=OWNER_TYPE_CHOICES, default="staff", help_text="Staff or team"
    )
    owner_staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="availability_profiles",
        help_text="If owner_type = staff, this is the user",
    )
    owner_team_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="If owner_type = team, this is the team name",
    )

    # Basic info
    name = models.CharField(max_length=255, help_text="Profile name")
    timezone = models.CharField(
        max_length=100, default="UTC", help_text="Timezone for availability computation"
    )

    # Weekly hours (JSON: {day: [{start, end}]} per docs/34 section 2.2)
    weekly_hours = models.JSONField(
        default=dict,
        help_text="Weekly availability by day (JSON: {monday: [{start: '09:00', end: '17:00'}], ...})",
    )

    # Exceptions (dates off, holidays) (JSON array)
    exceptions = models.JSONField(
        default=list,
        help_text="Exception dates (JSON array of {date: 'YYYY-MM-DD', reason: 'Holiday'})",
    )

    # Booking constraints (per docs/34 section 2.2)
    min_notice_minutes = models.IntegerField(
        default=60, help_text="Minimum notice required before booking (minutes)"
    )
    max_future_days = models.IntegerField(
        default=60, help_text="Maximum days in advance for booking"
    )
    slot_rounding_minutes = models.IntegerField(
        default=15, help_text="Round slots to nearest N minutes"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", help_text="Active or inactive"
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_availability_profiles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_availability_profiles"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "owner_type", "owner_staff_user"]),
        ]

    def __str__(self):
        if self.owner_type == "staff" and self.owner_staff_user:
            return f"{self.name} ({self.owner_staff_user.username})"
        return f"{self.name} (Team: {self.owner_team_name})"

    def clean(self):
        """Validate AvailabilityProfile data integrity."""
        errors = {}

        if self.owner_type == "staff" and not self.owner_staff_user:
            errors["owner_staff_user"] = "Staff owner requires a staff user"

        if self.owner_type == "team" and not self.owner_team_name:
            errors["owner_team_name"] = "Team owner requires a team name"

        if self.min_notice_minutes < 0:
            errors["min_notice_minutes"] = "Min notice cannot be negative"

        if self.max_future_days <= 0:
            errors["max_future_days"] = "Max future days must be positive"

        if self.slot_rounding_minutes <= 0:
            errors["slot_rounding_minutes"] = "Slot rounding must be positive"

        if errors:
            raise ValidationError(errors)


class BookingLink(models.Model):
    """
    BookingLink model (per docs/34 section 2.3).

    A shareable booking surface that binds appointment type and availability.
    """

    VISIBILITY_CHOICES = [
        ("portal_only", "Portal Only"),
        ("staff_only", "Staff Only"),
        ("public", "Public"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    # Identity
    booking_link_id = models.BigAutoField(primary_key=True)

    # Tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="booking_links",
        help_text="Firm this link belongs to",
    )

    # Bindings (per docs/34 section 2.3)
    appointment_type = models.ForeignKey(
        AppointmentType,
        on_delete=models.CASCADE,
        related_name="booking_links",
        help_text="Appointment type for this link",
    )
    availability_profile = models.ForeignKey(
        AvailabilityProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="booking_links",
        help_text="Availability profile (optional; used for routing)",
    )

    # Optional context
    account = models.ForeignKey(
        "crm.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_links",
        help_text="Optional: link to specific account",
    )
    engagement = models.ForeignKey(
        "crm.Engagement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_links",
        help_text="Optional: link to specific engagement",
    )

    # Visibility and access (per docs/34 section 2.3)
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default="portal_only",
        help_text="Who can access this link",
    )
    slug = models.SlugField(
        max_length=100, unique=True, help_text="URL slug for this booking link"
    )
    token = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text="Unique token for security"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", help_text="Active or inactive"
    )

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_booking_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_booking_links"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["token"]),
        ]

    def __str__(self):
        return f"{self.slug} - {self.appointment_type.name}"


class Appointment(models.Model):
    """
    Appointment model.

    Represents a scheduled appointment (internal authority per docs/34 section 6).
    """

    STATUS_CHOICES = [
        ("requested", "Requested (Needs Approval)"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
    ]

    # Identity
    appointment_id = models.BigAutoField(primary_key=True)

    # Tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="appointments",
        help_text="Firm this appointment belongs to",
    )

    # Type and link
    appointment_type = models.ForeignKey(
        AppointmentType,
        on_delete=models.PROTECT,
        related_name="appointments",
        help_text="Appointment type",
    )
    booking_link = models.ForeignKey(
        BookingLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        help_text="Booking link used (if applicable)",
    )

    # Participants
    staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="staff_appointments",
        help_text="Staff member for this appointment",
    )
    account = models.ForeignKey(
        "crm.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        help_text="Account for this appointment (if applicable)",
    )
    contact = models.ForeignKey(
        "crm.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        help_text="Contact for this appointment (if applicable)",
    )

    # Timing (internal authority per docs/34 section 6)
    start_time = models.DateTimeField(help_text="Appointment start time (UTC)")
    end_time = models.DateTimeField(help_text="Appointment end time (UTC)")
    timezone = models.CharField(
        max_length=100, default="UTC", help_text="Timezone for display"
    )

    # Intake responses (JSON)
    intake_responses = models.JSONField(
        default=dict, blank=True, help_text="Responses to intake questions (JSON)"
    )

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="confirmed", help_text="Appointment status"
    )
    status_reason = models.TextField(
        blank=True, help_text="Reason for status (e.g., cancellation reason)"
    )

    # External sync reference (for docs/16 CALENDAR_SYNC_SPEC)
    external_event_id = models.CharField(
        max_length=512,
        blank=True,
        help_text="External calendar event ID (if synced)",
    )

    # Audit
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="booked_appointments",
        help_text="User who booked this appointment",
    )
    booked_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_appointments"
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["firm", "staff_user", "start_time"]),
            models.Index(fields=["firm", "account"]),
            models.Index(fields=["firm", "status"]),
            models.Index(fields=["external_event_id"]),
        ]

    def __str__(self):
        return f"{self.appointment_type.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        """Validate Appointment data integrity."""
        errors = {}

        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                errors["end_time"] = "End time must be after start time"

            # Check that duration matches appointment type
            expected_duration_minutes = self.appointment_type.duration_minutes
            actual_duration_minutes = int((self.end_time - self.start_time).total_seconds() / 60)
            if actual_duration_minutes != expected_duration_minutes:
                errors["end_time"] = (
                    f"Duration must be {expected_duration_minutes} minutes "
                    f"(got {actual_duration_minutes} minutes)"
                )

        if errors:
            raise ValidationError(errors)


class AppointmentStatusHistory(models.Model):
    """
    AppointmentStatusHistory model.

    Tracks status changes for appointments (audit trail).
    """

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="status_history",
        help_text="Appointment for this status change",
    )
    from_status = models.CharField(max_length=20, help_text="Previous status")
    to_status = models.CharField(max_length=20, help_text="New status")
    reason = models.TextField(blank=True, help_text="Reason for status change")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who changed the status",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "calendar_appointment_status_history"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["appointment", "changed_at"]),
        ]

    def __str__(self):
        return f"{self.appointment}: {self.from_status} → {self.to_status}"
