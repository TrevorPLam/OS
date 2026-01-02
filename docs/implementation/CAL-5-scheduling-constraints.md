# CAL-5 Implementation: Scheduling Constraints

**Status:** ✅ **COMPLETED** (January 2, 2026)  
**Priority:** HIGH  
**Effort:** 8-12 hours  
**Related Feature:** Scheduling Platform - Complete Calendly Replacement

## Overview

Implemented comprehensive scheduling constraints for the AppointmentType model to support:
- **Daily meeting limit per event type**: Cap how many appointments of this type can be booked per day
- **Rolling availability window**: Dynamic booking window (e.g., "next 30 days")
- **Min/Max notice periods**: Event-specific notice requirements (1 hour - 30 days)
- **Event-specific buffer time configuration**: Already exists via buffer_before/after_minutes

## Implementation

### Database Schema Changes

**Migration:** `0009_add_scheduling_constraints.py`

#### New Fields in `AppointmentType` Model

1. **daily_meeting_limit** (IntegerField, optional)
   - Maximum number of this event type that can be booked per day
   - Null = unlimited
   - Range: 1-100
   - Example: Limit "Free Consultation" to 3 per day

2. **min_notice_hours** (IntegerField, optional)
   - Minimum advance notice required for booking (in hours)
   - Range: 1-720 hours (1 hour to 30 days)
   - Overrides AvailabilityProfile default if set
   - Example: 48 hours = require 2 days notice

3. **max_notice_days** (IntegerField, optional)
   - Maximum days in advance for booking
   - Range: 1-365 days
   - Overrides AvailabilityProfile default if set
   - Example: 90 days = can only book up to 3 months ahead

4. **rolling_window_days** (IntegerField, optional)
   - Rolling availability window in days
   - If set, overrides max_notice_days with a dynamic window
   - Range: 1-365 days
   - Example: 30 days = always show next 30 days from today

### Existing Buffer Time Configuration

AppointmentType already has buffer time fields (CAL-5 requirement):
- `buffer_before_minutes`: Time blocked before meeting
- `buffer_after_minutes`: Time blocked after meeting

These provide event-specific buffer time configuration.

### Model Validation

Enhanced `clean()` method with CAL-5 validation:

```python
# Daily meeting limit
if self.daily_meeting_limit is not None:
    if self.daily_meeting_limit < 1:
        errors['daily_meeting_limit'] = 'Daily meeting limit must be at least 1'
    elif self.daily_meeting_limit > 100:
        errors['daily_meeting_limit'] = 'Daily meeting limit cannot exceed 100'

# Min notice hours
if self.min_notice_hours is not None:
    if self.min_notice_hours < 1:
        errors['min_notice_hours'] = 'Minimum notice must be at least 1 hour'
    elif self.min_notice_hours > 720:  # 30 days
        errors['min_notice_hours'] = 'Minimum notice cannot exceed 720 hours (30 days)'

# Max notice days
if self.max_notice_days is not None:
    if self.max_notice_days < 1:
        errors['max_notice_days'] = 'Maximum notice must be at least 1 day'
    elif self.max_notice_days > 365:
        errors['max_notice_days'] = 'Maximum notice cannot exceed 365 days'

# Rolling window
if self.rolling_window_days is not None:
    if self.rolling_window_days < 1:
        errors['rolling_window_days'] = 'Rolling window must be at least 1 day'
    elif self.rolling_window_days > 365:
        errors['rolling_window_days'] = 'Rolling window cannot exceed 365 days'

# Validate min < max
if self.min_notice_hours and self.max_notice_days:
    min_hours = self.min_notice_hours
    max_hours = self.max_notice_days * 24
    if min_hours >= max_hours:
        errors['min_notice_hours'] = 'Minimum notice must be less than maximum notice'
```

### API Changes

**Serializer:** `AppointmentTypeSerializer`

Added fields:
- `daily_meeting_limit` (read-write, integer or null)
- `min_notice_hours` (read-write, integer or null)
- `max_notice_days` (read-write, integer or null)
- `rolling_window_days` (read-write, integer or null)

