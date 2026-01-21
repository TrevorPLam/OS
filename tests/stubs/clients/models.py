"""Minimal client models to satisfy calendar foreign key references in tests."""

from django.db import models


class Client(models.Model):
    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE, related_name="stub_clients")
    name = models.CharField(max_length=255, default="Stub Client")

    class Meta:
        app_label = "clients"


class ClientEngagement(models.Model):
    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE, related_name="stub_engagements")
    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE, related_name="stub_engagements")
    name = models.CharField(max_length=255, default="Stub Engagement")

    class Meta:
        app_label = "clients"


class Contact(models.Model):
    firm = models.ForeignKey("firm.Firm", on_delete=models.CASCADE, related_name="stub_contacts")
    client = models.ForeignKey("clients.Client", on_delete=models.CASCADE, related_name="stub_contacts")
    name = models.CharField(max_length=255, default="Stub Contact")
    email = models.EmailField(blank=True)

    class Meta:
        app_label = "clients"
