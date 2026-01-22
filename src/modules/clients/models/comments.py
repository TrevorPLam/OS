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
from .clients import Client


class ClientComment(models.Model):
    """
    Comments from clients on project tasks.

    Allows client portal users to comment on tasks in their projects.
    Visible to both firm team and client.
    """

    task = models.ForeignKey(
        "projects.Task", on_delete=models.CASCADE, related_name="client_comments", help_text="Task being commented on"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_task_comments",
        help_text="Portal user who wrote this comment",
    )

    # Comment Content
    comment = models.TextField()

    # Attachments (optional)
    has_attachment = models.BooleanField(default=False, help_text="Whether this comment has file attachments")

    # Read Status (for firm team)
    is_read_by_firm = models.BooleanField(default=False, help_text="Whether firm team has read this client comment")
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="read_client_comments",
        help_text="Firm team member who read this comment",
    )
    read_at = models.DateTimeField(null=True, blank=True, help_text="When the comment was read by firm")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_comment"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "-created_at"], name="clients_tas_cre_idx"),
            models.Index(fields=["client", "-created_at"], name="clients_com_cli_cre_idx"),
            models.Index(fields=["is_read_by_firm"], name="clients_com_is_rea_idx"),
        ]

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on task {self.task.title}"


class ClientChatThread(models.Model):
    """
    Daily chat thread between client and firm team.

    Threads rotate daily (00:00 UTC) to keep conversations organized.
    Archived threads are stored in ClientChatArchive.
    """

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="chat_threads", help_text="Client this thread belongs to"
    )
    date = models.DateField(help_text="Date of this thread (YYYY-MM-DD)")
    is_active = models.BooleanField(default=True, help_text="Whether this is the current active thread")
    archived_at = models.DateTimeField(null=True, blank=True, help_text="When this thread was archived")

    # Statistics
    message_count = models.IntegerField(default=0, help_text="Total messages in this thread")
    last_message_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last message")
    last_message_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_chat_message_threads",
        help_text="User who sent last message",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_chat_thread"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["client", "-date"], name="clients_cli_dat_idx"),
            models.Index(fields=["is_active"], name="clients_thr_is_act_idx"),
            models.Index(fields=["-last_message_at"], name="clients_las_idx"),
        ]
        unique_together = [["client", "date"]]

    def __str__(self):
        return f"{self.client.company_name} - Chat Thread {self.date}"


class ClientMessage(models.Model):
    """
    Individual message in a client chat thread.

    Messages are sent between client portal users and firm team members.
    Supports text messages and file attachments.
    """

    MESSAGE_TYPE_CHOICES = [
        ("text", "Text Message"),
        ("file", "File Attachment"),
        ("system", "System Notification"),
    ]

    thread = models.ForeignKey(
        ClientChatThread, on_delete=models.CASCADE, related_name="messages", help_text="Thread this message belongs to"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_client_messages",
        help_text="User who sent this message",
    )
    is_from_client = models.BooleanField(default=False, help_text="Whether sender is a client portal user")

    # Message Content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default="text")
    content = models.TextField(help_text="Message text content")

    # File Attachment (optional)
    attachment_url = models.URLField(blank=True, help_text="S3 URL for file attachment (if message_type=file)")
    attachment_filename = models.CharField(max_length=255, blank=True, help_text="Original filename of attachment")
    attachment_size_bytes = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")

    # Read Status
    is_read = models.BooleanField(default=False, help_text="Whether message has been read by recipient")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When message was read")
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="read_client_messages",
        help_text="User who read this message",
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["thread", "created_at"], name="clients_thr_cre_idx"),
            models.Index(fields=["sender", "-created_at"], name="clients_sen_cre_idx"),
            models.Index(fields=["is_read"], name="clients_msg_is_rea_idx"),
        ]

    def __str__(self):
        sender_name = self.sender.get_full_name() or self.sender.username
        return f"Message from {sender_name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        """Update thread statistics when message is saved."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Update thread statistics
            self.thread.message_count = self.thread.messages.count()
            self.thread.last_message_at = self.created_at
            self.thread.last_message_by = self.sender
            self.thread.save()