### Admin Interface

Updated `AppointmentTypeAdmin` with:
- New collapsible fieldset "Scheduling Constraints (CAL-5)"
- Contains: daily_meeting_limit, min_notice_hours, max_notice_days, rolling_window_days
- Collapsed by default to keep interface clean

## Usage Examples

### Daily Meeting Limit

```python
from modules.calendar.models import AppointmentType
from modules.firm.models import Firm

firm = Firm.objects.first()

# Limit "Free Consultation" to 5 per day
event = AppointmentType.objects.create(
    firm=firm,
    name="Free Consultation",
    daily_meeting_limit=5,
    duration_minutes=15,
    location_mode="phone",
)

# When booking: Check count for that day before allowing
from datetime import date
today = date.today()
count = Appointment.objects.filter(
    appointment_type=event,
    start_time__date=today,
    status__in=['confirmed', 'requested']
).count()

if count >= event.daily_meeting_limit:
    raise ValidationError("Daily limit reached for this event type")
```

### Minimum Notice Period

```python
# Require 48 hours advance notice
event = AppointmentType.objects.create(
    firm=firm,
    name="Strategy Session",
    min_notice_hours=48,  # 2 days
    duration_minutes=90,
    location_mode="video",
)

# When booking: Validate notice period
from datetime import datetime, timedelta
from django.utils import timezone

now = timezone.now()
requested_time = datetime(2026, 1, 5, 14, 0, 0)  # User wants Jan 5 at 2pm

min_booking_time = now + timedelta(hours=event.min_notice_hours)
if requested_time < min_booking_time:
    raise ValidationError(f"Minimum {event.min_notice_hours} hours notice required")
```

### Maximum Booking Window

```python
# Can only book up to 90 days in advance
event = AppointmentType.objects.create(
    firm=firm,
    name="Quarterly Review",
    max_notice_days=90,
    duration_minutes=60,
    location_mode="video",
)

# When booking: Validate not too far in future
max_booking_time = now + timedelta(days=event.max_notice_days)
if requested_time > max_booking_time:
    raise ValidationError(f"Cannot book more than {event.max_notice_days} days in advance")
```

### Rolling Window

```python
# Always show next 30 days (dynamic window)
event = AppointmentType.objects.create(
    firm=firm,
    name="Drop-In Session",
    rolling_window_days=30,
    duration_minutes=30,
    location_mode="video",
)

# When showing available slots:
from datetime import date, timedelta

start_date = date.today()
end_date = start_date + timedelta(days=event.rolling_window_days)

# Show slots only from today to end_date
# As days pass, window automatically shifts forward
```

### Combined Constraints

```python
# VIP event with multiple constraints
event = AppointmentType.objects.create(
    firm=firm,
    name="VIP Executive Session",
    daily_meeting_limit=2,  # Max 2 per day
    min_notice_hours=72,  # Require 3 days notice
    max_notice_days=120,  # Can book up to 4 months ahead
    rolling_window_days=90,  # But use 90-day rolling window
    buffer_before_minutes=30,  # 30 min prep time
    buffer_after_minutes=15,  # 15 min wrap-up
    duration_minutes=120,
    location_mode="in_person",
)
```

### API Usage

```bash
# Create event with constraints
curl -X POST https://api.example.com/api/calendar/appointment-types/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Limited Consultation",
    "daily_meeting_limit": 5,
    "min_notice_hours": 24,
    "max_notice_days": 60,
    "duration_minutes": 30,
    "location_mode": "video"
  }'

# Update constraints
curl -X PATCH https://api.example.com/api/calendar/appointment-types/123/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "daily_meeting_limit": 3,
    "min_notice_hours": 48
  }'

# Remove daily limit (set to null)
curl -X PATCH https://api.example.com/api/calendar/appointment-types/123/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"daily_meeting_limit": null}'
```

## Frontend Integration Notes

### Slot Availability Calculation

When computing available slots:

1. **Apply min_notice_hours**:
   ```javascript
   const minBookingTime = new Date();
   minBookingTime.setHours(minBookingTime.getHours() + event.min_notice_hours);
   // Filter slots before minBookingTime
   ```

