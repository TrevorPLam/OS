"""
Portal Rate Limiting (DOC-24.1).

Per SECURITY_MODEL docs/03-reference/requirements/DOC-24.md: "Rate limiting and abuse detection for portal endpoints."

Portal endpoints have stricter rate limits than staff endpoints to prevent abuse.
"""

from rest_framework.throttling import UserRateThrottle


class PortalRateThrottle(UserRateThrottle):
    """
    Rate limit for general portal API requests.

    Stricter than staff limits to prevent abuse from compromised client accounts.

    Rate: 30 requests per minute (conservative)
    """
    scope = 'portal'


class PortalBurstThrottle(UserRateThrottle):
    """
    Burst rate limit for portal requests.

    Allows brief bursts but limits sustained traffic.

    Rate: 60 requests per minute
    """
    scope = 'portal_burst'


class PortalSustainedThrottle(UserRateThrottle):
    """
    Sustained rate limit for portal requests.

    Limits long-term usage to prevent abuse.

    Rate: 300 requests per hour
    """
    scope = 'portal_sustained'


class PortalUploadThrottle(UserRateThrottle):
    """
    Rate limit for portal file uploads.

    Prevents storage abuse and DoS attacks.

    Rate: 10 uploads per hour
    """
    scope = 'portal_upload'


class PortalDownloadThrottle(UserRateThrottle):
    """
    Rate limit for portal file downloads.

    Prevents bandwidth abuse.

    Rate: 50 downloads per hour
    """
    scope = 'portal_download'


# Usage in ViewSets:
# from api.portal.throttling import PortalRateThrottle, PortalUploadThrottle
#
# class PortalDocumentViewSet(viewsets.ReadOnlyModelViewSet):
#     throttle_classes = [PortalRateThrottle, PortalUploadThrottle]
#     ...
