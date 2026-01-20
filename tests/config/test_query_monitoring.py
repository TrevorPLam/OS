import logging
from contextlib import contextmanager

import pytest
from django.db import DatabaseError

from config import database, query_monitoring


def test_build_database_options_returns_postgres_statement_timeout(monkeypatch):
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "6000")

    options = database.build_database_options("django.db.backends.postgresql")

    assert options == {"options": "-c statement_timeout=6000"}


def test_build_database_options_empty_for_non_postgres(monkeypatch):
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "5000")

    options = database.build_database_options("django.db.backends.sqlite3")

    assert options == {}


def test_get_statement_timeout_ms_accepts_zero(monkeypatch):
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "0")

    assert database.get_statement_timeout_ms() == 0


def test_get_statement_timeout_ms_rejects_invalid(monkeypatch):
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "invalid")

    with pytest.raises(ValueError, match="DB_STATEMENT_TIMEOUT_MS must be an integer"):
        database.get_statement_timeout_ms()


def test_query_timing_wrapper_logs_slow_query(monkeypatch, caplog):
    times = iter([1.0, 1.2])
    monkeypatch.setattr(query_monitoring, "perf_counter", lambda: next(times))

    wrapper = query_monitoring.QueryTimingWrapper(100, logging.getLogger("config.query_monitoring"))

    with caplog.at_level(logging.WARNING, logger="config.query_monitoring"):
        result = wrapper(lambda *_: "ok", "", (), False, None)

    assert result == "ok"
    assert "Slow database query detected" in caplog.text


def test_query_timing_wrapper_logs_statement_timeout(monkeypatch, caplog):
    times = iter([1.0, 1.01])
    monkeypatch.setattr(query_monitoring, "perf_counter", lambda: next(times))

    wrapper = query_monitoring.QueryTimingWrapper(100, logging.getLogger("config.query_monitoring"))

    def _raise_timeout(*_args, **_kwargs):
        raise DatabaseError("canceling statement due to statement timeout")

    with caplog.at_level(logging.ERROR, logger="config.query_monitoring"):
        with pytest.raises(DatabaseError):
            wrapper(_raise_timeout, "", (), False, None)

    assert "Database statement timeout detected" in caplog.text


def test_query_timeout_monitoring_middleware_wraps_execute(monkeypatch):
    captured = {}

    @contextmanager
    def _fake_wrapper(_wrapper):
        captured["wrapper"] = _wrapper
        yield

    def _execute_wrapper(wrapper):
        return _fake_wrapper(wrapper)

    monkeypatch.setattr(query_monitoring.connection, "execute_wrapper", _execute_wrapper)

    middleware = query_monitoring.QueryTimeoutMonitoringMiddleware(lambda _request: "response")

    response = middleware(object())

    assert response == "response"
    assert isinstance(captured.get("wrapper"), query_monitoring.QueryTimingWrapper)
