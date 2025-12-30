"""OAuth serializers for calendar module."""

from rest_framework import serializers
from .oauth_models import OAuthConnection, OAuthAuthorizationCode


class OAuthConnectionSerializer(serializers.ModelSerializer):
    """Serializer for OAuthConnection."""

    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    is_token_expired = serializers.SerializerMethodField()
    needs_refresh = serializers.SerializerMethodField()

    class Meta:
        model = OAuthConnection
        fields = [
            'connection_id',
            'provider',
            'user',
            'user_username',
            'provider_user_id',
            'provider_email',
            'scopes',
            'sync_enabled',
            'sync_window_days',
            'last_sync_at',
            'status',
            'error_message',
            'is_token_expired',
            'needs_refresh',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'connection_id',
            'provider_user_id',
            'provider_email',
            'scopes',
            'last_sync_at',
            'status',
            'error_message',
            'is_token_expired',
            'needs_refresh',
            'user_username',
            'created_at',
            'updated_at',
        ]

    def get_is_token_expired(self, obj):
        """Check if token is expired."""
        return obj.is_token_expired()

    def get_needs_refresh(self, obj):
        """Check if token needs refresh."""
        return obj.needs_refresh()


class OAuthInitiateSerializer(serializers.Serializer):
    """Serializer for initiating OAuth flow."""

    provider = serializers.ChoiceField(
        choices=OAuthConnection.PROVIDER_CHOICES,
        required=True,
        help_text='Calendar provider to connect'
    )


class OAuthCallbackSerializer(serializers.Serializer):
    """Serializer for OAuth callback."""

    code = serializers.CharField(
        required=True,
        help_text='Authorization code from provider'
    )
    state = serializers.UUIDField(
        required=True,
        help_text='State token for CSRF protection'
    )


class CalendarSyncStatusSerializer(serializers.Serializer):
    """Serializer for calendar sync status."""

    connection = OAuthConnectionSerializer(read_only=True)
    last_sync_at = serializers.DateTimeField(read_only=True)
    sync_enabled = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True, allow_blank=True)
