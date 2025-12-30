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
            models.Index(fields=["firm", "status"], name="calendar_fir_sta_idx"),
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
            models.Index(fields=["firm", "owner_type", "owner_staff_user"], name="calendar_fir_own_own_idx"),
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
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booking_links",
        help_text="Optional: link to specific client",
    )
    engagement = models.ForeignKey(
        "clients.ClientEngagement",
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
            models.Index(fields=["firm", "status"], name="calendar_fir_sta_idx"),
            models.Index(fields=["slug"], name="calendar_slu_idx"),
            models.Index(fields=["token"], name="calendar_tok_idx"),
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
        "clients.Client",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
        help_text="Client account for this appointment (if applicable)",
    )
    contact = models.ForeignKey(
        "clients.Contact",
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
    calendar_connection = models.ForeignKey(
        "CalendarConnection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="synced_appointments",
        help_text="Calendar connection for external sync (if applicable)",
    )
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
            models.Index(fields=["firm", "staff_user", "start_time"], name="calendar_fir_sta_sta_idx"),
            models.Index(fields=["firm", "account"], name="calendar_fir_acc_idx"),
            models.Index(fields=["firm", "status"], name="calendar_fir_sta_idx"),
            models.Index(fields=["calendar_connection", "external_event_id"], name="calendar_cal_ext_idx"),
        ]
        constraints = [
            # Per docs/16 section 2.2: (connection_id, external_event_id) must be unique
            models.UniqueConstraint(
                fields=["calendar_connection", "external_event_id"],
                condition=models.Q(calendar_connection__isnull=False) & models.Q(external_event_id__gt=""),
                name="unique_external_event_per_connection",
            ),
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
            models.Index(fields=["appointment", "changed_at"], name="calendar_app_cha_idx"),
        ]

    def __str__(self):
        return f"{self.appointment}: {self.from_status} → {self.to_status}"


class CalendarConnection(models.Model):
    """
    CalendarConnection model (per docs/16 section 2.1).

    Represents an authenticated connection to an external calendar provider.
    """

    PROVIDER_CHOICES = [
        ("google", "Google Calendar"),
        ("microsoft", "Microsoft Outlook"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("revoked", "Revoked"),
    ]

    # Identity
    connection_id = models.BigAutoField(primary_key=True)

    # Tenancy
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="calendar_connections",
        help_text="Firm this connection belongs to",
    )

    # Provider and owner (per docs/16 section 2.1)
    provider = models.CharField(
        max_length=20, choices=PROVIDER_CHOICES, help_text="Calendar provider"
    )
    owner_staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_connections",
        help_text="Staff user who owns this connection",
    )

    # OAuth credentials (encrypted at rest)
    credentials_encrypted = models.TextField(
        blank=True, help_text="Encrypted OAuth credentials"
    )
    scopes_granted = models.TextField(
        blank=True, help_text="Scopes granted by the provider"
    )

    # Sync state
    last_sync_cursor = models.TextField(
        blank=True, help_text="Last sync cursor/token from provider"
    )
    last_sync_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", help_text="Connection status"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_connections"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "owner_staff_user", "status"], name="calendar_fir_own_sta_idx"),
            models.Index(fields=["provider", "status"], name="calendar_pro_sta_idx"),
        ]

    def __str__(self):
        return f"{self.provider} - {self.owner_staff_user.username}"


