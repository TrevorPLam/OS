import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager


class ClientNote(models.Model):
    """
    Internal notes about a client.

    NOT visible to the client through the portal.
    Used for team collaboration and client history tracking.
    """

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="internal_notes")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="authored_client_notes"
    )
    note = models.TextField()
    is_pinned = models.BooleanField(default=False, help_text="Pinned notes appear at top")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_note"
        ordering = ["-is_pinned", "-created_at"]
        indexes = [
            models.Index(fields=["client", "-created_at"], name="clients_not_cli_cre_idx"),
        ]

    def __str__(self):
        return f"Note by {self.author} for {self.client.company_name}"


