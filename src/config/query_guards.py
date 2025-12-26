"""
Query guardrails for API endpoints.
"""

from contextlib import contextmanager

from django.conf import settings
from django.db import connection


@contextmanager
def query_timeout(milliseconds: int):
    """
    Apply a per-request statement timeout where supported.

    Currently only supported on PostgreSQL via SET LOCAL statement_timeout.
    """
    if not milliseconds:
        yield
        return

    if connection.vendor != "postgresql":
        yield
        return

    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = %s", [milliseconds])
        yield


class QueryTimeoutMixin:
    """Mixin to wrap list queries in a statement timeout."""

    query_timeout_ms = getattr(settings, "API_QUERY_TIMEOUT_MS", 3000)

    def with_query_timeout(self):
        return query_timeout(self.query_timeout_ms)

    def list(self, request, *args, **kwargs):
        with self.with_query_timeout():
            return super().list(request, *args, **kwargs)
