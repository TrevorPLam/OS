from modules.core.telemetry import sanitize_telemetry_fields


def test_sanitize_telemetry_fields_redacts_sensitive_strings():
    fields = {
        "email": "user@example.com",
        "subject": "Sensitive Subject",
        "count": 3,
        "duration_ms": 120,
        "status": "success",
        "custom": "should-not-leak",
        "nested": {"detail": "secret"},
    }

    sanitized = sanitize_telemetry_fields(fields)

    assert sanitized["email"] == "[REDACTED]"
    assert sanitized["subject"] == "[REDACTED]"
    assert sanitized["custom"] == "[REDACTED]"
    assert sanitized["nested"] == "[REDACTED]"
    assert sanitized["count"] == 3
    assert sanitized["duration_ms"] == 120
    assert sanitized["status"] == "success"


def test_sanitize_telemetry_fields_allows_numeric_values():
    fields = {
        "retries": 2,
        "success": True,
        "ratio": 0.5,
        "empty": None,
    }

    sanitized = sanitize_telemetry_fields(fields)

    assert sanitized == fields
