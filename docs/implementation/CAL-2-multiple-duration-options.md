# CAL-2 Implementation: Multiple Duration Options

**Status:** ✅ **COMPLETED** (January 2, 2026)  
**Priority:** HIGH  
**Effort:** 4-6 hours  
**Related Feature:** Scheduling Platform - Complete Calendly Replacement

## Overview

Implemented multiple duration options for AppointmentType, allowing bookers to select from different meeting lengths with optional duration-based pricing. This enables flexible scheduling where a single event type can offer multiple time slots (e.g., 15min, 30min, 60min consultations).

## Implementation

### Database Schema Changes

**Migration:** `0006_add_multiple_durations.py`

#### New Fields in `AppointmentType` Model

1. **enable_multiple_durations** (BooleanField)
   - Default: False
   - When enabled, bookers can select from duration options

2. **duration_options** (JSONField)
   - Array of duration choices
   - Supports two formats:
     - Simple: `[15, 30, 60]` (just minutes)
     - Extended: `[{"minutes": 30, "price": 50.00, "label": "30 min session"}, ...]`
   - Optional pricing per duration

#### New Fields in `Appointment` Model

1. **selected_duration_minutes** (IntegerField, nullable)
   - Stores the duration selected by the booker
   - Used when multiple duration options are available

2. **selected_duration_price** (DecimalField, nullable)
   - Stores the price for the selected duration
   - Used for duration-based pricing

### Model Methods

**`AppointmentType.get_available_durations()`**
Returns normalized list of duration options:
```python
[
  {"minutes": 30, "label": "30 minutes", "price": None},
  {"minutes": 60, "label": "1 hour", "price": 75.00}
]
```

### Validation

Enhanced `clean()` method validates:
- Multiple durations require at least one option
- Each option must be a positive integer or valid dict
- Extended format requires 'minutes' field
- Price values must be numeric

### API Changes

**AppointmentTypeSerializer**

Added fields:
- `enable_multiple_durations`
- `duration_options`
- `available_durations` (read-only, computed)

**AppointmentDetailSerializer**

Added fields:
- `selected_duration_minutes`
- `selected_duration_price`

### Admin Interface

Added collapsible "Multiple Durations (CAL-2)" fieldset with:
- `enable_multiple_durations` toggle
- `duration_options` JSON field

## Usage Examples

### Simple Duration Options

```python
from modules.calendar.models import AppointmentType

appointment_type = AppointmentType.objects.create(
    firm=firm,
    name="Consultation",
    duration_minutes=30,  # Default duration
    enable_multiple_durations=True,
    duration_options=[15, 30, 60],  # Three choices: 15, 30, or 60 minutes
)

# Get available durations
durations = appointment_type.get_available_durations()
# Returns:
# [
#   {"minutes": 15, "label": "15 minutes", "price": None},
#   {"minutes": 30, "label": "30 minutes", "price": None},
#   {"minutes": 60, "label": "60 minutes", "price": None}
# ]
```

### Duration-Based Pricing

```python
appointment_type = AppointmentType.objects.create(
    firm=firm,
    name="Paid Consultation",
    duration_minutes=30,
    enable_multiple_durations=True,
    duration_options=[
        {"minutes": 30, "price": 50.00, "label": "30 min - Quick consultation"},
        {"minutes": 60, "price": 90.00, "label": "1 hour - Standard consultation"},
        {"minutes": 90, "price": 120.00, "label": "1.5 hours - Extended consultation"},
    ],
)

durations = appointment_type.get_available_durations()
# Returns:
# [
#   {"minutes": 30, "label": "30 min - Quick consultation", "price": 50.00},
#   {"minutes": 60, "label": "1 hour - Standard consultation", "price": 90.00},
#   {"minutes": 90, "label": "1.5 hours - Extended consultation", "price": 120.00}
# ]
```

### Booking with Selected Duration

