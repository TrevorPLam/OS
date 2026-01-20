"""
Database configuration helpers for query timeouts and slow query monitoring.
"""

from __future__ import annotations

import os

DEFAULT_STATEMENT_TIMEOUT_MS = 5000
DEFAULT_SLOW_QUERY_THRESHOLD_MS = 100


def _parse_non_negative_int(value: str | None, setting_name: str) -> int | None:
    if value is None:
        return None

    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise ValueError(f"{setting_name} must be an integer.") from exc

    if parsed_value < 0:
        raise ValueError(f"{setting_name} must be >= 0.")

    return parsed_value


def get_statement_timeout_ms() -> int:
    parsed_value = _parse_non_negative_int(
        os.environ.get("DB_STATEMENT_TIMEOUT_MS"),
        "DB_STATEMENT_TIMEOUT_MS",
    )
    return DEFAULT_STATEMENT_TIMEOUT_MS if parsed_value is None else parsed_value


def get_slow_query_threshold_ms() -> int:
    parsed_value = _parse_non_negative_int(
        os.environ.get("DB_SLOW_QUERY_THRESHOLD_MS"),
        "DB_SLOW_QUERY_THRESHOLD_MS",
    )
    return DEFAULT_SLOW_QUERY_THRESHOLD_MS if parsed_value is None else parsed_value


def build_database_options(engine: str) -> dict[str, str]:
    if engine != "django.db.backends.postgresql":
        return {}

    statement_timeout_ms = get_statement_timeout_ms()
    if statement_timeout_ms == 0:
        return {}

    return {"options": f"-c statement_timeout={statement_timeout_ms}"}
