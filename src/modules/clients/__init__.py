"""
Clients Module - Post-Sale Client Management

This module handles all post-sale client operations after a Proposal is accepted.
Separates from CRM which handles pre-sale (Leads, Prospects, Proposals).
"""

# Import portal branding models to register them with Django
from .portal_branding import DomainVerificationRecord, PortalBranding  # noqa: F401