2. **Apply max_notice_days or rolling_window_days**:
   ```javascript
   const maxBookingTime = new Date();
   if (event.rolling_window_days) {
     maxBookingTime.setDate(maxBookingTime.getDate() + event.rolling_window_days);
   } else if (event.max_notice_days) {
     maxBookingTime.setDate(maxBookingTime.getDate() + event.max_notice_days);
   }
   // Filter slots after maxBookingTime
   ```

3. **Check daily_meeting_limit**:
   ```javascript
   // For each day with slots
   const bookingsOnDay = await getBookingsCount(event.id, day);
   if (bookingsOnDay >= event.daily_meeting_limit) {
     // Mark all slots on this day as unavailable
   }
   ```

### User Feedback

Show constraints to users:
- "Requires {min_notice_hours} hours advance notice"
- "Limited to {daily_meeting_limit} bookings per day"
- "Can book up to {max_notice_days} days in advance"
- "Available for the next {rolling_window_days} days"

### Constraint Hierarchy

1. Event-specific constraints (min_notice_hours, max_notice_days) override profile defaults
2. rolling_window_days overrides max_notice_days if both are set
3. daily_meeting_limit is checked after time-based constraints

## Business Logic Integration

### Booking Service

The booking service should enforce these constraints:

```python
class BookingService:
    def validate_booking_time(self, appointment_type, requested_time):
        """Validate booking time against constraints."""
        now = timezone.now()
        
        # Check minimum notice
        if appointment_type.min_notice_hours:
            min_time = now + timedelta(hours=appointment_type.min_notice_hours)
            if requested_time < min_time:
                raise ValidationError(
                    f"Minimum {appointment_type.min_notice_hours} hours notice required"
                )
        
        # Check maximum notice / rolling window
        if appointment_type.rolling_window_days:
            max_time = now + timedelta(days=appointment_type.rolling_window_days)
        elif appointment_type.max_notice_days:
            max_time = now + timedelta(days=appointment_type.max_notice_days)
        else:
            max_time = None
        
        if max_time and requested_time > max_time:
            raise ValidationError("Requested time is outside booking window")
        
        # Check daily limit
        if appointment_type.daily_meeting_limit:
            day = requested_time.date()
            count = Appointment.objects.filter(
                appointment_type=appointment_type,
                start_time__date=day,
                status__in=['confirmed', 'requested']
            ).count()
            
            if count >= appointment_type.daily_meeting_limit:
                raise ValidationError(
                    f"Daily limit of {appointment_type.daily_meeting_limit} reached"
                )
```

## Testing Recommendations

1. **Daily Limit Tests**
   - Create multiple appointments on same day
   - Verify limit is enforced
   - Test limit with different statuses (confirmed vs canceled)

2. **Notice Period Tests**
   - Test min_notice_hours boundary
   - Test max_notice_days boundary
   - Test validation of min < max

3. **Rolling Window Tests**
   - Verify window shifts daily
   - Test rolling_window_days overrides max_notice_days

4. **Validation Tests**
   - Test range validation (1-720 hours, 1-365 days)
   - Test min < max validation
   - Test null values (unlimited)

## Migration Notes

- Safe to run on production (all fields are nullable)
- Existing events will have null for all constraint fields
- Null values mean no constraint (unlimited/unrestricted)
- No data migration needed
- No downtime required

## Related Files

- Model: `src/modules/calendar/models.py`
- Migration: `src/modules/calendar/migrations/0009_add_scheduling_constraints.py`
- Serializer: `src/modules/calendar/serializers.py`
- Admin: `src/modules/calendar/admin.py`
- Tests: `src/modules/calendar/tests.py`

## Next Steps

Consider implementing:
- **CAL-6**: Meeting lifecycle management (states, no-show tracking, audit trail)
- **Booking Service**: Enforce constraints in booking logic
- **Analytics**: Most constrained events, popular booking windows
- **Admin Reports**: Daily limit utilization, booking patterns
