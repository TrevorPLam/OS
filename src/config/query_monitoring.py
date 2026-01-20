"""
Slow query logging and timeout monitoring middleware.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from time import perf_counter

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("config.query_monitoring")


class QueryTimingWrapper:
    def __init__(self, threshold_ms: int, log: logging.Logger) -> None:
        self.threshold_ms = threshold_ms
        self.log = log

    def __call__(
        self,
        execute: Callable,
        sql: str,
        params: object,
        many: bool,
        context: object,
    ) -> object:
        start_time = perf_counter()
        try:
            return execute(sql, params, many, context)
        except DatabaseError as exc:
            self._log_timeout(exc)
            raise
        finally:
            elapsed_ms = (perf_counter() - start_time) * 1000
            self._log_slow_query(elapsed_ms, sql)

    def _log_slow_query(self, elapsed_ms: float, sql: str) -> None:
        if elapsed_ms < self.threshold_ms:
            return

        self.log.warning(
            "Slow database query detected",
            extra={
                "duration_ms": round(elapsed_ms, 2),
                "sql_preview": sql[:200],
            },
        )

    def _log_timeout(self, error: DatabaseError) -> None:
        if not _is_statement_timeout(error):
            return

        self.log.error(
            "Database statement timeout detected",
            extra={"error": error.__class__.__name__},
        )


class QueryTimeoutMonitoringMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.threshold_ms = getattr(settings, "DB_SLOW_QUERY_THRESHOLD_MS", 100)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        wrapper = QueryTimingWrapper(self.threshold_ms, logger)
        with connection.execute_wrapper(wrapper):
            return self.get_response(request)


def _is_statement_timeout(error: DatabaseError) -> bool:
    message = str(error).lower()
    return "statement timeout" in message or "query timeout" in message
