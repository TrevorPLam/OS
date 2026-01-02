"""Admin configuration for calendar module."""

from django.contrib import admin

from .models import (
    Appointment,
    AppointmentStatusHistory,
    AppointmentType,
    AvailabilityProfile,
    BookingLink,
    CalendarConnection,
    MeetingPoll,
    MeetingPollVote,
    MeetingWorkflow,
    MeetingWorkflowExecution,
    SyncAttemptLog,
)
from .oauth_models import (
    OAuthAuthorizationCode,
    OAuthConnection,
)


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    """Admin for AppointmentType."""

    list_display = [
        "name",
        "event_category",
        "duration_minutes",
        "location_mode",
        "routing_policy",
        "status",
        "firm",
    ]
    list_filter = ["status", "event_category", "location_mode", "routing_policy", "firm"]
    search_fields = ["name", "internal_name", "description"]
    readonly_fields = ["appointment_type_id", "created_at", "updated_at"]
    filter_horizontal = ["required_hosts", "optional_hosts", "round_robin_pool"]

    fieldsets = (
        (None, {"fields": ("firm", "name", "description", "status")}),
        (
            "Rich Event Description (CAL-3)",
            {
                "fields": ("internal_name", "rich_description", "description_image"),
                "description": "Internal name for staff, rich HTML description with formatting, and optional image",
                "classes": ("collapse",),
            },
        ),
        (
            "Event Category (CAL-1)",
            {"fields": ("event_category",), "description": "Event type: one-on-one, group, collective, or round robin"},
        ),
        (
            "Group Event Settings (CAL-1)",
            {
                "fields": ("max_attendees", "enable_waitlist"),
                "description": "Required for group events",
                "classes": ("collapse",),
            },
        ),
        (
            "Collective Event Settings (CAL-1)",
            {
                "fields": ("required_hosts", "optional_hosts"),
                "description": "Configure hosts for collective events (multiple hosts, overlapping availability)",
                "classes": ("collapse",),
            },
        ),
        (
            "Round Robin Settings (CAL-1)",
            {
                "fields": ("round_robin_pool",),
                "description": "Configure staff pool for round robin distribution",
                "classes": ("collapse",),
            },
        ),
        ("Duration & Buffers", {"fields": ("duration_minutes", "buffer_before_minutes", "buffer_after_minutes")}),
        (
            "Multiple Durations (CAL-2)",
            {
                "fields": ("enable_multiple_durations", "duration_options"),
                "description": "Allow bookers to select from multiple duration options with optional pricing",
                "classes": ("collapse",),
            },
        ),
        ("Location", {"fields": ("location_mode", "location_details")}),
        (
            "Booking Channels",
            {"fields": ("allow_portal_booking", "allow_staff_booking", "allow_public_prospect_booking")},
        ),
        ("Routing", {"fields": ("routing_policy", "fixed_staff_user", "requires_approval")}),
        (
            "Intake Questions",
            {
                "fields": ("intake_questions",),
                "description": "JSON array of intake questions",
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("appointment_type_id", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(AvailabilityProfile)
class AvailabilityProfileAdmin(admin.ModelAdmin):
    """Admin for AvailabilityProfile."""

    list_display = [
        "name",
        "owner_type",
        "owner_staff_user",
        "timezone",
        "status",
        "firm",
    ]
    list_filter = ["owner_type", "status", "firm"]
    search_fields = ["name", "owner_team_name"]
    readonly_fields = ["availability_profile_id", "created_at", "updated_at"]


@admin.register(BookingLink)
class BookingLinkAdmin(admin.ModelAdmin):
    """Admin for BookingLink."""

    list_display = [
        "slug",
        "appointment_type",
        "visibility",
        "status",
        "firm",
        "created_at",
    ]
    list_filter = ["visibility", "status", "firm"]
    search_fields = ["slug"]
    readonly_fields = ["booking_link_id", "token", "created_at", "updated_at"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin for Appointment."""

    list_display = [
        "appointment_id",
        "appointment_type",
        "staff_user",
        "account",
        "start_time",
        "status",
        "firm",
    ]
    list_filter = ["status", "appointment_type", "firm", "start_time"]
    search_fields = ["staff_user__username", "account__name"]
    readonly_fields = ["appointment_id", "booked_at", "created_at", "updated_at"]


@admin.register(AppointmentStatusHistory)
class AppointmentStatusHistoryAdmin(admin.ModelAdmin):
    """Admin for AppointmentStatusHistory."""

    list_display = [
        "appointment",
        "from_status",
        "to_status",
        "changed_by",
        "changed_at",
    ]
    list_filter = ["from_status", "to_status", "changed_at"]
    search_fields = ["appointment__appointment_id", "reason"]
    readonly_fields = ["changed_at"]


@admin.register(CalendarConnection)
class CalendarConnectionAdmin(admin.ModelAdmin):
    """Admin for CalendarConnection."""

    list_display = [
        "connection_id",
        "provider",
        "owner_staff_user",
        "status",
        "last_sync_at",
        "firm",
    ]
    list_filter = ["provider", "status", "firm"]
    search_fields = ["owner_staff_user__username"]
    readonly_fields = ["connection_id", "last_sync_at", "created_at", "updated_at"]


@admin.register(SyncAttemptLog)
class SyncAttemptLogAdmin(admin.ModelAdmin):
    """Admin for SyncAttemptLog."""

    list_display = [
        "attempt_id",
        "direction",
        "operation",
        "status",
        "error_class",
        "connection",
        "started_at",
        "duration_ms",
    ]
    list_filter = ["direction", "operation", "status", "error_class", "started_at"]
    search_fields = ["correlation_id", "error_summary"]
    readonly_fields = ["attempt_id", "started_at", "finished_at", "duration_ms", "correlation_id"]


@admin.register(MeetingPoll)
class MeetingPollAdmin(admin.ModelAdmin):
    """Admin for MeetingPoll."""

    list_display = [
        "title",
        "created_by",
        "status",
        "voting_deadline",
        "require_all_invitees",
        "created_at",
    ]
    list_filter = ["status", "require_all_invitees", "firm", "created_at"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at", "closed_at"]
    raw_id_fields = ["created_by", "scheduled_appointment"]
    fieldsets = (
        (None, {"fields": ("firm", "title", "description")}),
        ("Organizer", {"fields": ("created_by",)}),
        (
            "Time Slots",
            {
                "fields": ("proposed_slots",),
                "description": "JSON array of proposed time slots",
            },
        ),
        (
            "Invitees",
            {
                "fields": ("invitees",),
                "description": "JSON array of invitee email addresses",
            },
        ),
        (
            "Settings",
            {"fields": ("voting_deadline", "require_all_invitees", "allow_maybe_votes")},
        ),
        ("Status", {"fields": ("status", "scheduled_appointment", "selected_slot_index", "closed_at")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(MeetingPollVote)
class MeetingPollVoteAdmin(admin.ModelAdmin):
    """Admin for MeetingPollVote."""

    list_display = ["poll", "voter_email", "voter_name", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["voter_email", "voter_name", "poll__title"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["poll", "voter_user"]
    fieldsets = (
        (None, {"fields": ("poll",)}),
        ("Voter", {"fields": ("voter_user", "voter_email", "voter_name")}),
        (
            "Responses",
            {
                "fields": ("responses", "notes"),
                "description": "responses is a JSON array of vote choices (yes/no/maybe) for each proposed slot",
            },
        ),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(MeetingWorkflow)
class MeetingWorkflowAdmin(admin.ModelAdmin):
    """Admin for MeetingWorkflow."""

    list_display = [
        "name",
        "trigger",
        "action_type",
        "delay_minutes",
        "status",
    ]
    list_filter = ["trigger", "action_type", "status", "firm"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["appointment_type", "created_by"]
    fieldsets = (
        (None, {"fields": ("firm", "name", "description")}),
        (
            "Trigger Configuration",
            {
                "fields": ("trigger", "appointment_type"),
                "description": "appointment_type filters which appointments trigger this workflow (blank = all)",
            },
        ),
        (
            "Action Configuration",
            {
                "fields": ("action_type", "action_config", "delay_minutes"),
                "description": "action_config is a JSON object with action-specific settings",
            },
        ),
        ("Status", {"fields": ("status",)}),
        ("Metadata", {"fields": ("created_at", "updated_at", "created_by")}),
    )


@admin.register(MeetingWorkflowExecution)
class MeetingWorkflowExecutionAdmin(admin.ModelAdmin):
    """Admin for MeetingWorkflowExecution."""

    list_display = [
        "workflow",
        "appointment",
        "status",
        "scheduled_for",
        "executed_at",
    ]
    list_filter = ["status", "scheduled_for", "executed_at"]
    search_fields = ["appointment__appointment_id", "workflow__name", "error_message"]
    readonly_fields = ["scheduled_for", "executed_at", "created_at"]
    raw_id_fields = ["workflow", "appointment"]


@admin.register(OAuthConnection)
class OAuthConnectionAdmin(admin.ModelAdmin):
    """Admin for OAuthConnection."""

    list_display = [
        "connection_id",
        "provider",
        "user",
        "provider_email",
        "status",
        "sync_enabled",
        "last_sync_at",
        "firm",
        "created_at",
    ]
    list_filter = ["provider", "status", "sync_enabled", "firm"]
    search_fields = ["user__username", "provider_email", "provider_user_id"]
    readonly_fields = [
        "connection_id",
        "token_expires_at",
        "last_sync_at",
        "created_at",
        "updated_at",
    ]
    raw_id_fields = ["firm", "user"]

    fieldsets = (
        (None, {"fields": ("firm", "user", "provider", "status")}),
        ("Provider Details", {"fields": ("provider_user_id", "provider_email", "provider_metadata")}),
        (
            "OAuth Tokens",
            {
                "fields": ("access_token", "refresh_token", "token_expires_at", "scopes"),
                "classes": ("collapse",),
            },
        ),
        (
            "Sync Configuration",
            {
                "fields": (
                    "sync_enabled",
                    "sync_window_days",
                    "last_sync_at",
                    "last_sync_cursor",
                )
            },
        ),
        (
            "Error Info",
            {
                "fields": ("error_message",),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(OAuthAuthorizationCode)
class OAuthAuthorizationCodeAdmin(admin.ModelAdmin):
    """Admin for OAuthAuthorizationCode."""

    list_display = [
        "code_id",
        "provider",
        "user",
        "state",
        "state_token",
        "expires_at",
        "created_at",
    ]
    list_filter = ["provider", "state", "firm"]
    search_fields = ["user__username", "state_token"]
    readonly_fields = [
        "code_id",
        "state_token",
        "created_at",
        "exchanged_at",
    ]
    raw_id_fields = ["firm", "user", "connection"]

    fieldsets = (
        (None, {"fields": ("firm", "user", "provider", "state", "state_token")}),
        ("Authorization Data", {"fields": ("authorization_code", "redirect_uri")}),
        (
            "Result",
            {
                "fields": ("connection", "error_message"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timing",
            {
                "fields": ("expires_at", "created_at", "exchanged_at"),
                "classes": ("collapse",),
            },
        ),
    )
