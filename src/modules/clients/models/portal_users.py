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


class ClientPortalUser(models.Model):
    """
    Client-side users with portal access.

    Links Django User accounts to Clients with specific permissions.
    """

    ROLE_CHOICES = [
        ("admin", "Client Admin"),
        ("member", "Client Member"),
        ("viewer", "View Only"),
    ]

from modules.core.validators import validate_safe_url
from modules.firm.utils import FirmScopedManager
from .clients import Client


class ClientPortalUser(models.Model):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    # Permissions
    can_upload_documents = models.BooleanField(default=True)
    can_view_billing = models.BooleanField(default=True)
    can_message_team = models.BooleanField(default=True)
    can_view_projects = models.BooleanField(default=True)

    # Audit
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="invited_portal_users",
        help_text="Firm user who invited this client user",
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "clients_portal_user"
        unique_together = [["client", "user"]]
        ordering = ["-invited_at"]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.client.company_name} ({self.role})"


