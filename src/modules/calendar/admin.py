"""Admin configuration for calendar module."""

from django.contrib import admin
from .models import (
    AppointmentType,
    AvailabilityProfile,
    BookingLink,
    Appointment,
    AppointmentStatusHistory,
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
