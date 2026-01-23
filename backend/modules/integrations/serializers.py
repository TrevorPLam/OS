from __future__ import annotations

from rest_framework import serializers

from modules.integrations.models import GoogleAnalyticsConfig, SalesforceConnection, SlackIntegration


class SalesforceConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesforceConnection
        fields = [
            "id",
            "client_id",
            "client_secret",
            "access_token",
            "refresh_token",
            "instance_url",
            "scopes",
            "status",
            "expires_at",
            "last_synced_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"client_secret": {"write_only": True}, "access_token": {"write_only": True}, "refresh_token": {"write_only": True}}


class SalesforceSyncRequestSerializer(serializers.Serializer):
    object_type = serializers.ChoiceField(choices=["contact", "lead", "opportunity"])
    payload = serializers.DictField()


class SlackIntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackIntegration
        fields = [
            "id",
            "bot_token",
            "signing_secret",
            "default_channel",
            "webhook_url",
            "status",
            "last_health_check",
            "last_error",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "bot_token": {"write_only": True},
            "signing_secret": {"write_only": True},
        }


class SlackTestMessageSerializer(serializers.Serializer):
    channel = serializers.CharField(required=False, allow_blank=True)
    text = serializers.CharField()


class GoogleAnalyticsConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleAnalyticsConfig
        fields = [
            "id",
            "measurement_id",
            "api_secret",
            "property_id",
            "stream_id",
            "status",
            "last_event_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "api_secret": {"write_only": True},
        }


class GoogleAnalyticsEventSerializer(serializers.Serializer):
    client_id = serializers.CharField()
    events = serializers.ListField(child=serializers.DictField(), allow_empty=False)
