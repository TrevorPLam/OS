# CAL-1 Implementation: Event Type Categories

**Status:** ✅ **COMPLETED** (January 2, 2026)  
**Priority:** HIGH  
**Effort:** 8-12 hours  
**Related Feature:** Scheduling Platform - Complete Calendly Replacement

## Overview

Implemented event type categories for the AppointmentType model to support different meeting structures:
- **One-on-One**: Traditional 1:1 meetings between a host and a single invitee
- **Group Events**: One-to-many meetings where a host meets with multiple invitees
- **Collective Events**: Multiple hosts meet with invitees (requires overlapping availability)
- **Round Robin**: Meetings distributed across a pool of staff members

## Implementation

### Database Schema Changes

**Migration:** `0005_add_event_categories.py`

#### New Fields in `AppointmentType` Model

1. **event_category** (CharField)
   - Choices: one_on_one, group, collective, round_robin
   - Default: one_on_one
   - Indexed with firm for efficient querying

2. **Group Event Fields**
   - `max_attendees` (IntegerField, nullable): Maximum attendees (2-1000)
   - `enable_waitlist` (BooleanField): Enable waiting list when capacity is reached

3. **Collective Event Fields** (ManyToMany)
   - `required_hosts`: Staff members who must all be available
   - `optional_hosts`: Additional staff members who may join

4. **Round Robin Fields** (ManyToMany)
   - `round_robin_pool`: Pool of staff members for distribution

### Model Validation

Enhanced `clean()` method to enforce category-specific requirements:
- Group events must have `max_attendees` between 2-1000
- Collective events require at least one required host (validated after save)
- Round robin events require a non-empty pool (validated after save)

### API Changes

**Serializer:** `AppointmentTypeSerializer`

Added fields:
- `event_category`
- `max_attendees`
- `enable_waitlist`
- `required_hosts` / `required_hosts_display`
- `optional_hosts` / `optional_hosts_display`
- `round_robin_pool` / `round_robin_pool_display`

Display fields provide full user details (id, username, email) for ManyToMany relationships.

### Admin Interface

Updated `AppointmentTypeAdmin` with:
- Event category in list view
- Filter by event category
- Collapsible fieldsets for category-specific settings
- `filter_horizontal` for easy ManyToMany management

## Usage Examples

### Creating a Group Event

```python
from modules.calendar.models import AppointmentType
from modules.firm.models import Firm

firm = Firm.objects.first()

group_event = AppointmentType.objects.create(
    firm=firm,
    name="Open Office Hours",
    description="Weekly group Q&A session",
    event_category="group",
    max_attendees=50,
    enable_waitlist=True,
    duration_minutes=60,
    location_mode="video",
)
```

### Creating a Collective Event

```python
from django.contrib.auth import get_user_model

User = get_user_model()

collective_event = AppointmentType.objects.create(
    firm=firm,
    name="Partner Consultation",
    description="Meet with multiple partners simultaneously",
    event_category="collective",
    duration_minutes=90,
    location_mode="in_person",
)

# Add required hosts
partners = User.objects.filter(firm=firm, role="partner")[:2]
collective_event.required_hosts.set(partners)
```

### Creating a Round Robin Event

```python
round_robin_event = AppointmentType.objects.create(
    firm=firm,
    name="Initial Consultation",
    description="Distributed across available consultants",
    event_category="round_robin",
    duration_minutes=30,
    location_mode="video",
)

# Add team members to pool
consultants = User.objects.filter(firm=firm, department="consulting")
round_robin_event.round_robin_pool.set(consultants)
```

## REST API Usage

### Create Group Event

```bash
POST /api/calendar/appointment-types/
{
  "name": "Team Workshop",
  "event_category": "group",
  "max_attendees": 20,
  "enable_waitlist": true,
  "duration_minutes": 120,
  "location_mode": "video"
}
```

### Response

```json
{
  "appointment_type_id": 123,
  "name": "Team Workshop",
  "event_category": "group",
  "max_attendees": 20,
  "enable_waitlist": true,
  "required_hosts": [],
  "required_hosts_display": [],
  "optional_hosts": [],
  "optional_hosts_display": [],
  "round_robin_pool": [],
  "round_robin_pool_display": [],
  "duration_minutes": 120,
  "location_mode": "video",
  "status": "active",
  "created_at": "2026-01-02T13:00:00Z",
  "updated_at": "2026-01-02T13:00:00Z"
}
```

## Next Steps

### Related Features (Not Yet Implemented)
- **CAL-2:** Multiple duration options per event type
- **CAL-3:** Rich event descriptions with WYSIWYG editor
- **CAL-4:** Custom URL slugs and event color coding
- **CAL-5:** Scheduling constraints (daily limits, rolling availability)
- **CAL-6:** Meeting lifecycle management (rescheduled, no-show tracking)

### Booking Logic Requirements
The event categories are defined in the model, but booking logic must be implemented in:
- `AvailabilityService`: Calculate available slots differently based on event category
- `BookingService`: Handle bookings with capacity limits, host requirements
- `RoutingService`: Implement round robin distribution algorithm

## Testing

### Manual Testing
1. Create appointment types for each category via Django admin
2. Verify validation enforces category-specific requirements
3. Test serializer with API requests (create, update, list)
4. Verify ManyToMany relationships display correctly

### Future Automated Tests
- Unit tests for model validation
- Integration tests for booking flows per category
- API endpoint tests for CRUD operations
- Availability calculation tests for collective events

## Files Changed

- `src/modules/calendar/models.py`: Added event_category and related fields
- `src/modules/calendar/serializers.py`: Updated AppointmentTypeSerializer
- `src/modules/calendar/admin.py`: Enhanced admin interface
- `src/modules/calendar/migrations/0005_add_event_categories.py`: Database migration

## Migration Instructions

```bash
cd src
python manage.py migrate calendar 0005_add_event_categories
```

## Verification

Check event categories are available:
```python
from modules.calendar.models import AppointmentType
print(dict(AppointmentType.EVENT_CATEGORY_CHOICES))
```

Expected output:
```
{
  'one_on_one': 'One-on-One',
  'group': 'Group Event (one-to-many)',
  'collective': 'Collective Event (multiple hosts, overlapping availability)',
  'round_robin': 'Round Robin (distribute across team)'
}
```