```python
from modules.calendar.models import Appointment

appointment = Appointment.objects.create(
    firm=firm,
    appointment_type=appointment_type,
    staff_user=staff,
    start_time=start,
    end_time=start + timedelta(minutes=60),  # Selected 60-minute option
    selected_duration_minutes=60,
    selected_duration_price=90.00,
)
```

## REST API Usage

### Create Appointment Type with Multiple Durations

```bash
POST /api/calendar/appointment-types/
{
  "name": "Coaching Session",
  "duration_minutes": 60,
  "enable_multiple_durations": true,
  "duration_options": [
    {"minutes": 30, "price": 75.00, "label": "30-minute session"},
    {"minutes": 60, "price": 130.00, "label": "1-hour session"},
    {"minutes": 90, "price": 180.00, "label": "90-minute deep dive"}
  ],
  "location_mode": "video"
}
```

### Response with Available Durations

```json
{
  "appointment_type_id": 123,
  "name": "Coaching Session",
  "duration_minutes": 60,
  "enable_multiple_durations": true,
  "duration_options": [
    {"minutes": 30, "price": 75.00, "label": "30-minute session"},
    {"minutes": 60, "price": 130.00, "label": "1-hour session"},
    {"minutes": 90, "price": 180.00, "label": "90-minute deep dive"}
  ],
  "available_durations": [
    {"minutes": 30, "label": "30-minute session", "price": 75.00},
    {"minutes": 60, "label": "1-hour session", "price": 130.00},
    {"minutes": 90, "label": "90-minute deep dive", "price": 180.00}
  ],
  "status": "active"
}
```

## Frontend Integration

Booking UI should:
1. Check if `enable_multiple_durations` is true
2. Display duration selector using `available_durations`
3. Show pricing next to each option if present
4. Submit selected `duration_minutes` and `price` when booking

Example UI flow:
```
Select a duration:
○ 30-minute session - $75
● 1-hour session - $130
○ 90-minute deep dive - $180
```

## Benefits

- **Flexibility**: One event type serves multiple use cases
- **Revenue optimization**: Different prices for different durations
- **Better UX**: Bookers choose what fits their needs
- **Simpler management**: Fewer event types to maintain

## Next Steps

### Related Features (Not Yet Implemented)
- **CAL-3:** Rich event descriptions with WYSIWYG editor
- **CAL-4:** Custom URL slugs and event color coding
- **CAL-5:** Scheduling constraints (daily limits, rolling availability)
- **CAL-6:** Meeting lifecycle management

### Frontend Requirements
- Duration selector component in booking UI
- Display pricing clearly for each option
- Calculate end time based on selected duration
- Handle payment flow if duration-based pricing used

## Files Changed

- `src/modules/calendar/models.py`: Added duration fields and validation
- `src/modules/calendar/serializers.py`: Enhanced serializers
- `src/modules/calendar/admin.py`: Added admin fieldset
- `src/modules/calendar/migrations/0006_add_multiple_durations.py`: Database migration

## Migration Instructions

```bash
cd src
python manage.py migrate calendar 0006_add_multiple_durations
```

## Testing

### Manual Testing
1. Create appointment type with simple duration options via admin
2. Create appointment type with pricing via API
3. Verify `get_available_durations()` returns correct format
4. Test booking flow with selected duration

### Validation Tests
```python
# Test validation
apt = AppointmentType(
    firm=firm,
    name="Test",
    duration_minutes=30,
    enable_multiple_durations=True,
    duration_options=[]  # Empty - should fail
)
try:
    apt.clean()
except ValidationError as e:
    print(e)  # "At least one duration option must be provided"

# Test with invalid format
apt.duration_options = [{"invalid": "data"}]  # Missing 'minutes'
try:
    apt.clean()
except ValidationError as e:
    print(e)  # "Option 0: 'minutes' field is required"
```

## Backwards Compatibility

- `enable_multiple_durations` defaults to False
- Existing appointment types continue using `duration_minutes`
- No changes required for existing bookings
- Migration is non-breaking
