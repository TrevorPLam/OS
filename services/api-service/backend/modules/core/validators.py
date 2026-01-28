"""
Security validators for protecting against common web vulnerabilities.

These validators are used across the application to ensure input safety.
"""

import ipaddress
import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_safe_url(value):
    """
    Validate that a URL does not point to internal/private networks.

    Protects against Server-Side Request Forgery (SSRF) attacks by blocking:
    - Private IP ranges (10.x.x.x, 172.16-31.x.x, 192.168.x.x)
    - Loopback addresses (127.x.x.x, localhost)
    - Link-local addresses (169.254.x.x)
    - Cloud metadata endpoints (169.254.169.254)
    - IPv6 private/link-local addresses

    Args:
        value: URL string to validate

    Raises:
        ValidationError: If URL points to a private/internal network

    Example:
        >>> validate_safe_url("https://example.com")  # OK
        >>> validate_safe_url("http://192.168.1.1")  # Raises ValidationError
        >>> validate_safe_url("http://localhost:8080")  # Raises ValidationError
    """
    if not value:
        return

    try:
        parsed = urlparse(value)
        hostname = parsed.hostname

        if not hostname:
            raise ValidationError("Invalid URL: no hostname found")

        # Block localhost variations
        localhost_patterns = [
            "localhost",
            "localhost.localdomain",
            "127.0.0.1",
            "::1",
            "0.0.0.0",  # noqa: S104 - intentionally blocking all-interface binding
        ]

        hostname_lower = hostname.lower()
        if hostname_lower in localhost_patterns or hostname_lower.startswith("localhost."):
            raise ValidationError("URLs pointing to localhost are not allowed for security reasons.")

        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)

            # Block private networks
            if ip.is_private:
                raise ValidationError("URLs pointing to private IP addresses are not allowed for security reasons.")

            # Block loopback
            if ip.is_loopback:
                raise ValidationError("URLs pointing to loopback addresses are not allowed for security reasons.")

            # Block link-local (including AWS/cloud metadata endpoint 169.254.169.254)
            if ip.is_link_local:
                raise ValidationError("URLs pointing to link-local addresses are not allowed for security reasons.")

            # Block reserved addresses
            if ip.is_reserved:
                raise ValidationError("URLs pointing to reserved addresses are not allowed for security reasons.")

            # Block multicast
            if ip.is_multicast:
                raise ValidationError("URLs pointing to multicast addresses are not allowed for security reasons.")

        except ValueError:
            # Not an IP address - it's a hostname, which is fine
            # Additional check: block internal DNS patterns
            internal_patterns = [
                r"\.internal$",
                r"\.local$",
                r"\.localhost$",
                r"\.corp$",
                r"\.lan$",
                r"\.home$",
                r"^metadata\.",
                r"^internal\.",
                r"^private\.",
            ]

            for pattern in internal_patterns:
                if re.search(pattern, hostname_lower):
                    raise ValidationError(
                        "URLs with internal hostname patterns are not allowed for security reasons."
                    ) from None

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}") from e
