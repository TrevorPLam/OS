"""
Core Models - Shared Infrastructure

This module contains models that are used across multiple apps.
"""

# Import purge models to register them with Django
from modules.core.purge import PurgedContent  # noqa: F401

__all__ = ["PurgedContent"]
