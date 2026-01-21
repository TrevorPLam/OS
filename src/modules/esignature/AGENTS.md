# AGENTS.md — E-Signature Module (DocuSign Integration)

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/esignature/`

## Purpose

DocuSign integration for sending documents for electronic signature.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | DocuSignConnection, Envelope, EnvelopeRecipient (~251 LOC) |
| `docusign_service.py` | DocuSign API client |
| `views.py` | OAuth and envelope endpoints |
| `serializers.py` | E-signature serializers |
| `signals.py` | Envelope status update hooks |

## Domain Model

```
DocuSignConnection (OAuth to DocuSign)
    └── Envelope (document sent for signing)
            └── EnvelopeRecipient (individual signers)
```

## Key Models

### DocuSignConnection

OAuth connection to DocuSign:

```python
class DocuSignConnection(models.Model):
    firm: OneToOne[Firm]              # One connection per firm
    
    # OAuth tokens (encrypted)
    access_token: str
    refresh_token: str
    token_expires_at: DateTime
    
    # DocuSign account
    account_id: str
    account_name: str
    base_uri: str                     # API endpoint URL
    
    is_active: bool
    connected_by: FK[User]
    
    last_sync_at: DateTime
    last_error: str
```

### Envelope

Document envelope sent for signing:

```python
class Envelope(models.Model):
    firm: FK[Firm]
    connection: FK[DocuSignConnection]
    
    # DocuSign reference
    docusign_envelope_id: str
    
    # Source document
    source_type: str                  # proposal, contract
    source_id: int
    
    # Status
    status: str                       # created, sent, delivered, signed, completed, voided
    
    # Tracking
    sent_at: DateTime
    completed_at: DateTime
    voided_at: DateTime
    void_reason: str
```

### EnvelopeRecipient

Individual signer in envelope:

```python
class EnvelopeRecipient(models.Model):
    envelope: FK[Envelope]
    
    recipient_id: str                 # DocuSign recipient ID
    
    name: str
    email: str
    role: str                         # signer, cc, approver
    
    # Status
    status: str                       # created, sent, delivered, signed, declined
    signed_at: DateTime
    declined_at: DateTime
    decline_reason: str
    
    # Routing
    routing_order: int                # Signing order
```

## DocuSign Service

```python
from modules.esignature.docusign_service import DocuSignService

service = DocuSignService(firm)

# Create and send envelope
envelope = service.create_envelope(
    document=proposal.get_pdf(),
    document_name="Proposal.pdf",
    recipients=[
        {"name": "John Doe", "email": "john@client.com", "role": "signer"},
        {"name": "Jane Smith", "email": "jane@firm.com", "role": "cc"},
    ],
    subject="Please sign: Consulting Proposal",
    message="Please review and sign the attached proposal.",
)

# Check status
status = service.get_envelope_status(envelope.docusign_envelope_id)

# Void envelope
service.void_envelope(envelope.docusign_envelope_id, reason="Client requested changes")

# Download signed document
signed_pdf = service.download_document(envelope.docusign_envelope_id)
```

## Signing Flow

```
1. Proposal/Contract ready for signature
2. User clicks "Send for Signature"
3. Create Envelope with recipients
4. DocuSign sends email to first recipient
5. Recipients sign in order (routing_order)
6. DocuSign webhook updates status
7. On completion:
   - Download signed document
   - Update Proposal/Contract status
   - Trigger downstream workflows
```

## Webhook Events

DocuSign sends webhooks for status changes:

| Event | Action |
|-------|--------|
| `envelope-sent` | Update status to "sent" |
| `envelope-delivered` | Update status to "delivered" |
| `envelope-completed` | Download signed doc, update source |
| `envelope-declined` | Update status, notify sender |
| `envelope-voided` | Update status to "voided" |
| `recipient-completed` | Update recipient status |

## Integration Points

### Proposals

```python
# From CRM module
proposal.send_for_signature()
# Creates envelope, sends to prospect
```

### Contracts

```python
# From CRM module
contract.send_for_signature()
# Creates envelope, sends to all parties
```

## Token Management

```python
def ensure_valid_token(connection):
    if connection.is_token_expired():
        refresh_token(connection)
```

## Dependencies

- **Depends on**: `firm/`, `crm/`, `documents/`
- **Used by**: Proposals, Contracts
- **External**: DocuSign eSignature API

## URLs

All routes under `/api/v1/esignature/`:

```
# OAuth
GET        /oauth/connect/            # Start DocuSign OAuth
GET        /oauth/callback/

# Connection
GET        /connection/
DELETE     /connection/

# Envelopes
GET        /envelopes/
GET        /envelopes/{id}/
POST       /envelopes/{id}/void/
GET        /envelopes/{id}/download/

# Webhooks
POST       /webhooks/docusign/        # DocuSign Connect webhook
```
