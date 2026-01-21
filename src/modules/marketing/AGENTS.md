# AGENTS.md — Marketing Module

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/marketing/`

## Purpose

Marketing automation primitives: tags, segments, email templates, and campaigns.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Tag, Segment, EmailTemplate, Campaign, CampaignRecipient |
| `views.py` | Marketing endpoints |
| `serializers.py` | Marketing serializers |
| `queue.py` | Campaign send queue |
| `jobs.py` | Background campaign jobs |

## Domain Model

```
Tag (contact classification)
Segment (dynamic grouping)
EmailTemplate (reusable template)
Campaign (email campaign)
    └── CampaignRecipient (individual sends)
```

## Key Models

### Tag

Contact classification:

```python
class Tag(models.Model):
    firm: FK[Firm]
    
    name: str
    color: str                        # Hex color for UI
    
    # Auto-apply rules (optional)
    auto_apply_rules: JSONField
```

### Segment

Dynamic contact grouping:

```python
class Segment(models.Model):
    firm: FK[Firm]
    
    name: str
    description: str
    
    # Filter criteria
    filter_criteria: JSONField        # Query builder output
    
    # Cached count
    member_count: int
    last_calculated_at: DateTime
```

### EmailTemplate

Reusable email template:

```python
class EmailTemplate(models.Model):
    firm: FK[Firm]
    
    name: str
    subject: str
    
    # Content
    html_content: str
    text_content: str
    
    # Variables
    available_variables: JSONField    # ["first_name", "company", ...]
    
    # Categorization
    category: str                     # newsletter, promotional, transactional
```

### Campaign

Email campaign:

```python
class Campaign(models.Model):
    firm: FK[Firm]
    
    name: str
    status: str                       # draft, scheduled, sending, sent, paused
    
    # Content
    template: FK[EmailTemplate]
    subject_override: str
    
    # Recipients
    segments: M2M[Segment]
    
    # Scheduling
    scheduled_at: DateTime
    sent_at: DateTime
    
    # Stats
    total_recipients: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    bounced_count: int
    unsubscribed_count: int
```

## Segment Criteria

```json
{
  "operator": "AND",
  "conditions": [
    { "field": "tags", "operator": "contains", "value": "interested" },
    { "field": "last_activity_at", "operator": "after", "value": "-30d" },
    { "field": "status", "operator": "not_equals", "value": "churned" }
  ]
}
```

## Campaign Flow

```
1. Create campaign (status=draft)
2. Select template and segments
3. Preview and test
4. Schedule or send immediately
5. Background job processes:
   a. Calculate segment members
   b. Deduplicate recipients
   c. Create CampaignRecipient records
   d. Queue emails for sending
6. Track opens/clicks via tracking pixels
7. Handle bounces and unsubscribes
```

## Dependencies

- **Depends on**: `firm/`, `clients/`, `crm/`
- **Used by**: `automation/` (workflow actions)
- **Related**: Email sending infrastructure

## URLs

All routes under `/api/v1/marketing/`:

```
# Tags
GET/POST   /tags/
GET/PUT    /tags/{id}/

# Segments
GET/POST   /segments/
GET/PUT    /segments/{id}/
GET        /segments/{id}/members/
POST       /segments/{id}/calculate/

# Templates
GET/POST   /templates/
GET/PUT    /templates/{id}/
POST       /templates/{id}/preview/

# Campaigns
GET/POST   /campaigns/
GET/PUT    /campaigns/{id}/
POST       /campaigns/{id}/schedule/
POST       /campaigns/{id}/send/
POST       /campaigns/{id}/pause/
GET        /campaigns/{id}/stats/
```
