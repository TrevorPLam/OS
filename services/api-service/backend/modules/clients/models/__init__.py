"""
Clients Models - Post-Sale Client Management

This module contains all post-sale client entities.
Clients are created when a Proposal is accepted in the CRM module.

TIER 0: All clients MUST belong to exactly one Firm for tenant isolation.
TIER 2.6: Organizations allow optional cross-client collaboration within a firm.
"""

from .organizations import Organization
from .clients import Client
from .portal_users import ClientPortalUser
from .notes import ClientNote
from .engagements import ClientEngagement, EngagementLine
from .comments import ClientComment, ClientChatThread, ClientMessage
from .contacts import ContactManager, Contact, ContactImport, ContactBulkUpdate
from .email_opt_in import EmailOptInRequest, EmailUnsubscribeToken
from .health_scores import ClientHealthScore
from .consents import ConsentRecord

__all__ = [
    'Organization',
    'Client',
    'ClientPortalUser',
    'ClientNote',
    'ClientEngagement',
    'EngagementLine',
    'ClientComment',
    'ClientChatThread',
    'ClientMessage',
    'ContactManager',
    'Contact',
    'ContactImport',
    'ContactBulkUpdate',
    'EmailOptInRequest',
    'EmailUnsubscribeToken',
    'ClientHealthScore',
    'ConsentRecord',
]
