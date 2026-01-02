# CAL-6 Implementation: Meeting Lifecycle Management

**Status:** ✅ **COMPLETED** (January 2, 2026)  
**Priority:** HIGH  
**Effort:** 6-8 hours  
**Related Feature:** Scheduling Platform - Complete Calendly Replacement

## Overview

Implemented comprehensive meeting lifecycle management for the Appointment model to support:
- **Meeting states**: scheduled, rescheduled, canceled, completed, no-show, awaiting confirmation
- **No-Show tracking**: Track which party didn't show up (client, staff, or both)
- **Awaiting Confirmation**: For group polls and manual approval workflows
- **Full audit trail**: AppointmentStatusHistory tracks all state transitions

## Implementation

### Database Schema Changes

**Migration:** `0010_add_meeting_lifecycle.py`

#### Updated STATUS_CHOICES

Expanded from 5 to 7 status options:
1. **requested**: Needs approval (existing)
2. **confirmed**: Appointment confirmed (existing)
3. **rescheduled**: Original appointment that was rescheduled (NEW)
4. **cancelled**: Appointment cancelled (existing)
5. **completed**: Meeting completed successfully (existing)
6. **no_show**: One or both parties didn't show up (existing)
7. **awaiting_confirmation**: Pending confirmation from invitees (NEW)

#### New Fields in `Appointment` Model

1. **rescheduled_at** (DateTimeField, optional)
   - Timestamp when appointment was rescheduled
   - Set when status changes to "rescheduled"
   - Used for tracking reschedule patterns

2. **rescheduled_from** (ForeignKey to self, optional)
   - Links new appointment to original
   - Enables rescheduling chain tracking
   - Reverse relation: `rescheduled_to`
   - Example: Original (rescheduled) → New (confirmed)

3. **cancelled_at** (DateTimeField, optional)
   - Timestamp when appointment was cancelled
   - Set when status changes to "cancelled"
   - Used for cancellation analytics

4. **completed_at** (DateTimeField, optional)
   - Timestamp when appointment was marked as completed
   - Set when status changes to "completed"
   - Used for completion rate tracking

5. **no_show_at** (DateTimeField, optional)
   - Timestamp when appointment was marked as no-show
   - Set when status changes to "no_show"
   - Used for no-show rate analytics

6. **no_show_party** (CharField, optional)
   - Tracks who didn't show up
   - Choices: "client", "staff", "both"
   - Enables party-specific no-show metrics
   - Example: Track client no-show rate vs staff no-show rate

### Existing Audit Trail

The `AppointmentStatusHistory` model (already exists) provides:
- Full audit trail of all status changes
- Tracks: from_status → to_status
- Records: reason, changed_by, changed_at
- Ordered by changed_at (most recent first)
- Indexed on (appointment, changed_at) for performance

### API Changes

**Serializer:** `AppointmentDetailSerializer`

Added fields:
- `rescheduled_at` (read-only, datetime)
- `rescheduled_from` (read-only, appointment ID)
- `cancelled_at` (read-only, datetime)
- `completed_at` (read-only, datetime)
- `no_show_at` (read-only, datetime)
- `no_show_party` (read-only, string)

These fields are included in appointment detail responses.

## Usage Examples

### Rescheduling an Appointment

```python
from modules.calendar.models import Appointment, AppointmentStatusHistory
from django.utils import timezone

# Get original appointment
original = Appointment.objects.get(appointment_id=123)

# Mark original as rescheduled
original.status = "rescheduled"
original.rescheduled_at = timezone.now()
original.save()

# Record in audit trail
AppointmentStatusHistory.objects.create(
    appointment=original,
    from_status="confirmed",
    to_status="rescheduled",
    reason="Client requested different time",
    changed_by=staff_user,
)

# Create new appointment with link to original
new_appointment = Appointment.objects.create(
    firm=original.firm,
    appointment_type=original.appointment_type,
    staff_user=original.staff_user,
    account=original.account,
    contact=original.contact,
    start_time=new_start_time,
    end_time=new_end_time,
    status="confirmed",
    rescheduled_from=original,
    booked_by=original.booked_by,
)

# Track the new appointment in audit trail
AppointmentStatusHistory.objects.create(
    appointment=new_appointment,
    from_status=None,
    to_status="confirmed",
    reason="Rescheduled from previous appointment",
    changed_by=staff_user,
)

# Access rescheduling chain
print(f"Original: {original.appointment_id}")
print(f"Rescheduled to: {list(original.rescheduled_to.all())}")
print(f"New appointment rescheduled from: {new_appointment.rescheduled_from}")
```

### Tracking No-Shows

