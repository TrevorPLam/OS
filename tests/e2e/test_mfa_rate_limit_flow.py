"""
Meta-commentary:
- Current Status: Adds an end-to-end-style MFA rate-limit regression test.
- Mapping: Exercises the T-137 MFA rate limit policy via the view entrypoint.
- Reasoning: Ensure the HTTP-facing path blocks brute-force attempts consistently.
- Assumption: APIRequestFactory mirrors the production request path for ratelimit usage.
- Limitation: Does not validate upstream proxies or load balancer IP headers.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIRequestFactory, force_authenticate

from modules.auth.mfa_views import mfa_verify_totp

User = get_user_model()


@pytest.mark.e2e
@pytest.mark.django_db
def test_mfa_totp_rate_limit_blocks_after_five_attempts():
    """Simulate repeated verification attempts to validate rate limiting."""
    user = User.objects.create_user(username="mfa_rate_user", password="pass1234")
    cache.clear()

    factory = APIRequestFactory()
    responses = []
    for _ in range(6):
        request = factory.post(
            "/api/auth/mfa/verify/totp/",
            {"code": "000000"},
            format="json",
            REMOTE_ADDR="203.0.113.99",
        )
        force_authenticate(request, user=user)
        responses.append(mfa_verify_totp(request))

    # No TOTP device is configured for this user; the initial 400/404 responses
    # reflect invalid verification attempts. This test is specifically asserting
    # that the IP-based rate limiting still triggers with a 429 after five tries,
    # regardless of the underlying TOTP device state.
    assert all(response.status_code in {400, 404} for response in responses[:5])
    assert responses[5].status_code == 429
