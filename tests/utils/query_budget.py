"""
Query budget helpers for Django API tests.

Meta-commentary:
- Current Status: Provides a shared query budget context manager for performance-marked tests.
- Mapping: Imported by API endpoint tests that guard against N+1 regressions.
- Reasoning: Centralizes query counting to keep guardrails consistent and maintainable.
- Assumption: Query counts are coarse guardrails and vary between SQLite and Postgres.
- Limitation: Budgets are maximum thresholds, not exact query plans.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection
from django.test.utils import CaptureQueriesContext


@contextmanager
def assert_max_queries(max_queries: int) -> Iterator[CaptureQueriesContext]:
    """Assert that the wrapped block executes within the provided query budget."""
    with CaptureQueriesContext(connection) as context:
        yield context

    executed = len(context)
    assert executed <= max_queries, (
        f"Expected at most {max_queries} queries, but captured {executed}. "
        "Inspect queryset/select_related/prefetch_related usage for regressions."
    )
