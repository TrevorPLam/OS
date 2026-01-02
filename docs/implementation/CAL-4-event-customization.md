# CAL-4 Implementation: Event Customization Features

**Status:** ✅ **COMPLETED** (January 2, 2026)  
**Priority:** HIGH  
**Effort:** 8-12 hours  
**Related Feature:** Scheduling Platform - Complete Calendly Replacement

## Overview

Implemented event customization features for the AppointmentType model to support:
- **Custom URL slugs per event**: SEO-friendly URLs for each event type
- **Event color coding**: Visual identification with hex color codes
- **Event-specific availability overrides**: Per-event customization of availability rules
- **Event status management**: Added "archived" status for historical events

## Implementation

### Database Schema Changes

**Migration:** `0008_add_event_customization.py`

#### New Fields in `AppointmentType` Model

1. **url_slug** (SlugField, optional)
   - Max length: 100 characters
   - Auto-generated from event name if not provided
   - Must be unique within a firm
   - Format: lowercase letters, numbers, and hyphens only
   - Example: "strategy-session", "tax-consultation"

2. **color_code** (CharField, optional)
   - Max length: 7 characters
   - Hex color format: #RRGGBB
   - Validated via clean() method
   - Used for visual identification in calendars and UI
   - Example: "#3B82F6" (blue), "#10B981" (green)

3. **availability_overrides** (JSONField, optional)
   - Event-specific availability overrides
   - Can override weekly_hours, min_notice_minutes, max_future_days, etc.
   - Falls back to default AvailabilityProfile if not set
   - Format: `{"weekly_hours": {...}, "min_notice_minutes": 120, ...}`

4. **status** field updated
   - Added "archived" option to existing choices
   - Choices: active, inactive, archived
   - Archived events are hidden from booking but preserved for history

#### Database Constraints

- **Unique Constraint**: `calendar_apt_firm_slug_uniq`
  - Ensures url_slug is unique within a firm (when url_slug is not empty)
  - Allows multiple empty slugs per firm (for auto-generation)

- **Index**: `calendar_apt_fir_slug_idx`
  - Indexed on (firm, url_slug) for fast lookups

### Model Changes

#### Auto-Generated Slugs

Override `save()` method to auto-generate slug from name if not provided:

```python
def save(self, *args, **kwargs):
    """Override save to auto-generate slug if not provided (CAL-4)."""
    if not self.url_slug:
        from django.utils.text import slugify
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        
        # Ensure uniqueness within firm
        while AppointmentType.objects.filter(
            firm=self.firm, url_slug=slug
        ).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        self.url_slug = slug
    
    super().save(*args, **kwargs)
```

#### Validation

Enhanced `clean()` method with CAL-4 validation:

```python
# Validate hex color format
if self.color_code:
    if not re.match(r'^#[0-9A-Fa-f]{6}$', self.color_code):
        errors['color_code'] = 'Color code must be in hex format: #RRGGBB'

# Validate slug format
if self.url_slug:
    if not re.match(r'^[a-z0-9-]+$', self.url_slug):
        errors['url_slug'] = 'URL slug must contain only lowercase letters, numbers, and hyphens'
```

### API Changes

**Serializer:** `AppointmentTypeSerializer`

Added fields:
- `url_slug` (read-write, auto-generated if not provided)
- `color_code` (read-write, validated for hex format)
- `availability_overrides` (read-write, JSON object)
- `status` (updated to include "archived")

### Admin Interface

Updated `AppointmentTypeAdmin` with:
- New collapsible fieldset "Event Customization (CAL-4)"
- Contains: url_slug, color_code, availability_overrides
- Collapsed by default to keep interface clean

## Usage Examples

### Creating an Event with Custom Slug and Color

```python
from modules.calendar.models import AppointmentType
from modules.firm.models import Firm

firm = Firm.objects.first()

event = AppointmentType.objects.create(
    firm=firm,
    name="Strategy Session",
    url_slug="premium-strategy",  # Custom slug
    color_code="#3B82F6",  # Blue color
    description="Premium strategy consultation",
    duration_minutes=60,
    location_mode="video",
)

# Access via URL: /book/premium-strategy
```

### Auto-Generated Slug

```python
# If url_slug is not provided, it's auto-generated
event = AppointmentType.objects.create(
    firm=firm,
    name="Tax Consultation",
    description="Annual tax review",
    duration_minutes=45,
    location_mode="video",
)

print(event.url_slug)  # "tax-consultation"

# Creating another event with same name auto-increments
event2 = AppointmentType.objects.create(
    firm=firm,
    name="Tax Consultation",
    description="Quarterly tax review",
    duration_minutes=30,
    location_mode="phone",
)

print(event2.url_slug)  # "tax-consultation-1"
```

