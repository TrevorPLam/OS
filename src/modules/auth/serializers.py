"""
Authentication Serializers.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from modules.auth.models import SAMLConfiguration

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password", "password2"]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


class ProvisionFirmSerializer(serializers.Serializer):
    """Serializer for provisioning a firm in debug-only environments."""

    firm_name = serializers.CharField(max_length=255)
    firm_slug = serializers.SlugField(max_length=255)

    def validate_firm_slug(self, value):
        """
        Ensure slug matches Firm.slug constraints: lowercase, [a-z0-9-], min length 3.
        """
        value = value.strip().lower()
        if len(value) < 3:
            raise serializers.ValidationError("Slug must be at least 3 characters long.")
        for ch in value:
            if not (ch.islower() or ch.isdigit() or ch == "-"):
                raise serializers.ValidationError(
                    "Slug must contain only lowercase letters, numbers, and hyphens."
                )
        return value
    admin_password = serializers.CharField(write_only=True)
    admin_first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    admin_last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    timezone = serializers.CharField(max_length=50, required=False, default="America/New_York")

    def validate_timezone(self, value):
        """
        Ensure timezone is a valid IANA identifier and within model length limits.
        """
        value = (value or "").strip()
        # Enforce the same max length as Firm.timezone
        if len(value) > 50:
            raise serializers.ValidationError("Timezone must be at most 50 characters long.")
        try:
            from zoneinfo import ZoneInfo  # Local import to avoid global dependency
            ZoneInfo(value)
        except Exception:
            raise serializers.ValidationError("Timezone must be a valid IANA timezone identifier.")
        return value
    currency = serializers.CharField(max_length=3, required=False, default="USD")
    subscription_tier = serializers.CharField(max_length=50, required=False, default="starter")


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])


class SAMLConfigurationSerializer(serializers.ModelSerializer):
    """
    Sprint 1.8: Serializer for SAML Configuration.
    """
    
    class Meta:
        model = SAMLConfiguration
        fields = [
            "id",
            "name",
            "sp_entity_id",
            "sp_public_cert",
            "sp_private_key",
            "idp_entity_id",
            "idp_sso_url",
            "idp_slo_url",
            "idp_x509_cert",
            "attribute_mapping",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "sp_private_key": {"write_only": True},
        }
