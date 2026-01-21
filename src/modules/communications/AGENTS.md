# AGENTS.md — Communications Module

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/communications/`

## Purpose

Internal messaging system for conversations and message threads.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Conversation, Message, MessageThread |
| `views.py` | Communications endpoints |

## Domain Model

```
Conversation (between staff and client)
    └── Message (individual messages)
```

## Key Models

### Conversation

Message thread:

```python
class Conversation(models.Model):
    firm: FK[Firm]
    
    # Participants
    participants: M2M[User]
    client: FK[Client]                # If client conversation
    
    subject: str
    status: str                       # active, archived
    
    # Tracking
    last_message_at: DateTime
    unread_count: int
```

### Message

Individual message:

```python
class Message(models.Model):
    conversation: FK[Conversation]
    
    sender: FK[User]
    content: str
    
    sent_at: DateTime
    read_at: DateTime
    
    # Attachments
    has_attachments: bool
```

## Dependencies

- **Depends on**: `firm/`, `clients/`
- **Used by**: Client portal (messaging)

## URLs

All routes under `/api/v1/communications/`:

```
GET/POST   /conversations/
GET        /conversations/{id}/
GET/POST   /conversations/{id}/messages/
POST       /conversations/{id}/mark-read/
```
