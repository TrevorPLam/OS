"""
Communications Module (DOC-33.1 per docs/33 COMMUNICATIONS_SPEC)

Provides native chat/messaging for staff↔staff and staff↔client communications.

This module implements:
- Conversation (thread) model with visibility rules
- Participant model for staff and portal users
- Message model with type support (text, system, attachment, action)
- MessageAttachment linking to governed Documents
- ConversationLink for domain object associations

Per docs/33:
- Communications MUST be in-context with the canonical object graph
- Attachments MUST be governed Documents
- Access MUST be permission-gated and auditable
"""

default_app_config = "modules.communications.apps.CommunicationsConfig"
