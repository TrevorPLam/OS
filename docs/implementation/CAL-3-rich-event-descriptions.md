# CAL-3 Implementation: Rich Event Descriptions

**Status:** ✅ **COMPLETED** (January 2, 2026)  
**Priority:** HIGH  
**Effort:** 6-8 hours  
**Related Feature:** Scheduling Platform - Complete Calendly Replacement

## Overview

Implemented rich event descriptions for the AppointmentType model to support:
- **WYSIWYG editor with formatting**: Rich HTML description field for formatted content
- **Link embedding**: Supported via HTML in rich_description field
- **Image upload and display**: Dedicated image field for event descriptions
- **Internal name vs public display name**: Separate internal_name field for staff use

## Implementation

### Database Schema Changes

**Migration:** `0007_add_rich_event_descriptions.py`

#### New Fields in `AppointmentType` Model

1. **internal_name** (CharField, optional)
   - Max length: 255 characters
   - For internal staff use when different from public display name
   - Searchable in admin interface
   - Blank allowed (defaults to using public name)

2. **rich_description** (TextField, optional)
   - Stores rich HTML content with formatting
   - Supports links, bold, italic, lists, etc.
   - Replaces plain text description for rich display
   - Falls back to plain `description` field if not set

3. **description_image** (ImageField, optional)
   - Upload path: `calendar/event_images/`
   - Optional image to display in event description
   - Supports common image formats (JPEG, PNG, GIF, etc.)
   - Nullable and blank for backward compatibility

### API Changes

**Serializer:** `AppointmentTypeSerializer`

Added fields:
- `internal_name` (read-write)
- `rich_description` (read-write)
- `description_image` (read-write, returns URL when image is uploaded)

These fields are included in the standard AppointmentType API responses.

### Admin Interface

Updated `AppointmentTypeAdmin` with:
- New collapsible fieldset "Rich Event Description (CAL-3)"
- Contains: internal_name, rich_description, description_image
- Added `internal_name` to search_fields for easy discovery
- Collapsed by default to keep interface clean

### Backward Compatibility

All new fields are optional (blank=True, null=True for ImageField):
- Existing appointment types continue to work without modification
- Plain `description` field remains for simple text descriptions
- Frontend can check for rich_description presence and fall back to description

## Usage Examples

### Creating an Event with Rich Description

```python
from modules.calendar.models import AppointmentType
from modules.firm.models import Firm

firm = Firm.objects.first()

event = AppointmentType.objects.create(
    firm=firm,
    name="Strategy Session",
    internal_name="STRAT-01 - Strategy Session (Premium)",
    description="Quick strategy consultation",
    rich_description='''
        <h2>What to Expect</h2>
        <p>In this <strong>60-minute session</strong>, we'll:</p>
        <ul>
            <li>Review your current business challenges</li>
            <li>Identify growth opportunities</li>
            <li>Create an actionable roadmap</li>
        </ul>
        <p>Learn more at <a href="https://example.com/strategy">our strategy page</a></p>
    ''',
    duration_minutes=60,
    location_mode="video",
)

# Add an image
from django.core.files import File
with open('event_banner.jpg', 'rb') as f:
    event.description_image.save('strategy_banner.jpg', File(f))
    event.save()
```

### Updating an Existing Event

```python
event = AppointmentType.objects.get(name="Consultation")
event.internal_name = "CONSULT-STANDARD"
event.rich_description = '''
    <p>Our standard consultation includes:</p>
    <ol>
        <li>Initial assessment</li>
        <li>Recommendations</li>
        <li>Follow-up plan</li>
    </ol>
'''
event.save()
```

### API Usage

```bash
# Create with rich description
curl -X POST https://api.example.com/api/calendar/appointment-types/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Consultation",
    "internal_name": "PREMIUM-CONSULT",
    "description": "Premium consultation service",
    "rich_description": "<h2>Premium Service</h2><p>Includes <strong>priority support</strong></p>",
    "duration_minutes": 90,
    "location_mode": "video"
  }'

# Upload image separately
curl -X PATCH https://api.example.com/api/calendar/appointment-types/123/ \
  -H "Authorization: Bearer TOKEN" \
  -F "description_image=@event_image.jpg"
```

## Frontend Integration Notes

### Displaying Rich Content

The frontend should:
1. Check if `rich_description` is present and non-empty
2. If yes, render it as HTML (with sanitization)
3. If no, fall back to plain `description` field
4. Display `description_image` if present

### WYSIWYG Editor

Recommended editors for rich_description:
- **TinyMCE**: Full-featured, easy to integrate
- **Quill**: Lightweight, modern
- **Draft.js**: React-specific, very customizable

### Security Considerations

- Always sanitize HTML before rendering to prevent XSS attacks
- Use a library like DOMPurify (JavaScript) or bleach (Python)
- Allow only safe tags: p, h1-h6, strong, em, ul, ol, li, a (with href), br
- Strip script tags, event handlers, and other dangerous content

## Testing Recommendations

1. **Model Tests**
   - Create appointment type with all rich fields
   - Verify fields are optional
   - Test image upload and retrieval

2. **API Tests**
   - Create/update via API with rich fields
   - Verify image upload endpoint
   - Test HTML content storage and retrieval

3. **Admin Tests**
   - Verify new fieldset displays correctly
   - Test search by internal_name
   - Verify image upload in admin

4. **Frontend Tests**
   - Test HTML rendering with sanitization
   - Verify fallback to plain description
   - Test image display

## Migration Notes

- Safe to run on production (all fields are optional)
- No data migration needed
- No downtime required
- Backward compatible with existing code

## Related Files

- Model: `src/modules/calendar/models.py`
- Migration: `src/modules/calendar/migrations/0007_add_rich_event_descriptions.py`
- Serializer: `src/modules/calendar/serializers.py`
- Admin: `src/modules/calendar/admin.py`

## Next Steps

Consider implementing:
- **CAL-4**: Event customization features (URL slugs, color coding, status management)
- **CAL-5**: Scheduling constraints (daily limits, rolling availability, notice periods)
- **CAL-6**: Meeting lifecycle management (states, no-show tracking, audit trail)