```python
# Mark appointment as no-show
appointment = Appointment.objects.get(appointment_id=456)
appointment.status = "no_show"
appointment.no_show_at = timezone.now()
appointment.no_show_party = "client"  # or "staff" or "both"
appointment.status_reason = "Client did not join video call"
appointment.save()

# Record in audit trail
AppointmentStatusHistory.objects.create(
    appointment=appointment,
    from_status="confirmed",
    to_status="no_show",
    reason="Client did not join video call after 15 minutes",
    changed_by=staff_user,
)

# Calculate no-show rates
from django.db.models import Count, Q

client_no_shows = Appointment.objects.filter(
    firm=firm,
    no_show_party="client"
).count()

total_completed = Appointment.objects.filter(
    firm=firm,
    status__in=["completed", "no_show"]
).count()

client_no_show_rate = (client_no_shows / total_completed) * 100 if total_completed > 0 else 0
print(f"Client no-show rate: {client_no_show_rate:.1f}%")
```

### Cancelling an Appointment

```python
# Cancel appointment
appointment = Appointment.objects.get(appointment_id=789)
appointment.status = "cancelled"
appointment.cancelled_at = timezone.now()
appointment.status_reason = "Client emergency"
appointment.save()

# Record in audit trail
AppointmentStatusHistory.objects.create(
    appointment=appointment,
    from_status="confirmed",
    to_status="cancelled",
    reason="Client emergency - family issue",
    changed_by=client_user,
)
```

### Marking as Completed

```python
# Mark appointment as completed (typically done automatically after meeting time)
appointment = Appointment.objects.get(appointment_id=101)
appointment.status = "completed"
appointment.completed_at = timezone.now()
appointment.save()

# Record in audit trail
AppointmentStatusHistory.objects.create(
    appointment=appointment,
    from_status="confirmed",
    to_status="completed",
    reason="Meeting completed successfully",
    changed_by=staff_user,
)
```

### Group Poll with Awaiting Confirmation

```python
# Create appointment from poll, pending confirmation
poll_appointment = Appointment.objects.create(
    firm=firm,
    appointment_type=appointment_type,
    staff_user=staff_user,
    start_time=selected_time,
    end_time=selected_time + timedelta(minutes=60),
    status="awaiting_confirmation",
    booked_by=organizer,
)

# When all invitees confirm
poll_appointment.status = "confirmed"
poll_appointment.save()

# Record confirmation in audit trail
AppointmentStatusHistory.objects.create(
    appointment=poll_appointment,
    from_status="awaiting_confirmation",
    to_status="confirmed",
    reason="All invitees confirmed availability",
    changed_by=organizer,
)
```

### Querying Status History

```python
# Get full audit trail for an appointment
appointment = Appointment.objects.get(appointment_id=123)
history = appointment.status_history.all()

for change in history:
    print(f"{change.changed_at}: {change.from_status} → {change.to_status}")
    print(f"  Changed by: {change.changed_by.username}")
    print(f"  Reason: {change.reason}")
    print()

# Get most recent status change
latest_change = appointment.status_history.first()

# Filter by status transition
cancellations = AppointmentStatusHistory.objects.filter(
    appointment__firm=firm,
    to_status="cancelled",
    changed_at__gte=start_date
)
```

## State Transition Diagram

```
┌─────────────┐
│  requested  │──approve──→ confirmed
└─────────────┘

┌─────────────┐
│  confirmed  │──reschedule──→ rescheduled
│             │──cancel────→ cancelled
│             │──no-show───→ no_show
│             │──complete──→ completed
└─────────────┘

┌─────────────────────────┐
│  awaiting_confirmation  │──confirm──→ confirmed
│                         │──timeout──→ cancelled
└─────────────────────────┘

┌─────────────┐
│ rescheduled │ (terminal state - original appointment)
└─────────────┘

┌───────────┐
│ cancelled │ (terminal state)
└───────────┘

┌───────────┐
│ completed │ (terminal state)
└───────────┘

┌──────────┐
│ no_show  │ (terminal state)
└──────────┘
```

## Frontend Integration Notes

### Status Display

Display statuses with appropriate visual indicators:

```javascript
const statusColors = {
  requested: 'yellow',
  confirmed: 'green',
  rescheduled: 'blue',
  cancelled: 'red',
  completed: 'gray',
  no_show: 'orange',
  awaiting_confirmation: 'purple'
};

const statusIcons = {
  requested: '⏳',
  confirmed: '✓',
  rescheduled: '🔄',
  cancelled: '✕',
  completed: '✓✓',
  no_show: '⚠',
  awaiting_confirmation: '⏲'
};
```

