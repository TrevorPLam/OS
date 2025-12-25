# Tier 4: Time Entry Approval System

**Status**: ✅ IMPLEMENTED
**Created**: 2025-12-25

## Overview

The Time Entry Approval System ensures that time entries are NOT billable by default and require explicit approval before being included in client invoices. This prevents unauthorized billing and provides a clear approval workflow.

## Core Principle

**Default-Deny for Billing**: Time entries exist independently of invoices and must be explicitly approved before they can be billed to clients.

## Database Schema

**Model**: `TimeEntry` (src/modules/projects/models.py)

### Approval Fields

```python
# TIER 4: Approval Gate (time entries NOT billable by default)
approved = models.BooleanField(
    default=False,
    help_text="Time entry approved for billing (default: False per Tier 4)"
)

approved_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='approved_time_entries',
    help_text="Staff/Admin who approved this time entry for billing"
)

approved_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text="When time entry was approved for billing"
)
```

## Billing Invariants

### Invariant 1: Approval Required Before Invoicing

Time entries cannot be added to an invoice unless `approved=True`.

**Enforcement**: In `TimeEntry.save()` method:

```python
# TIER 4: Enforce approval gate
if self.invoiced and not self.approved:
    raise ValidationError(
        "Time entry cannot be invoiced unless approved. "
        "Approval required before billing."
    )
```

### Invariant 2: Approval is Immutable After Invoicing

Once a time entry has been invoiced, its approval cannot be revoked.

**Enforcement**: In `TimeEntry.save()` method:

```python
# TIER 4: Prevent approval revocation after invoicing
if self.pk:  # Existing record
    old_instance = TimeEntry.objects.filter(pk=self.pk).first()
    if old_instance and old_instance.invoiced and old_instance.approved and not self.approved:
        raise ValidationError(
            "Cannot revoke approval for time entry that has been invoiced. "
            "Approval is immutable after billing."
        )
```

## Approval Workflow

### Step 1: Time Entry Creation

When a team member logs time, the entry is created with:
- `approved = False` (default)
- `invoiced = False` (default)
- `approved_by = None`
- `approved_at = None`

**State**: Time entry exists but is NOT billable.

### Step 2: Staff/Admin Approval

A project manager or admin reviews time entries and approves them for billing:

```python
from django.utils import timezone
from modules.projects.models import TimeEntry

# Approve a time entry
entry = TimeEntry.objects.get(id=entry_id)
entry.approved = True
entry.approved_by = request.user  # Staff or Admin
entry.approved_at = timezone.now()
entry.save()
```

**State**: Time entry is now billable (can be added to invoice).

### Step 3: Invoice Generation

When generating an invoice, only query approved time entries:

```python
from modules.projects.models import TimeEntry

# Query only approved, unbilled time entries
billable_entries = TimeEntry.objects.filter(
    project__client=client,
    approved=True,
    invoiced=False
).order_by('date')

# Add to invoice line items
for entry in billable_entries:
    line_items.append({
        'type': 'hourly',
        'description': f'{entry.description} ({entry.hours}h @ ${entry.hourly_rate}/hr)',
        'quantity': float(entry.hours),
        'rate': float(entry.hourly_rate),
        'amount': float(entry.billed_amount),
        'time_entry_id': entry.id
    })

    # Mark as invoiced
    entry.invoiced = True
    entry.invoice = invoice
    entry.save()
```

**State**: Time entry is now invoiced (approval is immutable).

## Approval Levels

### Current Implementation (Tier 4 Phase 1)

**Level 1: Staff/Admin Approval** ✅ IMPLEMENTED
- Any staff member or admin can approve time entries
- Approval tracked with `approved_by` field
- Timestamp recorded in `approved_at`

### Future Enhancement (Tier 4 Phase 2)

**Level 2: Client Approval (Optional)** ⚠️ DOCUMENTED
- For sensitive projects, require client approval in addition to staff approval
- New fields to add:
  ```python
  client_approved = models.BooleanField(default=False)
  client_approved_by = models.ForeignKey(...)
  client_approved_at = models.DateTimeField(...)
  ```
- Validation: `invoiced` requires both `approved=True` AND `client_approved=True`

## Permission Requirements

### Who Can Approve Time Entries?

**Current Model**: No explicit permission checks in model validation.

**Recommended Implementation** (Tier 4 Phase 2):

```python
# In API view or serializer
from rest_framework.permissions import BasePermission

class CanApproveTimeEntries(BasePermission):
    """
    Permission to approve time entries for billing.

    Allowed:
    - Project managers of the project
    - Firm admins
    - Master admins

    Not allowed:
    - Portal users (clients)
    - Regular team members (can log time, can't approve)
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is project manager
        if obj.project.project_manager == request.user:
            return True

        # Check if user is firm admin
        from modules.firm.models import FirmMembership
        membership = FirmMembership.objects.filter(
            firm=request.firm,
            user=request.user,
            role__in=['admin', 'master_admin']
        ).exists()

        return membership
```

## Reporting & Analytics

### Approval Status Report

Query time entries by approval status:

