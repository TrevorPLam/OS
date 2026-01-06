# AGENTS.md — Support Module (Ticketing & SLA)

Last Updated: 2026-01-06
Applies To: `src/modules/support/`

## Purpose

Support ticketing system with SLA tracking, surveys, and NPS.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Ticket, TicketComment, SLAPolicy, Survey, NPSResponse |
| `views.py` | Support endpoints |
| `serializers.py` | Support serializers |

## Domain Model

```
SLAPolicy (response/resolution times)
Ticket (support request)
    └── TicketComment (conversation)
    └── TicketActivity (audit trail)
Survey (satisfaction survey)
    └── SurveyResponse
NPSScore (Net Promoter Score tracking)
```

## Key Models

### Ticket

Support ticket:

```python
class Ticket(models.Model):
    firm: FK[Firm]
    
    ticket_number: str                # Auto-generated
    subject: str
    description: str
    
    # Classification
    priority: str                     # low, medium, high, urgent
    category: str                     # billing, technical, general
    
    status: str                       # open, pending, resolved, closed
    
    # Assignment
    requester: FK[User/Contact]
    assigned_to: FK[User]
    
    # SLA tracking
    sla_policy: FK[SLAPolicy]
    first_response_at: DateTime
    first_response_due: DateTime
    resolution_due: DateTime
    resolved_at: DateTime
    
    # Flags
    is_sla_breached: bool
```

### SLAPolicy

SLA configuration:

```python
class SLAPolicy(models.Model):
    firm: FK[Firm]
    
    name: str
    
    # Response times (minutes)
    first_response_urgent: int
    first_response_high: int
    first_response_medium: int
    first_response_low: int
    
    # Resolution times (minutes)
    resolution_urgent: int
    resolution_high: int
    resolution_medium: int
    resolution_low: int
    
    # Business hours
    business_hours_only: bool
```

### Survey

Post-resolution survey:

```python
class Survey(models.Model):
    firm: FK[Firm]
    
    name: str
    questions: JSONField              # Survey questions
    
    trigger: str                      # ticket_resolved, engagement_complete
```

## SLA Tracking

```python
def check_sla_breach(ticket):
    now = timezone.now()
    
    # First response SLA
    if not ticket.first_response_at and now > ticket.first_response_due:
        ticket.is_sla_breached = True
        notify_manager(ticket, "first_response_breach")
    
    # Resolution SLA
    if ticket.status != "resolved" and now > ticket.resolution_due:
        ticket.is_sla_breached = True
        notify_manager(ticket, "resolution_breach")
```

## Dependencies

- **Depends on**: `firm/`, `clients/`
- **Used by**: Client portal (submit tickets)

## URLs

All routes under `/api/v1/support/`:

```
# Tickets
GET/POST   /tickets/
GET/PUT    /tickets/{id}/
POST       /tickets/{id}/assign/
POST       /tickets/{id}/resolve/
POST       /tickets/{id}/close/

# Comments
GET/POST   /tickets/{id}/comments/

# SLA
GET/POST   /sla-policies/
GET/PUT    /sla-policies/{id}/

# Surveys
GET/POST   /surveys/
GET        /surveys/{id}/responses/

# Reports
GET        /reports/sla-compliance/
GET        /reports/ticket-volume/
```
