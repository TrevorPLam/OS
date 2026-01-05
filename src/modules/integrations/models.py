from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from modules.firm.models import Firm
from modules.firm.utils import FirmScopedManager


class SalesforceConnection(models.Model):
    STATUS_CHOICES = [
        ("disconnected", "Disconnected"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("error", "Error"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="salesforce_connections")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    client_id = models.CharField(max_length=255)
    client_secret = models.TextField(blank=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    instance_url = models.CharField(max_length=255, blank=True)
    scopes = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="disconnected")
    expires_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "integrations_salesforce_connection"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["firm", "status"], name="salesforce_conn_status_idx"),
            models.Index(fields=["firm", "created_at"], name="salesforce_conn_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.firm.slug} Salesforce Connection"

    def mark_error(self, message: str) -> None:
        self.last_error = message
        self.status = "error"
        self.save(update_fields=["last_error", "status"])


class SalesforceSyncLog(models.Model):
    connection = models.ForeignKey(
        SalesforceConnection, on_delete=models.SET_NULL, related_name="sync_logs", null=True, blank=True
    )
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="salesforce_sync_logs")
    object_type = models.CharField(max_length=50)
    direction = models.CharField(max_length=20, help_text="push|pull")
    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, help_text="success|error")
    message = models.CharField(max_length=500, blank=True)
    payload_snippet = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integrations_salesforce_sync_log"
        ordering = ["-occurred_at"]
        indexes = [models.Index(fields=["firm", "object_type"], name="salesforce_sync_object_idx")]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.object_type}:{self.status}"


class SlackIntegration(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("disabled", "Disabled"),
        ("error", "Error"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="slack_integrations")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    bot_token = models.TextField(blank=True)
    signing_secret = models.TextField(blank=True)
    default_channel = models.CharField(max_length=120, blank=True)
    webhook_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="disabled")
    last_health_check = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "integrations_slack"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["firm", "status"], name="slack_integration_status_idx")]

    def __str__(self) -> str:
        return f"{self.firm.slug} Slack"

    def mark_error(self, message: str) -> None:
        self.last_error = message
        self.status = "error"
        self.last_health_check = timezone.now()
        self.save(update_fields=["last_error", "status", "last_health_check"])


class SlackMessageLog(models.Model):
    integration = models.ForeignKey(
        SlackIntegration, on_delete=models.CASCADE, related_name="message_logs", null=True, blank=True
    )
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="slack_message_logs")
    channel = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=[("sent", "Sent"), ("error", "Error")])
    message = models.CharField(max_length=500)
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integrations_slack_message_log"
        ordering = ["-occurred_at"]
        indexes = [models.Index(fields=["firm", "channel"], name="slack_log_channel_idx")]

    def __str__(self) -> str:
        return f"{self.firm.slug}:{self.channel}:{self.status}"


class GoogleAnalyticsConfig(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("disabled", "Disabled"),
        ("error", "Error"),
    ]

    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="google_analytics_configs")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    measurement_id = models.CharField(max_length=50)
    api_secret = models.CharField(max_length=120)
    property_id = models.CharField(max_length=50, blank=True)
    stream_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    last_event_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = "integrations_google_analytics"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["firm", "status"], name="ga_config_status_idx")]

    def __str__(self) -> str:
        return f"{self.firm.slug} GA {self.measurement_id}"

    def mark_error(self, message: str) -> None:
        self.last_error = message
        self.status = "error"
        self.save(update_fields=["last_error", "status"])
