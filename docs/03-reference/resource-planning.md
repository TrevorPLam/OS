# Resource Planning & Allocation System

## Overview

The Resource Planning & Allocation System (Task 3.2) provides capacity planning and resource allocation tracking for projects. It enables firms to manage team member assignments, track availability, and detect over-allocation conflicts.

## Models

### ResourceAllocation

Tracks allocation of team members to projects with percentage-based capacity planning.

**Key Features:**
- Percentage-based allocation (0-100%)
- Role and billing rate tracking
- Conflict detection for over-allocation
- Status lifecycle (planned → active → completed/cancelled)
- Timeline management with start/end dates

**Fields:**
- `project`: Project the resource is allocated to (required)
- `resource`: Team member allocated (required)
- `allocation_type`: Type of allocation (dedicated, part-time, as-needed, backup)
- `allocation_percentage`: Percentage of resource's time allocated (0-100, required)
- `hourly_rate`: Billing rate for this resource on this project
- `start_date`, `end_date`: Allocation timeline (required)
- `role`: Resource's role on the project (e.g., "Lead Consultant", "Analyst")
- `is_billable`: Whether the resource's time is billable
- `status`: Planned, active, completed, or cancelled
- `notes`: Notes about the allocation

**Validation:**
- Ensures `end_date` is after `start_date`
- Validates `allocation_percentage` is between 0-100
- Detects overlapping allocations that exceed 100% capacity
- Warns when a resource is over-allocated

**API Endpoints:**
- `GET /api/projects/resource-allocations/` - List allocations
- `POST /api/projects/resource-allocations/` - Create allocation
- `GET /api/projects/resource-allocations/{id}/` - Retrieve allocation
- `PUT /api/projects/resource-allocations/{id}/` - Update allocation
- `DELETE /api/projects/resource-allocations/{id}/` - Delete allocation
- `GET /api/projects/resource-allocations/conflicts/` - Find over-allocation conflicts

**Conflict Detection Endpoint:**
```
GET /api/projects/resource-allocations/conflicts/?start_date=2026-01-01&end_date=2026-03-31
```

Returns resources that are over-allocated (>100% total allocation) during the specified period, including:
- Resource details
- Total allocation percentage
- List of overlapping allocations

### ResourceCapacity

Tracks available capacity for team members, accounting for leave, holidays, and other unavailability.

**Key Features:**
- Daily capacity tracking
- Unavailability management (vacation, sick leave, holidays, etc.)
- Net available hours calculation
- Firm-scoped tenant isolation

**Fields:**
- `firm`: Firm this capacity entry belongs to (required, TIER 0)
- `resource`: Team member (required)
- `date`: Date of capacity entry (required, unique per resource)
- `available_hours`: Total hours available (default: 8.00)
- `unavailable_hours`: Hours unavailable (default: 0.00)
- `unavailability_type`: Reason for unavailability (vacation, sick leave, holiday, training, administrative, other)
- `notes`: Notes about capacity on this date

**Computed Properties:**
- `net_available_hours`: `available_hours - unavailable_hours` (read-only)

**Unavailability Types:**
- Vacation
- Sick Leave
- Public Holiday
- Training/Conference
- Administrative Time
- Other

**API Endpoints:**
- `GET /api/projects/resource-capacities/` - List capacity entries
- `POST /api/projects/resource-capacities/` - Create capacity entry
- `GET /api/projects/resource-capacities/{id}/` - Retrieve capacity entry
- `PUT /api/projects/resource-capacities/{id}/` - Update capacity entry
- `DELETE /api/projects/resource-capacities/{id}/` - Delete capacity entry
- `GET /api/projects/resource-capacities/availability/` - Get availability summary

**Availability Summary Endpoint:**
```
GET /api/projects/resource-capacities/availability/?start_date=2026-01-01&end_date=2026-03-31&resource=123
```

Returns availability summary for resources during the specified period, including:
- Total available hours
- Total unavailable hours
- Net available hours

## Usage Examples

### Creating a Resource Allocation

```python
from modules.projects.models import ResourceAllocation
from datetime import date

allocation = ResourceAllocation.objects.create(
    project=project,
    resource=team_member,
    allocation_type="part_time",
    allocation_percentage=50.00,  # 50% allocated
    hourly_rate=150.00,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 3, 31),
    role="Senior Consultant",
    is_billable=True,
    status="planned",
)
```

### Recording Unavailability

