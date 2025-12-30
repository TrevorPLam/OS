"""Admin configuration for calendar module."""

from django.contrib import admin
from .models import (
    AppointmentType,
    AvailabilityProfile,
    BookingLink,
    Appointment,
    AppointmentStatusHistory,
    CalendarConnection,
    SyncAttemptLog,
)


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    """Admin for AppointmentType."""

    list_display = [
        "name",
        "duration_minutes",
        "location_mode",
        "routing_policy",
        "status",
        "firm",
    ]
    list_filter = ["status", "location_mode", "routing_policy", "firm"]
    search_fields = ["name", "description"]
    readonly_fields = ["appointment_type_id", "created_at", "updated_at"]


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