class SyncAttemptLog(models.Model):
    """
    SyncAttemptLog model (per docs/16 section 2.3).

    Records each sync attempt for retry-safety and observability.
    """

    DIRECTION_CHOICES = [
        ("pull", "Pull (External → Internal)"),
        ("push", "Push (Internal → External)"),
    ]

    OPERATION_CHOICES = [
        ("list_changes", "List Changes"),
        ("upsert", "Upsert"),
        ("delete", "Delete"),
        ("resync", "Manual Resync"),
    ]

    STATUS_CHOICES = [
        ("success", "Success"),
        ("fail", "Fail"),
    ]

    ERROR_CLASS_CHOICES = [
        ("transient", "Transient (Retry)"),
        ("non_retryable", "Non-Retryable"),
        ("rate_limited", "Rate Limited"),
    ]

    # Identity
    attempt_id = models.BigAutoField(primary_key=True)

    # Context
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="sync_attempts",
        help_text="Firm for this sync attempt",
    )
    connection = models.ForeignKey(
        CalendarConnection,
        on_delete=models.CASCADE,
        related_name="sync_attempts",
        help_text="Calendar connection for this attempt",
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sync_attempts",
        help_text="Appointment being synced (nullable for list operations)",
    )

    # Attempt details (per docs/16 section 2.3)
    direction = models.CharField(
        max_length=10, choices=DIRECTION_CHOICES, help_text="Sync direction"
    )
    operation = models.CharField(
        max_length=20, choices=OPERATION_CHOICES, help_text="Sync operation"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, help_text="Attempt status"
    )
    error_class = models.CharField(
        max_length=20,
        choices=ERROR_CLASS_CHOICES,
        blank=True,
        help_text="Error classification (if failed)",
    )
    error_summary = models.TextField(
        blank=True, help_text="Redacted error summary (no PII, no content)"
    )

    # Retry tracking (DOC-16.2)
    retry_count = models.IntegerField(
        default=0, help_text="Number of times this operation has been retried"
    )
    next_retry_at = models.DateTimeField(
        null=True, blank=True, help_text="Scheduled time for next retry (if applicable)"
    )
    max_retries_reached = models.BooleanField(
        default=False, help_text="Whether max retry attempts have been exhausted"
    )

    # Observability (per docs/16 section 6)
    correlation_id = models.UUIDField(
        null=True, blank=True, help_text="Correlation ID for tracing"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(
        null=True, blank=True, help_text="Operation duration in milliseconds"
    )

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_sync_attempts"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["firm", "connection", "started_at"], name="calendar_fir_con_sta_idx"),
            models.Index(fields=["status", "error_class"], name="calendar_sta_err_idx"),
            models.Index(fields=["correlation_id"], name="calendar_cor_idx"),
            models.Index(fields=["next_retry_at"], name="calendar_nex_idx"),
            models.Index(fields=["max_retries_reached"], name="calendar_max_idx"),
        ]

    def __str__(self):
        status_icon = "✓" if self.status == "success" else "✗"
        return f"{status_icon} {self.direction} {self.operation} at {self.started_at}"


