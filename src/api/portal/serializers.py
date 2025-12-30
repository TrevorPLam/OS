"""
Portal Serializers (DOC-26.1).

Serializers for client portal views - only expose client-safe fields.
"""

from rest_framework import serializers
from modules.clients.models import Client, ClientPortalUser
from modules.documents.models import Document, Folder
from modules.calendar.models import Appointment


class PortalAccountSerializer(serializers.ModelSerializer):
    """Serializer for account switcher."""

    class Meta:
        model = Client
        fields = ["id", "name", "account_number"]


class PortalProfileSerializer(serializers.ModelSerializer):
    """Serializer for portal user profile."""

    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = ClientPortalUser
        fields = [
            "id",
            "email",
            "full_name",
            "client_name",
            "can_view_projects",
            "can_view_invoices",
            "can_view_documents",
            "can_upload_documents",
            "can_message_staff",
            "can_book_appointments",
            "notification_preferences",
        ]
        read_only_fields = [
            "id",
            "email",
            "full_name",
            "client_name",
            "can_view_projects",
            "can_view_invoices",
            "can_view_documents",
            "can_upload_documents",
            "can_message_staff",
            "can_book_appointments",
        ]


class PortalHomeSerializer(serializers.Serializer):
    """Serializer for portal home dashboard."""

    recent_messages = serializers.ListField(child=serializers.DictField())
    upcoming_appointments = serializers.ListField(child=serializers.DictField())
    recent_documents = serializers.ListField(child=serializers.DictField())
    pending_invoices = serializers.ListField(child=serializers.DictField())
    account_count = serializers.IntegerField()


class PortalFolderSerializer(serializers.ModelSerializer):
    """Serializer for portal folder view."""

    class Meta:
        model = Folder
        fields = ["id", "name", "description", "parent"]


class PortalDocumentSerializer(serializers.ModelSerializer):
    """Serializer for portal document view."""

    folder_name = serializers.CharField(source="folder.name", read_only=True, allow_null=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.get_full_name", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "name",
            "description",
            "folder",
            "folder_name",
            "file_type",
            "file_size_bytes",
            "current_version",
            "created_at",
            "updated_at",
            "uploaded_by_name",
        ]
        read_only_fields = fields


class PortalAppointmentSerializer(serializers.ModelSerializer):
    """Serializer for portal appointment view."""

    appointment_type_name = serializers.CharField(source="appointment_type.name", read_only=True)
    staff_name = serializers.CharField(source="staff_user.get_full_name", read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_type",
            "appointment_type_name",
            "staff_user",
            "staff_name",
            "start_time",
            "end_time",
            "location_mode",
            "location_details",
            "status",
            "notes",
            "created_at",
        ]
        read_only_fields = fields
