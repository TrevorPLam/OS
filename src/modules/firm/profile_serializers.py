"""
Serializers for user profile extensions.

Provides DRF serializers for UserProfile model.
"""

from rest_framework import serializers
from modules.firm.profile_extensions import UserProfile
from modules.firm.models import FirmMembership


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile."""

    user_id = serializers.IntegerField(source='firm_membership.user.id', read_only=True)
    user_email = serializers.EmailField(source='firm_membership.user.email', read_only=True)
    user_full_name = serializers.CharField(source='firm_membership.user.get_full_name', read_only=True)
    firm_id = serializers.IntegerField(source='firm_membership.firm.id', read_only=True)
    firm_name = serializers.CharField(source='firm_membership.firm.name', read_only=True)
    role = serializers.CharField(source='firm_membership.role', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    profile_photo_url = serializers.CharField(source='get_profile_photo_url', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'firm_membership',
            'user_id',
            'user_email',
            'user_full_name',
            'firm_id',
            'firm_name',
            'role',
            'display_name',
            # Visual Identity
            'profile_photo',
            'profile_photo_url',
            'job_title',
            'bio',
            # Email Signature
            'email_signature_html',
            'email_signature_plain',
            'include_signature_by_default',
            # Meeting & Scheduling
            'personal_meeting_link',
            'meeting_link_description',
            'calendar_booking_link',
            # Contact Information
            'phone_number',
            'phone_extension',
            'mobile_number',
            'office_location',
            # Social & Professional Links
            'linkedin_url',
            'twitter_handle',
            'website_url',
            # Preferences
            'timezone_preference',
            'language_preference',
            'notification_preferences',
            # Visibility Settings
            'show_phone_in_directory',
            'show_email_in_directory',
            'show_availability_to_clients',
            # Metadata
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'user_id',
            'user_email',
            'user_full_name',
            'firm_id',
            'firm_name',
            'role',
            'display_name',
            'profile_photo_url',
        ]


class UserProfilePhotoUploadSerializer(serializers.Serializer):
    """Serializer for profile photo upload."""

    profile_photo = serializers.ImageField(
        required=True,
        help_text='Profile photo file (recommended: 400x400px, max 2MB)'
    )

    def validate_profile_photo(self, value):
        """Validate profile photo size and format."""
        # Check file size (max 2MB)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('Profile photo must be less than 2MB')

        # Check file format
        allowed_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_formats:
            raise serializers.ValidationError(
                f'Unsupported file format. Allowed formats: {", ".join(allowed_formats)}'
            )

        return value


class EmailSignatureGenerateSerializer(serializers.Serializer):
    """Serializer for generating email signature preview."""

    html = serializers.BooleanField(
        default=True,
        help_text='Generate HTML signature (default: True)'
    )