class MeetingPoll(models.Model):
    """
    Meeting Poll model (Calendly-like feature).

    Allows organizers to propose multiple time slots and let invitees vote
    to find a time that works for everyone.

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("scheduled", "Meeting Scheduled"),
        ("cancelled", "Cancelled"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="meeting_polls",
        help_text="Firm this poll belongs to",
    )

    # Poll details
    title = models.CharField(max_length=500, help_text="Meeting poll title")
    description = models.TextField(blank=True, help_text="Meeting description")
    duration_minutes = models.IntegerField(help_text="Meeting duration in minutes")
    location_mode = models.CharField(
        max_length=20,
        choices=AppointmentType.LOCATION_MODE_CHOICES,
        default="video",
        help_text="How the meeting will be conducted",
    )
    location_details = models.TextField(
        blank=True, help_text="Additional location info"
    )

    # Organizer
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_polls",
        help_text="Staff member who created this poll",
    )

    # Invitees (JSON array of emails or user IDs)
    invitees = models.JSONField(
        default=list,
        help_text="List of invitee emails or user IDs",
    )

    # Proposed time slots (JSON array)
    proposed_slots = models.JSONField(
        default=list,
        help_text="List of proposed time slots {start_time, end_time, timezone}",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
        help_text="Poll status",
    )

    # Voting deadline
    voting_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When voting closes (optional)",
    )

    # Selected slot (when meeting is scheduled)
    selected_slot_index = models.IntegerField(
        null=True,
        blank=True,
        help_text="Index of the selected slot from proposed_slots",
    )
    scheduled_appointment = models.ForeignKey(
        "Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_poll",
        help_text="Appointment created from this poll",
    )

    # Settings
    allow_maybe_votes = models.BooleanField(
        default=True,
        help_text="Allow 'maybe' votes in addition to yes/no",
    )
    require_all_invitees = models.BooleanField(
        default=False,
        help_text="Require all invitees to respond before scheduling",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_meeting_polls"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="calendar_fir_sta_idx"),
            models.Index(fields=["firm", "-created_at"], name="calendar_fir_cre_idx"),
            models.Index(fields=["created_by", "status"], name="calendar_cre_sta_idx"),
        ]

    def __str__(self):
        return f"Poll: {self.title}"

    def get_vote_summary(self):
        """Get vote counts for each proposed slot."""
        from collections import defaultdict

        summary = defaultdict(lambda: {"yes": 0, "no": 0, "maybe": 0})

        for vote in self.votes.all():
            for slot_index, response in enumerate(vote.responses):
                if response in ["yes", "no", "maybe"]:
                    summary[slot_index][response] += 1

        return dict(summary)

    def find_best_slot(self):
        """Find the slot with most 'yes' votes."""
        vote_summary = self.get_vote_summary()
        if not vote_summary:
            return None

        best_slot = max(vote_summary.items(), key=lambda x: x[1]["yes"])
        return best_slot[0]  # Return slot index


class MeetingPollVote(models.Model):
    """
    Vote on a meeting poll.

    Records an invitee's availability for each proposed time slot.

    TIER 0: Belongs to exactly one Firm (via poll relationship).
    """

    VOTE_CHOICES = [
        ("yes", "Yes, I can attend"),
        ("no", "No, I cannot attend"),
        ("maybe", "Maybe / If needed"),
    ]

    # Relationship
    poll = models.ForeignKey(
        MeetingPoll,
        on_delete=models.CASCADE,
        related_name="votes",
        help_text="Poll this vote belongs to",
    )

    # Voter
    voter_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="poll_votes",
        help_text="User who voted (if authenticated)",
    )
    voter_email = models.EmailField(
        help_text="Email of voter (for external invitees)",
    )
    voter_name = models.CharField(
        max_length=255,
        help_text="Name of voter",
    )

    # Responses (JSON array parallel to poll.proposed_slots)
    # Example: ["yes", "no", "maybe", "yes"]
    responses = models.JSONField(
        default=list,
        help_text="Array of responses for each proposed slot",
    )

    # Additional notes
    notes = models.TextField(
        blank=True,
        help_text="Optional notes from voter",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "calendar_meeting_poll_votes"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["poll", "voter_email"], name="calendar_pol_vot_idx"),
            models.Index(fields=["voter_user", "-created_at"], name="calendar_vot_cre_idx"),
        ]
        # One vote per email per poll
        unique_together = [["poll", "voter_email"]]

    def __str__(self):
        return f"Vote by {self.voter_name} on {self.poll.title}"


class MeetingWorkflow(models.Model):
    """
    Meeting Workflow (Pre/Post meeting automation).

    Defines automated actions before and after appointments:
    - Pre-meeting reminders
    - Pre-meeting content sharing
    - Post-meeting follow-ups
    - Post-meeting surveys

    TIER 0: Belongs to exactly one Firm (tenant boundary).
    """

    TRIGGER_CHOICES = [
        ("appointment_created", "Appointment Created"),
        ("appointment_confirmed", "Appointment Confirmed"),
        ("appointment_completed", "Appointment Completed"),
        ("appointment_cancelled", "Appointment Cancelled"),
    ]

    ACTION_TYPE_CHOICES = [
        ("send_email", "Send Email"),
        ("send_sms", "Send SMS"),
        ("create_task", "Create Task"),
        ("send_survey", "Send Survey"),
        ("update_crm", "Update CRM"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("archived", "Archived"),
    ]

    # TIER 0: Firm tenancy (REQUIRED)
    firm = models.ForeignKey(
        "firm.Firm",
        on_delete=models.CASCADE,
        related_name="meeting_workflows",
        help_text="Firm this workflow belongs to",
    )

    # Workflow identification
    name = models.CharField(max_length=255, help_text="Workflow name")
    description = models.TextField(blank=True, help_text="Workflow description")

    # Trigger configuration
    trigger = models.CharField(
        max_length=30,
        choices=TRIGGER_CHOICES,
        help_text="When to trigger this workflow",
    )
    appointment_type = models.ForeignKey(
        AppointmentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="workflows",
        help_text="Apply workflow to this appointment type (null = all types)",
    )

    # Timing
    delay_minutes = models.IntegerField(
        default=0,
        help_text="Delay before executing action (minutes, can be negative for 'before' actions)",
    )

    # Action configuration
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        help_text="Type of action to perform",
    )
    action_config = models.JSONField(
        default=dict,
        help_text="Action configuration (email template, SMS text, survey ID, etc.)",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Workflow status",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
    )

    # TIER 0: Managers
    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "calendar_meeting_workflows"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["firm", "status"], name="calendar_fir_sta_idx"),
            models.Index(fields=["firm", "trigger"], name="calendar_fir_tri_idx"),
            models.Index(fields=["appointment_type", "status"], name="calendar_app_sta_idx"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_trigger_display()})"


class MeetingWorkflowExecution(models.Model):
    """
    Tracks execution of meeting workflow actions.

    Records when workflows are triggered and their execution status.

    TIER 0: Belongs to exactly one Firm (via workflow relationship).
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("executing", "Executing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    # Relationships
    workflow = models.ForeignKey(
        MeetingWorkflow,
        on_delete=models.CASCADE,
        related_name="executions",
        help_text="Workflow being executed",
    )
    appointment = models.ForeignKey(
        "Appointment",
        on_delete=models.CASCADE,
        related_name="workflow_executions",
        help_text="Appointment that triggered this workflow",
    )

    # Execution details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Execution status",
    )
    scheduled_for = models.DateTimeField(
        help_text="When this workflow should execute",
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When workflow was executed",
    )

    # Results
    result_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Execution result data (email sent, task created, etc.)",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if execution failed",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "calendar_workflow_executions"
        ordering = ["scheduled_for"]
        indexes = [
            models.Index(fields=["workflow", "status"], name="calendar_wor_sta_idx"),
            models.Index(fields=["appointment", "status"], name="calendar_app_sta_idx"),
            models.Index(fields=["status", "scheduled_for"], name="calendar_sta_sch_idx"),
        ]

    def __str__(self):
        return f"{self.workflow.name} for {self.appointment}"
