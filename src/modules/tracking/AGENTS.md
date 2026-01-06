# AGENTS.md — Tracking Module (Site & Event Analytics)

Last Updated: 2026-01-06
Applies To: `src/modules/tracking/`

## Purpose

Site tracking and event analytics for lead scoring and attribution.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | TrackingSession, TrackingEvent, PageView |
| `views.py` | Tracking ingestion endpoints |
| `serializers.py` | Tracking serializers |

## Domain Model

```
TrackingSession (visitor session)
    └── PageView (page visits)
    └── TrackingEvent (custom events)
```

## Key Models

### TrackingSession

Visitor session:

```python
class TrackingSession(models.Model):
    firm: FK[Firm]
    
    visitor_id: str                   # Anonymous tracking ID
    
    # Attribution
    utm_source: str
    utm_medium: str
    utm_campaign: str
    referrer: str
    
    # Identity resolution
    contact: FK[Contact]              # If identified
    lead: FK[Lead]                    # If lead
    
    started_at: DateTime
    last_activity_at: DateTime
```

### TrackingEvent

Custom event:

```python
class TrackingEvent(models.Model):
    session: FK[TrackingSession]
    
    event_type: str                   # form_submit, button_click, video_play
    event_name: str
    properties: JSONField
    
    occurred_at: DateTime
```

## Events Used For

- Lead scoring (page visits, form fills)
- Attribution (which campaign drove this lead)
- Behavior tracking (what pages interest prospects)

## Dependencies

- **Depends on**: `firm/`, `crm/`, `clients/`
- **Used by**: Lead scoring, analytics dashboards

## URLs

All routes under `/api/v1/tracking/`:

```
POST       /events/                   # Ingest events
POST       /pageviews/                # Ingest page views
POST       /identify/                 # Link visitor to contact

GET        /sessions/
GET        /sessions/{id}/events/
GET        /analytics/attribution/
```
