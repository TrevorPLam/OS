# Calendar Specification (CALENDAR_SPEC)

Defines internal calendar domain semantics: appointment types, availability, booking flows, shared calendars, and the boundaries between internal scheduling and external sync (CALENDAR_SYNC_SPEC.md).

Normative. If conflicts with SYSTEM_SPEC.md or DOMAIN_MODEL.md, those govern.

---

## 1) Goals
1. Provide native scheduling for staff and clients (Calendly-like).
2. Support shared firm calendars and individual staff calendars.
3. Provide deterministic availability computation with buffers and rules.
4. Keep internal appointment semantics stable; external sync is an integration layer, not the authority.

---

## 2) Core concepts

### 2.1 AppointmentType
Defines a bookable meeting type.

Fields (conceptual):
- appointment_type_id
- name
- duration_minutes
- buffer_before_minutes
- buffer_after_minutes
- location_mode (video | phone | in_person | custom)
- allowed_booking_channels (portal | staff | public_prospect)
- requires_approval (boolean)
- intake_questions (optional)
- routing_policy (see 2.4)
- status (active | inactive)

### 2.2 AvailabilityProfile
Defines availability rules for a staff user (or team pool).

Fields:
- availability_profile_id
- owner_type (staff | team)
- owner_id
- timezone
- weekly_hours (by day)
- exceptions (dates off, holidays)
- min_notice_minutes
- max_future_days
- slot_rounding_minutes
- status

### 2.3 BookingLink
A shareable booking surface that binds:
- appointment type
- availability profile (or routing pool)
- optional account/engagement context
- channel (portal-only vs public)

Fields:
- booking_link_id
- appointment_type_id
- routing_pool_id (optional)
- visibility (portal_only | staff_only | public)
- slug/token
- status

Security:
- public links must be rate limited and abuse protected.

### 2.4 Routing policies
Routing determines which staff member(s) are eligible.
Options (policy-defined; choose what to implement in V1):
- fixed_staff (preselected staff)
- round_robin_pool
- engagement_owner
- service_line_owner
- skill_tag_match (future)

Routing outputs:
- eligible staff list
- chosen staff (for booking)
- reason trace (for debugging)

---

## 3) Booking flows

### 3.1 Portal booking
1. Portal user selects appointment type.
2. System computes available slots from eligible staff availability.
3. Portal user selects slot and confirms.
4. Appointment created in `requested` or `confirmed` based on requires_approval.
5. Notify staff and (optionally) create conversation/system message.

### 3.2 Prospect booking (optional)
If enabled:
- prospect must provide contact info
- creates a pre-account “prospect record” or intake draft
- must be constrained with anti-abuse controls

### 3.3 Staff booking
Staff can book on behalf of client:
- may bypass approval
- must select account/contact context when available

---

## 4) Availability computation (normative requirements)

1. Availability MUST be computed in the profile timezone, then converted to display timezone.
2. Buffers MUST be enforced.
3. Min notice and max future booking MUST be enforced.
4. Conflicts MUST consider:
- existing appointments in native system
- (optionally) externally synced busy blocks (if you model them)
5. Slot selection MUST be protected against race conditions:
- use a reservation/hold mechanism or atomic booking transaction.

---

## 5) Shared calendars and visibility

1. Team calendar views SHOULD show:
- time blocks (busy/free)
- meeting titles/details based on permissions
2. Portal users MUST NOT see internal meeting details beyond what is explicitly shared.

---

## 6) Relationship to calendar sync

CALENDAR_SYNC_SPEC.md defines external provider sync behavior.
Rules:
1. Internal Appointment remains the source of meaning.
2. External sync updates must follow reconciliation policies; no silent semantic rewrites.
3. Sync logs and manual resync tooling are required (CALENDAR_SYNC_SPEC.md).

---

## 7) Permissions
- Staff can manage their availability; managers/admins can manage team pools.
- Booking link creation (public) should be restricted (Manager+).
- Portal can book/cancel only within granted account scope and allowed appointment types.

---

## 8) Testing requirements
- slot calculation correctness with buffers and exceptions
- DST boundary behavior
- race condition prevention (two users attempt same slot)
- portal cannot access internal calendar details
- routing policy determinism
- approval-required flow correctness

---