### Rescheduling UI

When user reschedules:
1. Show original appointment details
2. Allow selecting new time
3. Create link between old and new appointments
4. Show "Rescheduled from [original date/time]" badge

### No-Show Tracking

Provide options for staff to mark no-shows:
- "Client didn't show"
- "Staff didn't show"
- "Both didn't show"

Include timestamp and optional note field.

### Status History Timeline

Display status changes as timeline:
```
✓ Completed - Jan 5, 2026 3:30 PM (by Staff)
  Reason: Meeting completed successfully

✓ Confirmed - Jan 2, 2026 10:15 AM (by Client)
  Reason: Approved booking request

⏳ Requested - Jan 2, 2026 10:00 AM (by Client)
  Reason: Initial booking
```

## Business Logic Integration

### Auto-Complete Past Appointments

```python
from django.utils import timezone
from modules.calendar.models import Appointment

def auto_complete_past_appointments():
    """Mark past appointments as completed if not already in terminal state."""
    cutoff = timezone.now() - timedelta(hours=1)  # 1 hour grace period
    
    appointments = Appointment.objects.filter(
        end_time__lt=cutoff,
        status="confirmed"
    )
    
    for appointment in appointments:
        appointment.status = "completed"
        appointment.completed_at = appointment.end_time
        appointment.save()
        
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            from_status="confirmed",
            to_status="completed",
            reason="Automatically marked as completed after meeting time",
            changed_by=None,
        )
```

### No-Show Detection

```python
def detect_no_shows():
    """Detect appointments that should be marked as no-show."""
    cutoff = timezone.now() - timedelta(minutes=30)  # 30 min after start
    
    appointments = Appointment.objects.filter(
        start_time__lt=cutoff,
        status="confirmed"
    )
    
    # Check if meeting was joined (implementation specific)
    for appointment in appointments:
        if not appointment.was_joined():  # Custom method
            appointment.status = "no_show"
            appointment.no_show_at = timezone.now()
            appointment.no_show_party = "client"  # Default
            appointment.status_reason = "Did not join meeting"
            appointment.save()
```

## Analytics & Reporting

### Common Metrics

```python
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

# Completion rate
total = Appointment.objects.filter(firm=firm, end_time__lt=timezone.now()).count()
completed = Appointment.objects.filter(firm=firm, status="completed").count()
completion_rate = (completed / total * 100) if total > 0 else 0

# No-show rate by party
no_shows = Appointment.objects.filter(firm=firm, status="no_show")
client_no_shows = no_shows.filter(no_show_party="client").count()
staff_no_shows = no_shows.filter(no_show_party="staff").count()

# Cancellation rate
cancelled = Appointment.objects.filter(firm=firm, status="cancelled").count()
cancellation_rate = (cancelled / total * 100) if total > 0 else 0

# Reschedule frequency
rescheduled = Appointment.objects.filter(firm=firm, status="rescheduled").count()
reschedule_rate = (rescheduled / total * 100) if total > 0 else 0

# Average reschedule chain length
appointments_with_reschedules = Appointment.objects.filter(
    firm=firm,
    rescheduled_to__isnull=False
)
```

## Testing Recommendations

1. **Status Tests**
   - Test all 7 status values
   - Test status transitions
   - Test terminal states

2. **Rescheduling Tests**
   - Create rescheduling chain
   - Verify forward and reverse relationships
   - Test multiple reschedules

3. **No-Show Tests**
   - Test all no_show_party values
   - Verify timestamp tracking
   - Test no-show analytics

4. **Audit Trail Tests**
   - Verify status history creation
   - Test history ordering
   - Test reason and changed_by tracking

5. **Lifecycle Tests**
   - Test complete workflow: requested → confirmed → completed
   - Test cancellation flow
   - Test awaiting_confirmation flow

## Migration Notes

- Safe to run on production
- Existing appointments unaffected
- New fields are nullable
- Status field max_length increased from 20 to 30
- No data migration needed
- No downtime required

## Related Files

- Model: `src/modules/calendar/models.py`
- Migration: `src/modules/calendar/migrations/0010_add_meeting_lifecycle.py`
- Serializer: `src/modules/calendar/serializers.py`
- Tests: `src/modules/calendar/tests.py`

## Next Steps

Consider implementing:
- **Auto-completion**: Background task to mark past appointments as completed
- **No-show detection**: Automatic detection based on meeting join status
- **Rescheduling limits**: Limit number of reschedules per appointment
- **Status webhooks**: Notify external systems of status changes
- **Analytics dashboard**: Visual representation of lifecycle metrics
