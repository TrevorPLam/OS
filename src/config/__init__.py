"""
Configuration package initialization.

ASSESS-C3.10: Enable SQLite foreign key constraints for test determinism.
"""

from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def enable_sqlite_foreign_keys(sender, connection, **kwargs):
    """
    Enable foreign key constraints in SQLite.

    SQLite disables foreign key constraints by default for backward compatibility.
    This ensures referential integrity is enforced in tests using SQLite.

    Note: Production uses PostgreSQL which always enforces foreign keys.
    """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
