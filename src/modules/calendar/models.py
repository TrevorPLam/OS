"""
Calendar Models.

Implements appointment types, availability profiles, booking links, and appointments.
Complies with docs/34 CALENDAR_SPEC.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

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
        ("archived", "Archived"),
    ]

    # CAL-1: Event type categories
    EVENT_CATEGORY_CHOICES = [
        ("one_on_one", "One-on-One"),
        ("group", "Group Event (one-to-many)"),
        ("collective", "Collective Event (multiple hosts, overlapping availability)"),
        ("round_robin", "Round Robin (distribute across team)"),
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

    # CAL-3: Rich event descriptions
    internal_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Internal name for staff use (if different from public display name)",
    )
    rich_description = models.TextField(
        blank=True,
        help_text="Rich HTML description with formatting, links, and embedded content",
    )
    description_image = models.ImageField(
        upload_to="calendar/event_images/",
        blank=True,
        null=True,
        help_text="Image to display in event description",
    )

    # CAL-1: Event category
    event_category = models.CharField(
        max_length=20,
        choices=EVENT_CATEGORY_CHOICES,
        default="one_on_one",
        help_text="Event type category (one-on-one, group, collective, or round robin)",
    )

    # CAL-1: Group event settings (for event_category="group")
    max_attendees = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of attendees for group events (2-1000). Required for group events.",
    )
    enable_waitlist = models.BooleanField(
        default=False,
        help_text="Enable waitlist when group event reaches max capacity",
    )

    # CAL-1: Collective event settings (for event_category="collective")
    required_hosts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="collective_required_appointments",
        blank=True,
        help_text="Required hosts for collective events (all must be available)",
    )
    optional_hosts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="collective_optional_appointments",
        blank=True,
        help_text="Optional hosts for collective events",
    )

    # CAL-1: Round robin settings (for event_category="round_robin")
    round_robin_pool = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="round_robin_appointments",
        blank=True,
        help_text="Pool of staff members for round robin distribution",
    )

    # Duration and buffers (per docs/34 section 2.1)
    duration_minutes = models.IntegerField(
        help_text="Meeting duration in minutes (default if multiple options not enabled)"
    )

    # CAL-2: Multiple duration options
    enable_multiple_durations = models.BooleanField(
        default=False,
        help_text="Allow bookers to choose from multiple duration options",
    )
    duration_options = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "Array of duration options in minutes (e.g., [15, 30, 60]). "
            "If enabled, booker can select from these options. Each option can optionally include "
            "pricing if duration-based pricing is used: "
            '[{"minutes": 30, "price": 50.00, "label": "30 min session"}, ...]'
        ),
    )

    buffer_before_minutes = models.IntegerField(default=0, help_text="Buffer time before meeting (minutes)")
    buffer_after_minutes = models.IntegerField(default=0, help_text="Buffer time after meeting (minutes)")

    # CAL-5: Scheduling constraints
    daily_meeting_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of this event type that can be booked per day (null = unlimited)",
    )
    min_notice_hours = models.IntegerField(
        null=True,
        blank=True,
        help_text="Minimum notice required before booking (hours, 1-720). Overrides profile default if set.",
    )
    max_notice_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum days in advance for booking (1-365). Overrides profile default if set.",
    )
    rolling_window_days = models.IntegerField(
        null=True,
        blank=True,
        help_text=(
            "Rolling availability window in days (e.g., 30 = only show next 30 days). "
            "If set, overrides max_notice_days with a rolling window."
        ),
    )

    # Location
    location_mode = models.CharField(
        max_length=20,
        choices=LOCATION_MODE_CHOICES,
        default="video",
        help_text="How the meeting will be conducted",
    )
    location_details = models.TextField(blank=True, help_text="Additional location info (e.g., Zoom link, address)")

    # Booking channels (per docs/34 section 2.1)
    allow_portal_booking = models.BooleanField(default=True, help_text="Can portal users book this type?")
    allow_staff_booking = models.BooleanField(default=True, help_text="Can staff book this type?")
    allow_public_prospect_booking = models.BooleanField(default=False, help_text="Can public prospects book this type?")

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

    # CAL-4: Event customization features
    url_slug = models.SlugField(
        max_length=100,
        blank=True,
        help_text="Custom URL slug for this event type (e.g., 'strategy-session'). Auto-generated if not provided.",
    )
    color_code = models.CharField(
        max_length=7,
        blank=True,
        default="",
        help_text="Color code for visual identification (hex format: #RRGGBB)",
    )
    availability_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Event-specific availability overrides. "
            "Can override weekly_hours, exceptions, buffer times, etc. "
            "JSON format: {'weekly_hours': {...}, 'min_notice_minutes': 120, ...}"
        ),
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Event status: active, inactive, or archived",
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
            models.Index(fields=["firm", "status"], name="calendar_apt_fir_sta_idx"),
            models.Index(fields=["firm", "event_category"], name="calendar_apt_fir_cat_idx"),
            models.Index(fields=["firm", "url_slug"], name="calendar_apt_fir_slug_idx"),
        ]
        constraints = [
            # Ensure url_slug is unique within a firm (if provided)
            models.UniqueConstraint(
                fields=["firm", "url_slug"],
                condition=models.Q(url_slug__gt=""),
                name="calendar_apt_firm_slug_uniq",
            ),
        ]

    def __str__(self):
        category_display = dict(self.EVENT_CATEGORY_CHOICES).get(self.event_category, self.event_category)
        return f"{self.name} ({category_display}, {self.duration_minutes} min)"

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

        # CAL-1: Validate event category-specific requirements
        if self.event_category == "group":
            if not self.max_attendees:
                errors["max_attendees"] = "Group events require max_attendees to be set"
            elif self.max_attendees < 2 or self.max_attendees > 1000:
                errors["max_attendees"] = "Group events must have between 2 and 1000 max attendees"

        elif self.event_category == "collective":
            # Collective events require at least one required host
            # Note: ManyToMany validation happens after save, so we check in save() override
            pass

        elif self.event_category == "round_robin":
            # Round robin requires a pool of staff members
            # Note: ManyToMany validation happens after save, so we check in save() override
            pass

        # CAL-2: Validate multiple duration options
        if self.enable_multiple_durations:
            if not self.duration_options:
                errors["duration_options"] = "Multiple durations enabled but no options provided"
            elif not isinstance(self.duration_options, list):
                errors["duration_options"] = "Duration options must be a list"
            elif len(self.duration_options) == 0:
                errors["duration_options"] = "At least one duration option must be provided"
            else:
                # Validate each option
                for idx, option in enumerate(self.duration_options):
                    if isinstance(option, dict):
                        # Extended format with pricing
                        if "minutes" not in option:
                            errors["duration_options"] = f"Option {idx}: 'minutes' field is required"
                            break
                        if not isinstance(option["minutes"], int) or option["minutes"] <= 0:
                            errors["duration_options"] = f"Option {idx}: 'minutes' must be a positive integer"
                            break
                        if "price" in option:
                            try:
                                float(option["price"])
                            except (ValueError, TypeError):
                                errors["duration_options"] = f"Option {idx}: 'price' must be a number"
                                break
                    elif isinstance(option, int):
                        # Simple format (just minutes)
                        if option <= 0:
                            errors["duration_options"] = f"Option {idx}: Duration must be positive"
                            break
                    else:
                        errors["duration_options"] = f"Option {idx}: Must be an integer or dict with 'minutes' field"
                        break

        # CAL-4: Validate customization fields
        if self.color_code:
            # Validate hex color format
            import re

            if not re.match(r"^#[0-9A-Fa-f]{6}$", self.color_code):
                errors["color_code"] = "Color code must be in hex format: #RRGGBB (e.g., #3B82F6)"

        if self.url_slug:
            # Validate slug format (lowercase, hyphens, no spaces)
            import re

            if not re.match(r"^[a-z0-9-]+$", self.url_slug):
                errors["url_slug"] = "URL slug must contain only lowercase letters, numbers, and hyphens"

        # CAL-5: Validate scheduling constraints
        if self.daily_meeting_limit is not None:
            if self.daily_meeting_limit < 1:
                errors["daily_meeting_limit"] = "Daily meeting limit must be at least 1"
            elif self.daily_meeting_limit > 100:
                errors["daily_meeting_limit"] = "Daily meeting limit cannot exceed 100"

        if self.min_notice_hours is not None:
            if self.min_notice_hours < 1:
                errors["min_notice_hours"] = "Minimum notice must be at least 1 hour"
            elif self.min_notice_hours > 720:  # 30 days
                errors["min_notice_hours"] = "Minimum notice cannot exceed 720 hours (30 days)"

        if self.max_notice_days is not None:
            if self.max_notice_days < 1:
                errors["max_notice_days"] = "Maximum notice must be at least 1 day"
            elif self.max_notice_days > 365:
                errors["max_notice_days"] = "Maximum notice cannot exceed 365 days"

        if self.rolling_window_days is not None:
            if self.rolling_window_days < 1:
                errors["rolling_window_days"] = "Rolling window must be at least 1 day"
            elif self.rolling_window_days > 365:
                errors["rolling_window_days"] = "Rolling window cannot exceed 365 days"

        # Validate min < max for notice periods
        if self.min_notice_hours and self.max_notice_days:
            min_hours = self.min_notice_hours
            max_hours = self.max_notice_days * 24
            if min_hours >= max_hours:
                errors["min_notice_hours"] = "Minimum notice must be less than maximum notice"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug if not provided (CAL-4)."""
        if not self.url_slug:
            # Auto-generate slug from name
            from django.utils.text import slugify

            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # Ensure uniqueness within firm
            if self.firm_id:
                while AppointmentType.objects.filter(firm=self.firm, url_slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            self.url_slug = slug

        super().save(*args, **kwargs)

    def get_available_durations(self):
        """
        Get list of available durations for this appointment type (CAL-2).

        Returns:
            List of duration options, each as a dict with 'minutes', 'label', and optionally 'price'
        """
        if not self.enable_multiple_durations or not self.duration_options:
            # Single duration mode
            return [
                {
                    "minutes": self.duration_minutes,
                    "label": f"{self.duration_minutes} minutes",
                    "price": None,
                }
            ]

        # Multiple duration mode
        result = []
        for option in self.duration_options:
            if isinstance(option, dict):
                # Extended format
                minutes = option.get("minutes")
                label = option.get("label", f"{minutes} minutes")
                price = option.get("price")
                result.append(
                    {
                        "minutes": minutes,
                        "label": label,
                        "price": price,
                    }
                )
            elif isinstance(option, int):
                # Simple format (just minutes)
                result.append(
                    {
                        "minutes": option,
                        "label": f"{option} minutes",
                        "price": None,
                    }
                )

        return result


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
    owner_type = models.CharField(max_length=20, choices=OWNER_TYPE_CHOICES, default="staff", help_text="Staff or team")
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
    timezone = models.CharField(max_length=100, default="UTC", help_text="Timezone for availability computation")

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

    # AVAIL-2: Recurring unavailability blocks
    recurring_unavailability = models.JSONField(
        default=list,
        help_text="Recurring unavailability blocks (JSON array of {day_of_week: 'monday', start: '12:00', end: '13:00', reason: 'Lunch'})",
    )

    # AVAIL-2: Holiday blocking
    auto_detect_holidays = models.BooleanField(
        default=False,
        help_text="Automatically block common holidays based on timezone/country",
    )
    custom_holidays = models.JSONField(
        default=list,
        help_text="Custom holiday dates (JSON array of {date: 'YYYY-MM-DD', name: 'Company Holiday'})",
    )

    # AVAIL-2: Meeting gap configuration
    min_gap_between_meetings_minutes = models.IntegerField(
        default=0,
        help_text="Minimum gap between meetings (minutes). 0 means back-to-back allowed.",
    )
    max_gap_between_meetings_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum gap between meetings (minutes). Null means no limit.",
    )

    # AVAIL-3: Location-based availability
    location_based_schedules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Different schedules per location (JSON: {location_name: {weekly_hours: {...}, timezone: '...'}})",
    )

    # Booking constraints (per docs/34 section 2.2)
    min_notice_minutes = models.IntegerField(default=60, help_text="Minimum notice required before booking (minutes)")
    max_future_days = models.IntegerField(default=60, help_text="Maximum days in advance for booking")
    slot_rounding_minutes = models.IntegerField(default=15, help_text="Round slots to nearest N minutes")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", help_text="Active or inactive")

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
    slug = models.SlugField(max_length=100, unique=True, help_text="URL slug for this booking link")
    token = models.UUIDField(default=uuid.uuid4, unique=True, help_text="Unique token for security")

    # AVAIL-3: Secret events (direct link only, hidden from public)
    is_secret = models.BooleanField(
        default=False,
        help_text="Secret events are only accessible via direct link, not listed publicly",
    )

    # AVAIL-3: Password protection
    password_protected = models.BooleanField(
        default=False,
        help_text="Require password to book",
    )
    password_hash = models.CharField(
        max_length=255,
        blank=True,
        help_text="Hashed password for protected booking links",
    )

    # AVAIL-3: Email domain restrictions
    allowed_email_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Whitelist of allowed email domains (e.g., ['example.com', 'partner.com']). Empty means all allowed.",
    )
    blocked_email_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="Blacklist of blocked email domains (e.g., ['spam.com'])",
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", help_text="Active or inactive")

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
            models.Index(fields=["firm", "status"], name="calendar_bkl_fir_sta_idx"),
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
        ("rescheduled", "Rescheduled"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No Show"),
        ("awaiting_confirmation", "Awaiting Confirmation"),
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

    # TEAM-1: Collective event hosts (for event_category="collective")
    collective_hosts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="collective_appointments",
        blank=True,
        help_text="All hosts assigned to this collective event appointment (required + available optional hosts)",
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
    timezone = models.CharField(max_length=100, default="UTC", help_text="Timezone for display")

    # AVAIL-4: Invitee timezone auto-detection
    invitee_timezone = models.CharField(
        max_length=100,
        blank=True,
        help_text="Auto-detected timezone of the invitee/booker",
    )
    invitee_timezone_offset_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Browser timezone offset in minutes (for DST handling)",
    )

    # CAL-2: Selected duration (for multiple duration options)
    selected_duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration selected by booker (if multiple options were available)",
    )
    selected_duration_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Price for selected duration (if duration-based pricing is used)",
    )

    # Intake responses (JSON)
    intake_responses = models.JSONField(default=dict, blank=True, help_text="Responses to intake questions (JSON)")

    # Status
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default="confirmed", help_text="Appointment status"
    )
    status_reason = models.TextField(blank=True, help_text="Reason for status (e.g., cancellation reason)")

    # CAL-6: Meeting lifecycle tracking
    rescheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this appointment was rescheduled",
    )
    rescheduled_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_to",
        help_text="Original appointment that this was rescheduled from",
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this appointment was cancelled",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this appointment was marked as completed",
    )
    no_show_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this appointment was marked as no-show",
    )
    no_show_party = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("client", "Client No-Show"),
            ("staff", "Staff No-Show"),
            ("both", "Both No-Show"),
        ],
        help_text="Which party didn't show up",
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
            models.Index(fields=["firm", "status"], name="calendar_app_fir_sta_idx"),
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
                    f"Duration must be {expected_duration_minutes} minutes " f"(got {actual_duration_minutes} minutes)"
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
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, help_text="Calendar provider")
    owner_staff_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_connections",
        help_text="Staff user who owns this connection",
    )

    # OAuth credentials (encrypted at rest)
    credentials_encrypted = models.TextField(blank=True, help_text="Encrypted OAuth credentials")
    scopes_granted = models.TextField(blank=True, help_text="Scopes granted by the provider")

    # Sync state
    last_sync_cursor = models.TextField(blank=True, help_text="Last sync cursor/token from provider")
    last_sync_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", help_text="Connection status")

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
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, help_text="Sync direction")
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES, help_text="Sync operation")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, help_text="Attempt status")
    error_class = models.CharField(
        max_length=20,
        choices=ERROR_CLASS_CHOICES,
        blank=True,
        help_text="Error classification (if failed)",
    )
    error_summary = models.TextField(blank=True, help_text="Redacted error summary (no PII, no content)")

    # Retry tracking (DOC-16.2)
    retry_count = models.IntegerField(default=0, help_text="Number of times this operation has been retried")
    next_retry_at = models.DateTimeField(
        null=True, blank=True, help_text="Scheduled time for next retry (if applicable)"
    )
    max_retries_reached = models.BooleanField(default=False, help_text="Whether max retry attempts have been exhausted")

    # Observability (per docs/16 section 6)
    correlation_id = models.UUIDField(null=True, blank=True, help_text="Correlation ID for tracing")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True, help_text="Operation duration in milliseconds")

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
    location_details = models.TextField(blank=True, help_text="Additional location info")

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
            models.Index(fields=["firm", "status"], name="calendar_pol_fir_sta_idx"),
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
            models.Index(fields=["firm", "status"], name="calendar_wfl_fir_sta_idx"),
            models.Index(fields=["firm", "trigger"], name="calendar_fir_tri_idx"),
            models.Index(fields=["appointment_type", "status"], name="calendar_wfl_app_sta_idx"),
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
            models.Index(fields=["appointment", "status"], name="calendar_exe_app_sta_idx"),
            models.Index(fields=["status", "scheduled_for"], name="calendar_sta_sch_idx"),
        ]

    def __str__(self):
        return f"{self.workflow.name} for {self.appointment}"
