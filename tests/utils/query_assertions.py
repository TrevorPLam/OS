"""Query-count assertion helpers for endpoint performance tests.

Meta-commentary:
- Current Status: Lightweight context manager that enforces max query counts in tests.
- Follow-up (T-059): Expand coverage to additional endpoints as they gain baseline budgets.
- Assumption: Tests run with SQLite in CI, so query counts are compared relative to that adapter.
- Limitation: Budgets are coarse caps, not exact query plans; adjust when serializers change.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection
from django.test.utils import CaptureQueriesContext


@contextmanager
def assert_max_queries(max_queries: int) -> Iterator[CaptureQueriesContext]:
    """Assert that the wrapped block executes no more than the provided query budget.

    Use this in endpoint tests to guard against N+1 regressions while keeping budgets
    intentionally permissive for serializer evolution and middleware overhead.
    """
    with CaptureQueriesContext(connection) as context:
        yield context

    executed = len(context)
    assert executed <= max_queries, (
        f"Expected at most {max_queries} queries, but captured {executed}. "
        "Inspect viewset/select_related/prefetch_related usage for regressions."
    )
