# AGENTS.md — Email Ingestion Module

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/email_ingestion/`

## Purpose

Ingests emails from Gmail/Outlook, maps them to CRM entities, and provides triage workflow.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | EmailConnection, EmailArtifact, EmailMapping, TriageAction (~495 LOC) |
| `services.py` | Email fetching and parsing |
| `retry_service.py` | Failed ingestion retry logic |
| `staleness_service.py` | Stale email detection |
| `views.py` | Admin ingestion management |
| `serializers.py` | Email serializers |

## Domain Model

```
EmailConnection (OAuth to Gmail/Outlook)
    └── EmailArtifact (ingested email)
            ├── EmailMapping (→ Lead, Client, Project)
            └── TriageAction (assignment, categorization)
```

## Key Models

### EmailConnection

OAuth connection to email provider:

```python
class EmailConnection(models.Model):
    firm: FK[Firm]
    
    name: str
    provider: str                     # gmail, outlook
    email_address: str
    
    credentials_encrypted: str        # OAuth tokens (encrypted)
    
    is_active: bool
    last_sync_at: DateTime
```

### EmailArtifact

Ingested email record:

```python
class EmailArtifact(models.Model):
    firm: FK[Firm]
    connection: FK[EmailConnection]
    
    # Email metadata (content NOT stored by default)
    message_id: str                   # Email Message-ID header
    subject: str
    from_address: str
    to_addresses: JSONField
    cc_addresses: JSONField
    received_at: DateTime
    
    # Processing
    status: str                       # pending, mapped, triaged, archived
    
    # Mapping (where this email belongs)
    mapped_to_type: str               # lead, client, project
    mapped_to_id: int
    mapping_confidence: Decimal       # 0.0-1.0
    
    # Governance
    has_attachments: bool
    attachment_count: int
    is_archived: bool
```

### EmailMapping

Suggested or confirmed mapping:

```python
class EmailMapping(models.Model):
    artifact: FK[EmailArtifact]
    
    entity_type: str                  # lead, prospect, client, project
    entity_id: int
    confidence: Decimal
    
    mapping_method: str               # auto, manual, ai_suggested
    confirmed_by: FK[User]
    confirmed_at: DateTime
```

## Ingestion Flow

```
1. EmailConnection configured (OAuth)
2. Background job fetches new emails
3. For each email:
   a. Create EmailArtifact
   b. Parse headers (no content stored)
   c. Auto-map based on:
      - From address → Contact/Lead lookup
      - Subject patterns → Project matching
      - Thread ID → Existing conversation
   d. Queue for triage if low confidence
4. Staff reviews triage queue
5. Confirmed mappings update entity records
```

## Mapping Logic

```python
def suggest_mapping(artifact):
    """
    Mapping priority:
    1. Exact email match to Contact → Client
    2. Exact email match to Lead → Lead
    3. Thread reply → Same entity as thread
    4. Subject keyword match → Project
    5. No match → Triage queue
    """
```

## Retry Logic

`retry_service.py` handles failed ingestions:

```python
from modules.email_ingestion.retry_service import RetryService

service = RetryService()

# Retry failed artifacts
service.retry_failed(max_attempts=3)

# Exponential backoff
# Attempt 1: immediate
# Attempt 2: 5 minutes
# Attempt 3: 30 minutes
# After max: moved to DLQ
```

## Staleness Detection

`staleness_service.py` detects stale connections:

```python
from modules.email_ingestion.staleness_service import check_staleness

# Alert if no sync in 24 hours
stale_connections = check_staleness(threshold_hours=24)
```

## Privacy Rules

1. **No Content Storage**: Email body is NOT stored by default
2. **Metadata Only**: Subject, from, to, dates
3. **Opt-in Content**: Attachments stored only if explicitly enabled
4. **Encrypted Credentials**: OAuth tokens encrypted at rest

## Dependencies

- **Depends on**: `firm/`, `crm/`, `clients/`, `projects/`
- **Used by**: CRM (activity feed), Projects (communication log)
- **External**: Google Gmail API, Microsoft Graph API

## URLs

All routes under `/api/v1/email-ingestion/`:

```
# Connections
GET/POST   /connections/
GET/PUT    /connections/{id}/
POST       /connections/{id}/sync-now/
GET        /connections/{id}/status/

# Artifacts
GET        /artifacts/
GET        /artifacts/{id}/
POST       /artifacts/{id}/map/
POST       /artifacts/{id}/archive/

# Triage
GET        /triage-queue/
POST       /triage-queue/bulk-map/

# Admin
GET        /stats/
GET        /failed/
POST       /failed/{id}/retry/
```