### Event-Specific Availability Overrides

```python
# Create event with custom availability (different from default profile)
event = AppointmentType.objects.create(
    firm=firm,
    name="Weekend Workshop",
    url_slug="weekend-workshop",
    color_code="#8B5CF6",  # Purple
    duration_minutes=120,
    availability_overrides={
        "weekly_hours": {
            "saturday": [{"start": "09:00", "end": "13:00"}],
            "sunday": [{"start": "09:00", "end": "13:00"}],
        },
        "min_notice_minutes": 2880,  # 2 days notice
        "max_future_days": 90,
    },
    location_mode="in_person",
)
```

### Archiving Events

```python
# Archive an old event type (preserves historical data)
event = AppointmentType.objects.get(url_slug="old-service")
event.status = "archived"
event.save()

# Query only active events
active_events = AppointmentType.objects.filter(firm=firm, status="active")

# Include archived in reports
all_events = AppointmentType.objects.filter(firm=firm)
```

### API Usage

```bash
# Create with custom slug and color
curl -X POST https://api.example.com/api/calendar/appointment-types/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Consultation",
    "url_slug": "premium-consult",
    "color_code": "#10B981",
    "description": "Premium consultation service",
    "duration_minutes": 90,
    "location_mode": "video",
    "availability_overrides": {
      "min_notice_minutes": 180
    }
  }'

# Update event color
curl -X PATCH https://api.example.com/api/calendar/appointment-types/123/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"color_code": "#EF4444"}'

# Archive an event
curl -X PATCH https://api.example.com/api/calendar/appointment-types/123/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "archived"}'
```

## Frontend Integration Notes

### URL Routing

Frontend should use `url_slug` for booking URLs:
- `/book/{firm_slug}/{event_slug}` (e.g., `/book/acme-corp/strategy-session`)
- Fall back to appointment_type_id if slug is empty (for backward compatibility)

### Color Coding

Display events with their color codes in:
- Calendar views (event blocks)
- Event lists (color-coded badges or borders)
- Admin interfaces (visual identification)

Example CSS:
```css
.event-badge {
  border-left: 4px solid var(--event-color);
}
```

### Availability Overrides

When booking an event:
1. Check if `availability_overrides` is set and non-empty
2. Merge overrides with base AvailabilityProfile
3. Use merged configuration for slot calculation

Priority: Event overrides > Profile defaults

### Status Filtering

- **Active**: Show in public booking pages
- **Inactive**: Hide from public, show in admin with indicator
- **Archived**: Hide from booking, show in admin with "Archived" badge

## Validation Rules

### URL Slug
- Optional (auto-generated if empty)
- Lowercase letters, numbers, and hyphens only
- Unique within firm
- Max 100 characters

### Color Code
- Optional (no color if empty)
- Must match pattern: `^#[0-9A-Fa-f]{6}$`
- Examples: `#3B82F6`, `#10B981`, `#EF4444`

### Availability Overrides
- Optional (use profile defaults if empty)
- Must be valid JSON object
- Supported keys: weekly_hours, min_notice_minutes, max_future_days, exceptions, etc.
- Partial overrides allowed (only override specific fields)

## Testing Recommendations

1. **Slug Tests**
   - Auto-generation from name
   - Custom slug preservation
   - Uniqueness within firm
   - Multiple events with same name

2. **Color Code Tests**
   - Valid hex colors accepted
   - Invalid formats rejected
   - Empty color allowed

3. **Availability Override Tests**
   - Override specific fields
   - Merge with profile defaults
   - Empty overrides use profile

4. **Status Tests**
   - Active/inactive/archived transitions
   - Filtering by status
   - Archived events excluded from booking

## Migration Notes

- Safe to run on production (all fields are optional)
- Existing events will have:
  - Empty url_slug (will be auto-generated on first save)
  - Empty color_code
  - Empty availability_overrides (falls back to profile)
  - Existing status values preserved
- No data migration needed
- No downtime required

## Related Files

- Model: `src/modules/calendar/models.py`
- Migration: `src/modules/calendar/migrations/0008_add_event_customization.py`
- Serializer: `src/modules/calendar/serializers.py`
- Admin: `src/modules/calendar/admin.py`
- Tests: `src/modules/calendar/tests.py`

## Next Steps

Consider implementing:
- **CAL-5**: Scheduling constraints (daily limits, rolling availability, notice periods)
- **CAL-6**: Meeting lifecycle management (states, no-show tracking, audit trail)
- **Frontend Components**: Event color picker, slug editor, availability override UI
- **Analytics**: Most booked events by color, popular URL slugs
