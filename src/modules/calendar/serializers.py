"""Calendar serializers."""

from rest_framework import serializers
from .models import AppointmentType, AvailabilityProfile, BookingLink, Appointment


class AppointmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for AppointmentType."""

    class Meta:
        model = AppointmentType
        fields = [
            "appointment_type_id",
            "name",
            "description",
            "duration_minutes",
            "buffer_before_minutes",
            "buffer_after_minutes",
            "location_mode",
            "location_details",
            "allow_portal_booking",
            "allow_staff_booking",
            "allow_public_prospect_booking",
            "requires_approval",
            "routing_policy",
            "intake_questions",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["appointment_type_id", "created_at", "updated_at"]


class AvailabilityProfileSerializer(serializers.ModelSerializer):
    """Serializer for AvailabilityProfile."""

    owner_display = serializers.SerializerMethodField()

    class Meta:
        model = AvailabilityProfile
        fields = [
            "availability_profile_id",
            "name",
            "owner_type",
            "owner_staff_user",
            "owner_team_name",
            "owner_display",
            "timezone",
            "weekly_hours",
            "exceptions",
            "min_notice_minutes",
            "max_future_days",
            "slot_rounding_minutes",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["availability_profile_id", "owner_display", "created_at", "updated_at"]

    def get_owner_display(self, obj):
        """Return display name for owner."""
        if obj.owner_type == "staff" and obj.owner_staff_user:
            return obj.owner_staff_user.username
        return obj.owner_team_name


class BookingLinkSerializer(serializers.ModelSerializer):
    """Serializer for BookingLink."""

    appointment_type_name = serializers.CharField(source="appointment_type.name", read_only=True)
    booking_url = serializers.SerializerMethodField()

    class Meta:
        model = BookingLink
        fields = [
            "booking_link_id",
            "appointment_type",
            "appointment_type_name",
            "availability_profile",
            "account",
            "engagement",
            "visibility",
            "slug",
            "token",
            "status",
            "booking_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["booking_link_id", "token", "booking_url", "created_at", "updated_at"]

    def get_booking_url(self, obj):
        """Return full booking URL."""
        return f"/book/{obj.slug}"


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer for Appointment list view."""

    appointment_type_name = serializers.CharField(source="appointment_type.name", read_only=True)
    staff_username = serializers.CharField(source="staff_user.username", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            "appointment_id",
            "appointment_type",
            "appointment_type_name",
            "staff_user",
            "staff_username",
            "account",
            "account_name",
            "start_time",
            "end_time",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for Appointment detail view."""

    appointment_type_name = serializers.CharField(source="appointment_type.name", read_only=True)
    staff_username = serializers.CharField(source="staff_user.username", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True, allow_null=True)
    contact_name = serializers.CharField(source="contact.name", read_only=True, allow_null=True)
    booked_by_username = serializers.CharField(source="booked_by.username", read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            "appointment_id",
            "appointment_type",
            "appointment_type_name",
            "booking_link",
            "staff_user",
            "staff_username",
            "account",
            "account_name",
            "contact",
            "contact_name",
            "start_time",
            "end_time",
            "timezone",
            "intake_responses",
            "status",
            "status_reason",
            "external_event_id",
            "booked_by",
            "booked_by_username",
            "booked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BookAppointmentSerializer(serializers.Serializer):
    """Serializer for booking an appointment."""

    appointment_type_id = serializers.IntegerField(required=True)
    start_time = serializers.DateTimeField(required=True)
    account_id = serializers.IntegerField(required=False, allow_null=True)
    contact_id = serializers.IntegerField(required=False, allow_null=True)
    intake_responses = serializers.JSONField(required=False, default=dict)

    def validate_start_time(self, value):
        """Ensure start time is in the future."""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Start time must be in the future")
        return value


class CancelAppointmentSerializer(serializers.Serializer):
    """Serializer for cancelling an appointment."""

    reason = serializers.CharField(required=True, max_length=500)

    def validate_reason(self, value):
        """Reason must not be empty."""
        if not value.strip():
            raise serializers.ValidationError("Reason cannot be empty")
        return value.strip()


class AvailableSlotsSerializer(serializers.Serializer):
    """Serializer for requesting available slots."""

    appointment_type_id = serializers.IntegerField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    staff_user_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        """Validate date range."""
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError("End date must be after start date")

        # Limit to 30 days max
        delta = (data["end_date"] - data["start_date"]).days
        if delta > 30:
            raise serializers.ValidationError("Date range cannot exceed 30 days")

        return data
