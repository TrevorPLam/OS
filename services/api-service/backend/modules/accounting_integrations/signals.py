"""Signals for Accounting Integrations."""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Placeholder for future signal handlers
# Example: Auto-sync invoices when they are marked as sent
