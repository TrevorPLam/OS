# AGENTS.md — Calendar Module (Scheduling & Booking)

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/calendar/`

## Purpose

Calendar management, appointment scheduling, and booking links (Calendly-style functionality).

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | AppointmentType, AvailabilityProfile, Appointment, BookingLink (~1775 LOC) |
| `views.py` | Calendar CRUD, booking management |
| `serializers.py` | Calendar serializers |
| `availability_service.py` | Availability computation and conflict checks |
| `booking_service.py` | Booking flows with race condition protection |
| `routing_service.py` | Routing policies for staff assignment |
| `round_robin_service.py` | Round robin strategy selection |
| `group_event_service.py` | Group event registration and waitlist management |
| `meeting_poll_service.py` | Poll-based scheduling workflows |
| `invitation_service.py` | ICS invitation generation |
| `services.py` | Service aggregator (re-exports core service classes) |
| `google_service.py` | Google Calendar OAuth + sync |
| `microsoft_service.py` | Microsoft/Outlook OAuth + sync |
| `sync_service.py` | Calendar synchronization logic |
| `sync_services.py` | Additional sync utilities |
| `booking_validation_service.py` | Booking slot validation |
| `holiday_service.py` | Holiday detection |
| `ical_service.py` | iCal export/import |
| `timezone_service.py` | Timezone handling |
| `workflow_services.py` | Post-booking workflow triggers |
| `admin_views.py` | Admin calendar management |
| `oauth_models.py` | OAuth token storage |
| `oauth_serializers.py` | OAuth flow serializers |
| `oauth_views.py` | OAuth callback handlers |

## Domain Model

```
AppointmentType (booking template)
    └── AvailabilityProfile (when bookable)
    └── BookingLink (public URL)

Appointment (scheduled event)
    └── Attendee (participants)

CalendarConnection (OAuth to Google/Microsoft)
    └── CalendarSync (bi-directional sync)
```

## Key Models

### AppointmentType

Defines a bookable meeting type:

```python
class AppointmentType(models.Model):
    firm: FK[Firm]
    name: str                         # "30-min Discovery Call"
    description: str
    
    # Timing
    duration_minutes: int
    buffer_before: int                # Minutes before
    buffer_after: int                 # Minutes after
    
    # Category
    event_category: str               # one_on_one, group, collective, round_robin
    
    # Location
    location_mode: str                # video, phone, in_person, custom
    video_link: str                   # Zoom/Meet URL
    
    # Limits
    max_bookings_per_day: int
    min_notice_hours: int             # Minimum advance booking
    max_future_days: int              # How far ahead bookable
    
    status: str                       # active, inactive, archived
```

### AvailabilityProfile

When someone is bookable:

```python
class AvailabilityProfile(models.Model):
    firm: FK[Firm]
    user: FK[User]                    # Whose availability
    
    name: str
    timezone: str
    
    # Weekly schedule (JSON)
    weekly_hours: JSONField           # { "monday": [{"start": "09:00", "end": "17:00"}], ... }
    
    # Exceptions
    date_overrides: JSONField         # Specific date overrides
```

### Appointment

A scheduled meeting:

```python
class Appointment(models.Model):
    firm: FK[Firm]
    appointment_type: FK[AppointmentType]
    
    title: str
    start_time: DateTime
    end_time: DateTime
    timezone: str
    
    status: str                       # scheduled, confirmed, cancelled, completed
    
    # Attendees
    host: FK[User]
    booker_name: str
    booker_email: str
    
    # Integration
    external_calendar_id: str         # Google/Microsoft event ID
    video_meeting_url: str
```

### BookingLink

Public booking page:

```python
class BookingLink(models.Model):
    firm: FK[Firm]
    appointment_type: FK[AppointmentType]
    
    slug: str                         # URL slug
    is_active: bool
    
    # Customization
    custom_questions: JSONField       # Pre-booking questions
    confirmation_message: str
    redirect_url: str
```

## Calendar Sync

### Google Calendar

```python
from modules.calendar.google_service import GoogleCalendarService

service = GoogleCalendarService(user)

# Sync events
events = service.fetch_events(start_date, end_date)
service.create_event(appointment)
service.update_event(appointment)
service.delete_event(external_id)
```

### Microsoft Calendar

```python
from modules.calendar.microsoft_service import MicrosoftCalendarService

service = MicrosoftCalendarService(user)
# Same interface as Google
```

## Booking Flow

```
1. Client visits /book/{slug}
2. System checks availability (AvailabilityProfile + existing appointments)
3. Client selects slot
4. booking_validation_service validates:
   - Slot still available
   - Min notice met
   - Max bookings not exceeded
   - No conflicts with synced calendars
5. Appointment created
6. workflow_services triggers:
   - Confirmation email
   - Calendar invite
   - Automation workflows
```

## Event Categories

| Category | Description |
|----------|-------------|
| `one_on_one` | Single host, single attendee |
| `group` | Single host, multiple attendees |
| `collective` | Multiple hosts (overlapping availability) |
| `round_robin` | Distribute across team members |

## Dependencies

- **Depends on**: `firm/`, `auth/`, `core/`
- **Used by**: CRM (meeting scheduling), Client portal
- **External**: Google Calendar API, Microsoft Graph API

## URLs

Staff endpoints (`/api/v1/calendar/`):
```
GET/POST   /appointment-types/
GET/PUT    /appointment-types/{id}/

GET/POST   /availability-profiles/
GET/PUT    /availability-profiles/{id}/

GET/POST   /appointments/
GET/PUT    /appointments/{id}/
POST       /appointments/{id}/cancel/

GET/POST   /booking-links/
GET/PUT    /booking-links/{id}/

# OAuth
GET        /oauth/google/
GET        /oauth/google/callback/
GET        /oauth/microsoft/
GET        /oauth/microsoft/callback/

# Admin
GET        /admin/calendar-connections/
POST       /admin/sync-now/
```

Public booking (`/book/`):
```
GET        /{slug}/                       # Booking page
GET        /{slug}/slots/                 # Available slots
POST       /{slug}/book/                  # Create appointment
```
