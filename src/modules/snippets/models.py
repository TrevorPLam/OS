"""
Models for snippets module.

Quick text insertion system for productivity enhancement.
Allows staff to create reusable text snippets with shortcuts and variables.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from modules.firm.models import Firm
from modules.firm.managers import FirmScopedManager
import re


class Snippet(models.Model):
    """
    Reusable text snippet with shortcut trigger.

    HubSpot-style snippets for quick text insertion in emails, tickets, messages.
    Supports variables like {{contact_name}}, {{company_name}}, {{my_name}}, etc.

    Usage:
        - Type # + shortcut (e.g., #meeting) to trigger snippet
        - Variables are replaced with actual values at insertion time
        - Can be personal (user-owned) or team-wide (shared)
    """

    CONTEXT_CHOICES = [
        ('all', 'All Contexts'),
        ('email', 'Email Only'),
        ('ticket', 'Tickets Only'),
        ('message', 'Messages Only'),
        ('note', 'Notes Only'),
    ]

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='snippets',
        help_text='Firm this snippet belongs to'
    )

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_snippets',
        help_text='User who created this snippet'
    )
    is_shared = models.BooleanField(
        default=False,
        help_text='If True, snippet is available to all team members; if False, only creator can use it'
    )
    shared_with_roles = models.JSONField(
        default=list,
        blank=True,
        help_text='List of role names this snippet is shared with (empty = all roles if is_shared=True)'
    )

    # Snippet Definition
    shortcut = models.CharField(
        max_length=50,
        help_text='Shortcut trigger (e.g., "meeting", "followup"). Type # + shortcut to insert'
    )
    name = models.CharField(
        max_length=255,
        help_text='Descriptive name for this snippet'
    )
    content = models.TextField(
        help_text='Snippet content with optional variables: {{contact_name}}, {{company_name}}, {{my_name}}, etc.'
    )

    # Context & Usage
    context = models.CharField(
        max_length=20,
        choices=CONTEXT_CHOICES,
        default='all',
        help_text='Where this snippet can be used'
    )
    usage_count = models.IntegerField(
        default=0,
        help_text='Number of times this snippet has been used'
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this snippet was last used'
    )

    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this snippet is active and available for use'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'snippets'
        ordering = ['-usage_count', 'shortcut']
        indexes = [
            models.Index(fields=['firm', 'shortcut']),
            models.Index(fields=['firm', 'is_shared']),
            models.Index(fields=['firm', 'created_by']),
            models.Index(fields=['is_active']),
        ]
        unique_together = [('firm', 'shortcut', 'created_by')]

    def __str__(self):
        return f"#{self.shortcut} - {self.name}"

    def clean(self):
        """Validate snippet."""
        super().clean()

        # Validate shortcut format (alphanumeric, underscore, hyphen only)
        if not re.match(r'^[a-z0-9_-]+$', self.shortcut):
            raise ValidationError({
                'shortcut': 'Shortcut must contain only lowercase letters, numbers, underscore, and hyphen'
            })

        # Check for duplicate shortcuts within scope
        qs = Snippet.objects.filter(
            firm=self.firm,
            shortcut=self.shortcut,
            is_active=True
        )

        if not self.is_shared:
            # Personal snippet - check for duplicate in user's personal snippets
            qs = qs.filter(created_by=self.created_by, is_shared=False)
        else:
            # Shared snippet - check for duplicate in shared snippets
            qs = qs.filter(is_shared=True)

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            scope = "team" if self.is_shared else "your personal"
            raise ValidationError({
                'shortcut': f'A snippet with shortcut "#{self.shortcut}" already exists in {scope} snippets'
            })

    def get_available_variables(self):
        """
        Return list of available variables for this snippet.

        Variables depend on context:
        - Common: {{my_name}}, {{my_email}}, {{my_title}}, {{company_name}}
        - Contact context: {{contact_name}}, {{contact_email}}, {{contact_company}}
        - Ticket context: {{ticket_number}}, {{ticket_subject}}
        - Meeting context: {{meeting_date}}, {{meeting_time}}, {{meeting_link}}
        """
        common_vars = [
            '{{my_name}}',
            '{{my_email}}',
            '{{my_title}}',
            '{{my_phone}}',
            '{{company_name}}',
            '{{current_date}}',
            '{{current_time}}',
        ]

        context_vars = {
            'email': ['{{contact_name}}', '{{contact_email}}', '{{contact_company}}'],
            'ticket': ['{{ticket_number}}', '{{ticket_subject}}', '{{requester_name}}'],
            'message': ['{{recipient_name}}', '{{conversation_subject}}'],
            'all': ['{{contact_name}}', '{{contact_email}}', '{{ticket_number}}'],
        }

        return common_vars + context_vars.get(self.context, [])

    def extract_variables(self):
        """Extract all variables from snippet content."""
        return re.findall(r'\{\{(\w+)\}\}', self.content)

    def render(self, context_data):
        """
        Render snippet content with actual values.

        Args:
            context_data (dict): Dictionary of variable values
                Example: {'contact_name': 'John Doe', 'my_name': 'Jane Smith'}

        Returns:
            str: Rendered snippet content with variables replaced
        """
        rendered = self.content

        for key, value in context_data.items():
            placeholder = '{{' + key + '}}'
            rendered = rendered.replace(placeholder, str(value or ''))

        return rendered

    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])


class SnippetUsageLog(models.Model):
    """
    Log of snippet usage for analytics and insights.

    Tracks when, where, and by whom snippets are used.
    """

    snippet = models.ForeignKey(
        Snippet,
        on_delete=models.CASCADE,
        related_name='usage_logs',
        help_text='Snippet that was used'
    )
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='snippet_usages',
        help_text='User who used the snippet'
    )

    # Context
    context = models.CharField(
        max_length=20,
        help_text='Where the snippet was used (email, ticket, message, note)'
    )
    context_object_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Type of object (e.g., "ticket", "email", "message")'
    )
    context_object_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='ID of the object where snippet was used'
    )

    # Usage Details
    variables_used = models.JSONField(
        default=dict,
        help_text='Variables that were replaced in this usage'
    )
    rendered_length = models.IntegerField(
        default=0,
        help_text='Length of rendered snippet (characters)'
    )

    # Metadata
    used_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = 'snippet_usage_logs'
        ordering = ['-used_at']
        indexes = [
            models.Index(fields=['snippet', '-used_at']),
            models.Index(fields=['used_by', '-used_at']),
            models.Index(fields=['context', '-used_at']),
        ]

    def __str__(self):
        return f"{self.snippet.shortcut} used by {self.used_by} at {self.used_at}"


class SnippetFolder(models.Model):
    """
    Folder for organizing snippets.

    Allows users to organize their snippets into categories/folders.
    """

    firm = models.ForeignKey(
        Firm,
        on_delete=models.CASCADE,
        related_name='snippet_folders',
        help_text='Firm this folder belongs to'
    )

    name = models.CharField(
        max_length=100,
        help_text='Folder name'
    )
    description = models.TextField(
        blank=True,
        help_text='Folder description'
    )

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='snippet_folders',
        help_text='User who created this folder'
    )
    is_shared = models.BooleanField(
        default=False,
        help_text='If True, folder is visible to all team members'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    firm_scoped = FirmScopedManager()

    class Meta:
        db_table = 'snippet_folders'
        ordering = ['name']
        indexes = [
            models.Index(fields=['firm', 'created_by']),
        ]
        unique_together = [('firm', 'name', 'created_by')]

    def __str__(self):
        return self.name

    def snippet_count(self):
        """Return count of snippets in this folder."""
        return self.snippets.count()


# Add folder foreign key to Snippet model
Snippet.add_to_class(
    'folder',
    models.ForeignKey(
        SnippetFolder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='snippets',
        help_text='Folder this snippet belongs to'
    )
)
