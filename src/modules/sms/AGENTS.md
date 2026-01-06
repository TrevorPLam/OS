# AGENTS.md — SMS Module (Twilio Integration)

Last Updated: 2026-01-06
Applies To: `src/modules/sms/`

## Purpose

SMS messaging via Twilio with two-way conversations and campaign support.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | SMSConfig, SMSMessage, SMSConversation, SMSCampaign |
| `twilio_service.py` | Twilio API client |
| `views.py` | SMS endpoints |
| `serializers.py` | SMS serializers |
| `webhooks.py` | Twilio webhook handlers |

## Domain Model

```
SMSConfig (Twilio credentials per firm)
    └── SMSConversation (two-way thread)
            └── SMSMessage (individual messages)
    └── SMSCampaign (bulk messaging)
```

## Key Models

### SMSConfig

Twilio configuration:

```python
class SMSConfig(models.Model):
    firm: OneToOne[Firm]
    
    account_sid: str                  # Twilio Account SID
    auth_token: str                   # Encrypted
    phone_number: str                 # Twilio phone number
    
    is_enabled: bool
    
    # Opt-out management
    auto_opt_out_keywords: JSONField  # ["STOP", "UNSUBSCRIBE"]
```

### SMSMessage

Individual message:

```python
class SMSMessage(models.Model):
    firm: FK[Firm]
    conversation: FK[SMSConversation]
    
    direction: str                    # inbound, outbound
    
    from_number: str
    to_number: str
    body: str
    
    # Twilio tracking
    twilio_sid: str
    status: str                       # queued, sent, delivered, failed
    
    sent_at: DateTime
    delivered_at: DateTime
    
    # Cost tracking
    segments: int                     # Message segments
    price: Decimal
```

### SMSConversation

Two-way thread:

```python
class SMSConversation(models.Model):
    firm: FK[Firm]
    
    phone_number: str                 # Contact's phone
    
    # Linked entity
    contact_type: str                 # lead, contact, client
    contact_id: int
    
    status: str                       # active, opted_out, blocked
    last_message_at: DateTime
```

## Twilio Service

```python
from modules.sms.twilio_service import TwilioService

service = TwilioService(firm)

# Send message
message = service.send_sms(
    to="+15551234567",
    body="Your appointment is confirmed for tomorrow at 10 AM.",
)

# Check status
status = service.get_message_status(twilio_sid)
```

## Webhook Handling

Twilio sends webhooks for:

| Event | Handler |
|-------|---------|
| Message received | Create inbound SMSMessage |
| Delivery status | Update SMSMessage status |
| Opt-out | Mark conversation as opted_out |

```python
# In webhooks.py
@csrf_exempt
def twilio_webhook(request):
    # Validate Twilio signature
    # Process event
    # Return TwiML response
```

## Opt-Out Compliance

Automatic opt-out handling:

```python
# If inbound message matches opt-out keyword
if message.body.upper() in config.auto_opt_out_keywords:
    conversation.status = "opted_out"
    # Send confirmation
    service.send_sms(to=message.from_number, body="You have been unsubscribed.")
```

## Dependencies

- **Depends on**: `firm/`, `clients/`, `crm/`
- **Used by**: Marketing automation, appointment reminders
- **External**: Twilio API

## URLs

All routes under `/api/v1/sms/`:

```
# Config
GET/PUT    /config/
POST       /config/test/

# Messages
GET        /messages/
GET        /messages/{id}/
POST       /messages/send/

# Conversations
GET        /conversations/
GET        /conversations/{id}/
GET        /conversations/{id}/messages/

# Webhooks
POST       /webhooks/twilio/
```