```python
from modules.projects.models import ResourceCapacity
from datetime import date
from decimal import Decimal

# Record vacation day
capacity = ResourceCapacity.objects.create(
    firm=firm,
    resource=team_member,
    date=date(2026, 1, 15),
    available_hours=Decimal("8.00"),
    unavailable_hours=Decimal("8.00"),
    unavailability_type="vacation",
    notes="Planned vacation",
)
```

### Checking for Over-Allocation

```python
from datetime import date

# Get all allocations for a resource in a date range
allocations = ResourceAllocation.objects.filter(
    resource=team_member,
    status__in=["planned", "active"],
    start_date__lte=date(2026, 3, 31),
    end_date__gte=date(2026, 1, 1),
)

# Calculate total allocation
total_allocation = sum(alloc.allocation_percentage for alloc in allocations)

if total_allocation > 100:
    print(f"Resource is over-allocated: {total_allocation}%")
```

### Getting Net Available Hours

```python
from datetime import date

# Get capacity for a specific date
capacity = ResourceCapacity.objects.get(
    resource=team_member,
    date=date(2026, 1, 15)
)

# Access net available hours
net_hours = capacity.net_available_hours  # available_hours - unavailable_hours
```

## Integration with Projects

### Project Model

The `Project` model now supports resource allocation tracking through the `resource_allocations` reverse relationship:

```python
# Get all resources allocated to a project
allocations = project.resource_allocations.filter(status="active")

# Get team members on the project
team_members = [alloc.resource for alloc in allocations]
```

### Resource Planning Workflow

1. **Planning Phase**: Create ResourceAllocations with `status="planned"`
2. **Activation**: Update status to `"active"` when work begins
3. **Monitoring**: Use conflicts endpoint to detect over-allocation
4. **Capacity Management**: Record unavailability in ResourceCapacity
5. **Completion**: Update status to `"completed"` when allocation ends

## Admin Interface

Both models have full Django admin support:

### ResourceAllocation Admin
- List view with project, resource, allocation %, role, dates, and status
- Filters by status, allocation type, billable flag, and start date
- Search by resource name, project name, and role
- Fieldsets for allocation details, timeline, financial, and audit info

### ResourceCapacity Admin
- List view with resource, date, available hours, unavailable hours, net hours, and type
- Filters by date, unavailability type, and firm
- Search by resource name
- Computed field showing net available hours

## Tenant Isolation (TIER 0)

**ResourceAllocation:**
- Inherits firm context through Project relationship
- Queries automatically scoped via `project__firm`

**ResourceCapacity:**
- Direct `firm` foreign key for efficient queries
- Uses `FirmScopedManager` for automatic scoping
- All queries filtered by `request.firm`

## Database Schema

### Indexes

**ResourceAllocation:**
- `proj_res_alloc_proj_status_idx`: (project, status)
- `proj_res_alloc_res_status_idx`: (resource, status, start_date)
- `proj_res_alloc_dates_idx`: (start_date, end_date)

**ResourceCapacity:**
- `proj_res_cap_firm_res_date_idx`: (firm, resource, date)
- `proj_res_cap_firm_date_idx`: (firm, date)

### Unique Constraints

- ResourceCapacity: (resource, date) - One capacity entry per resource per day

## Permissions

- **Staff Users**: Full access to resource planning within their firm
- **Portal Users**: Explicitly denied access (internal planning only)
- **Platform Operators**: Metadata-only access (break-glass for content)

## Performance Considerations

- Indexes on frequently queried fields (project, resource, dates, status)
- `select_related` used in ViewSets to minimize database queries
- Conflict detection optimized to query only active/planned allocations
- Availability summary aggregates data efficiently

## Future Enhancements

Potential improvements for future versions:

1. **Gantt Chart Integration**: Visual timeline view of allocations (Task 3.6)
2. **Auto-Scheduling**: Suggest optimal resource allocation based on availability
3. **Skill Matching**: Match resources to projects based on required skills
4. **Utilization Reporting**: Track actual vs. planned utilization
5. **Capacity Forecasting**: Predict future capacity needs
6. **Approval Workflows**: Require manager approval for allocations
7. **Integration with Calendar**: Sync with team member calendars
8. **Mobile Notifications**: Alert resources of new allocations

## Related Documentation

- [Projects Module](./projects-module.md) - Full projects module documentation
- [System Invariants](../../spec/SYSTEM_INVARIANTS.md) - Platform rules
- [Architecture Overview](../04-explanation/architecture-overview.md) - System design
- [API Usage Guide](./api-usage.md) - API documentation