```python
from modules.projects.models import TimeEntry
from django.db.models import Sum, Count

# Get approval statistics for a project
stats = {
    'total_entries': TimeEntry.objects.filter(project=project).count(),
    'approved': TimeEntry.objects.filter(project=project, approved=True).count(),
    'pending_approval': TimeEntry.objects.filter(project=project, approved=False).count(),
    'invoiced': TimeEntry.objects.filter(project=project, invoiced=True).count(),
    'billable_hours': TimeEntry.objects.filter(
        project=project,
        approved=True,
        invoiced=False
    ).aggregate(total=Sum('hours'))['total'] or 0
}
```

### Approval Lag Analysis

Identify time entries waiting for approval:

```python
from datetime import timedelta
from django.utils import timezone

# Find entries pending approval for > 7 days
threshold = timezone.now() - timedelta(days=7)

stale_entries = TimeEntry.objects.filter(
    approved=False,
    created_at__lt=threshold
).order_by('created_at')
```

## Audit Trail

All approval actions should be logged in the audit system:

```python
from modules.firm.audit import audit

# When approving a time entry
audit.log_billing_event(
    firm=entry.project.firm,
    action='time_entry_approved',
    actor=request.user,
    metadata={
        'time_entry_id': entry.id,
        'project_id': entry.project.id,
        'hours': float(entry.hours),
        'billed_amount': float(entry.billed_amount),
        'approved_by': request.user.id,
    }
)

# When attempting to invoice unapproved entry (validation failure)
audit.log_billing_event(
    firm=entry.project.firm,
    action='time_entry_invoice_blocked_unapproved',
    actor=request.user,
    metadata={
        'time_entry_id': entry.id,
        'reason': 'Approval required before billing',
    },
    severity='WARNING'
)
```

## API Endpoints (Future - Tier 4 Phase 2)

### Approve Time Entry

```
POST /api/time-entries/{id}/approve/

Request:
{
  "approval_note": "Reviewed and approved for billing"
}

Response:
{
  "id": 123,
  "approved": true,
  "approved_by": {
    "id": 5,
    "name": "Jane Smith"
  },
  "approved_at": "2025-12-25T10:30:00Z"
}
```

### Bulk Approve Time Entries

```
POST /api/time-entries/bulk-approve/

Request:
{
  "time_entry_ids": [123, 124, 125],
  "approval_note": "Week ending 2025-12-20 approved"
}

Response:
{
  "approved_count": 3,
  "failed_count": 0,
  "time_entries": [...]
}
```

### Query Billable Hours

```
GET /api/projects/{project_id}/billable-hours/

Query Params:
- approved=true (only approved entries)
- invoiced=false (only unbilled entries)
- date_from=2025-12-01
- date_to=2025-12-31

Response:
{
  "total_hours": 120.5,
  "total_amount": 18075.00,
  "entries": [...]
}
```

## Edge Cases & Error Handling

### Case 1: Approving Already-Invoiced Entry

**Current Behavior**: No validation error (entry already approved when invoiced).

**Expected**: Should be idempotent - re-approving an already-approved entry is safe.

### Case 2: Revoking Approval After Invoice Draft

**Scenario**: Entry approved, added to draft invoice (not sent), then approval revoked.

**Current Behavior**: Validation error if `invoiced=True`.

**Recommendation**: Only block revocation if invoice status is 'sent' or 'paid'.

### Case 3: Deleting Time Entry After Invoiced

**Current Behavior**: Django allows deletion (invoice FK is SET_NULL).

**Recommendation** (Tier 4 Phase 2): Block deletion of invoiced time entries:

```python
def delete(self, *args, **kwargs):
    if self.invoiced:
        raise ValidationError(
            "Cannot delete time entry that has been invoiced. "
            "Contact support if this entry was added in error."
        )
    super().delete(*args, **kwargs)
```

## Testing Checklist

- [ ] Time entry created with `approved=False` by default
- [ ] Cannot invoice time entry with `approved=False`
- [ ] Can approve time entry (sets approved=True, approved_by, approved_at)
- [ ] Cannot revoke approval after `invoiced=True`
- [ ] Invoice generation only includes approved entries
- [ ] Approval audit events are logged
- [ ] Permission checks prevent unauthorized approval

## Migration Applied

**Migration**: `projects/0002_timeentry_approved_timeentry_approved_at_and_more.py`

**Fields Added**:
- `approved` (BooleanField, default=False)
- `approved_by` (ForeignKey to User, nullable)
- `approved_at` (DateTimeField, nullable)

## Implementation Status

- ✅ Model fields added
- ✅ Validation in save() method
- ✅ Migration created and applied
- ⚠️ API endpoints pending (Tier 4 Phase 2)
- ⚠️ Permission classes pending (Tier 4 Phase 2)
- ⚠️ Audit logging pending (Tier 4 Phase 2)
- ⚠️ Client approval (optional) pending (future)

## See Also

- [BILLING_INVARIANTS_AND_ARCHITECTURE.md](./BILLING_INVARIANTS_AND_ARCHITECTURE.md) - Complete Tier 4 architecture
- [CREDIT_LEDGER_SYSTEM.md](./CREDIT_LEDGER_SYSTEM.md) - Credit tracking system
