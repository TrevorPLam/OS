"""
Custom throttling classes for rate limiting.

Protects API from abuse and DDoS attacks.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Throttle for burst requests - 100 requests per minute.
    Protects against rapid-fire requests.
    """

    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    """
    Throttle for sustained requests - 1000 requests per hour.
    Protects against sustained abuse.
    """

    scope = "sustained"


class AnonymousRateThrottle(AnonRateThrottle):
    """
    Throttle for anonymous users - 20 requests per hour.
    Forces authentication for heavy API use.
    """

    scope = "anon"


class PaymentRateThrottle(UserRateThrottle):
    """
    Special throttle for payment endpoints - 10 requests per minute.
    Prevents payment abuse and fraud attempts.
    """

    scope = "payment"


class UploadRateThrottle(UserRateThrottle):
    """
    Special throttle for file uploads - 30 requests per hour.
    Prevents storage abuse.
    """

    scope = "upload"
