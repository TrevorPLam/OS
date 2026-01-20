"""
Meta-commentary:
- Current Status: Adds safety invariants for MFA rate limiting and constant-time OTP checks.
- Mapping: Covers T-127 (constant-time OTP comparison) and T-137 (MFA rate limiting).
- Reasoning: MFA endpoints are high-value targets; enforce deterministic security guards in tests.
- Assumption: Django cache is available for rate limit counters in test runs.
- Limitation: Rate limit assertions rely on django-ratelimit's cache-based behavior.
"""

import hmac

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.auth.mfa_views import mfa_verify_sms, mfa_verify_totp

User = get_user_model()


@pytest.mark.django_db
def test_sms_mfa_uses_constant_time_comparison(monkeypatch):
    """Ensure SMS OTP verification uses hmac.compare_digest for constant-time checks."""
    user = User.objects.create_user(username="mfa_sms_user", password="pass1234")
    cache.set(f"sms_otp_enroll_{user.id}", "123456", timeout=60)

    calls = []
    original_compare_digest = hmac.compare_digest

    def tracking_compare_digest(a, b):
        # Keep behavior consistent while tracking invocation for security assurance.
        calls.append((a, b))
        return original_compare_digest(a, b)

    monkeypatch.setattr(hmac, "compare_digest", tracking_compare_digest)

    factory = APIRequestFactory()

    # Positive path: valid OTP should succeed and use compare_digest
    request = factory.post("/api/auth/mfa/verify/sms/", {"code": "123456"}, format="json")
    force_authenticate(request, user=user)
    response = mfa_verify_sms(request)

    assert response.status_code == 200
    assert calls, "compare_digest must be used for OTP comparisons"

    # Reset tracking for negative path assertion
    calls.clear()

    # Negative path: invalid OTP should still invoke compare_digest and fail in constant time
    request = factory.post("/api/auth/mfa/verify/sms/", {"code": "000000"}, format="json")
    force_authenticate(request, user=user)
    response = mfa_verify_sms(request)

    assert response.status_code in (400, 401)
    assert calls, "compare_digest must be used for OTP comparisons even on invalid codes"

    assert response.status_code == 200
    assert calls, "compare_digest must be used for OTP comparisons"


@pytest.mark.django_db
def test_totp_verification_rate_limited_by_ip():
    """Verify TOTP verification requests are rate limited per IP."""
    user = User.objects.create_user(username="mfa_totp_user", password="pass1234")
    cache.clear()

    factory = APIRequestFactory()
    for attempt in range(6):
        request = factory.post(
            "/api/auth/mfa/verify/totp/",
            {"code": "000000"},
            format="json",
            REMOTE_ADDR="203.0.113.42",
        )
        force_authenticate(request, user=user)
        response = mfa_verify_totp(request)

        # Note: We do not enroll a TOTP device for this user in this test.
        # mfa_verify_totp returns 404 when no confirmed TOTP device exists, so both
        # 400 (invalid code) and 404 (no device) are acceptable for the first 5 attempts.
        # The security property under test is that the 6th request from the same IP
        # is rate limited (429), regardless of device-enrollment state.
        if attempt < 5:
            assert response.status_code in {400, 404}
        else:
            assert response.status_code == 429
