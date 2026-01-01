# Profitability Reporting with Margin Analysis

**Feature:** 3.3 - Complex Task  
**Module:** Finance  
**Status:** ✅ Completed  
**Created:** January 1, 2026

---

## Overview

The Profitability Reporting system provides real-time financial insights into project and service line performance. It tracks revenue, costs, and margins to help firms understand which projects and service lines are most profitable.

This feature supports data-driven decision making by:
- Identifying profitable vs. unprofitable projects
- Analyzing margin trends across service lines
- Forecasting project completion costs
- Tracking billable utilization rates

---

## Architecture

### Models

#### ProjectProfitability

Tracks profitability for individual projects in real-time.

**Key Fields:**
- **Revenue Tracking:**
  - `total_revenue`: Total revenue from invoices and payments
  - `recognized_revenue`: Revenue recognized based on completion percentage
  
- **Cost Tracking:**
  - `labor_cost`: Total cost of labor (time entries × rates)
  - `expense_cost`: Total project expenses (travel, materials, etc.)
  - `overhead_cost`: Allocated overhead costs (facility, admin, etc.)
  
- **Margin Analysis:**
  - `gross_margin`: Revenue minus direct costs (labor + expenses)
  - `gross_margin_percentage`: Gross margin as percentage of revenue
  - `net_margin`: Gross margin minus overhead costs
  - `net_margin_percentage`: Net margin as percentage of revenue
  
- **Metrics:**
  - `hours_logged`: Total hours logged on project
  - `billable_utilization`: Percentage of billable hours vs total hours
  - `estimated_completion_cost`: Estimated total cost to complete
  - `estimated_final_margin`: Projected final margin at completion

**Relationships:**
- One-to-one relationship with `Project`
- Belongs to `Firm` for tenant isolation

**Calculation Method:**
```python
# Revenue
total_revenue = sum(invoice.paid_amount for paid invoices)
recognized_revenue = total_revenue * completion_percentage

# Costs
labor_cost = sum(time_entry.hours * hourly_rate)
expense_cost = sum(approved_expenses.amount)
overhead_cost = labor_cost * 0.20  # 20% allocation

# Margins
gross_margin = recognized_revenue - (labor_cost + expense_cost)
gross_margin_percentage = (gross_margin / recognized_revenue) * 100
net_margin = gross_margin - overhead_cost
net_margin_percentage = (net_margin / recognized_revenue) * 100

# Utilization
billable_utilization = (billable_hours / total_hours) * 100
```

#### ServiceLineProfitability

Aggregates profitability across multiple projects within a service line over a specified period.

**Key Fields:**
- `name`: Service line name (e.g., "Management Consulting", "IT Advisory")
- `description`: Description of this service line
- `period_start`: Start of reporting period
- `period_end`: End of reporting period
- `total_revenue`: Total revenue across all projects
- `total_cost`: Total costs (labor + expenses + overhead)
- `gross_margin`: Total revenue minus total costs
- `margin_percentage`: Margin as percentage of revenue
- `project_count`: Number of projects in service line
- `active_project_count`: Number of active projects

**Unique Constraint:**
- `(firm, name, period_start, period_end)` - One record per service line per period

---

## API Endpoints

### Project Profitability

**Base URL:** `/api/finance/project-profitability/`

#### List Project Profitability
```http
GET /api/finance/project-profitability/
```

**Query Parameters:**
- `project`: Filter by project ID
- `search`: Search by project name or client name
- `ordering`: Sort by `gross_margin_percentage`, `net_margin_percentage`, `total_revenue`, `last_calculated_at`

**Response:**
```json
{
  "count": 50,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "firm": 1,
      "project": 42,
      "project_name": "Digital Transformation Project",
      "client_name": "Acme Corp",
      "total_revenue": "125000.00",
      "recognized_revenue": "100000.00",
      "labor_cost": "60000.00",
      "expense_cost": "10000.00",
      "overhead_cost": "12000.00",
      "gross_margin": "30000.00",
      "gross_margin_percentage": "30.00",
      "net_margin": "18000.00",
      "net_margin_percentage": "18.00",
      "hours_logged": "800.00",
      "billable_utilization": "85.00",
      "last_calculated_at": "2026-01-01T12:00:00Z",
      "created_at": "2025-12-01T10:00:00Z"
    }
  ]
}
```

#### Recalculate Single Project
```http
POST /api/finance/project-profitability/{id}/recalculate/
```

**Response:**
```json
{
  "id": 1,
  "project_name": "Digital Transformation Project",
  "gross_margin_percentage": "30.00",
  ...
}
```

#### Recalculate All Projects
```http
POST /api/finance/project-profitability/recalculate_all/
```

**Response:**
```json
{
  "message": "Recalculated profitability for 50 project(s)."
}
```

### Service Line Profitability

**Base URL:** `/api/finance/service-line-profitability/`

#### List Service Line Profitability
```http
GET /api/finance/service-line-profitability/
```

**Query Parameters:**
- `name`: Filter by service line name
- `period_start`: Filter by period start date
- `period_end`: Filter by period end date
- `ordering`: Sort by `margin_percentage`, `total_revenue`, `period_start`

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "firm": 1,
      "name": "Management Consulting",
      "description": "General management consulting services",
      "period_start": "2025-Q4",
      "period_end": "2025-12-31",
      "total_revenue": "1500000.00",
      "total_cost": "900000.00",
      "gross_margin": "600000.00",
      "margin_percentage": "40.00",
      "project_count": 25,
      "active_project_count": 18,
      "last_calculated_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

## Admin Interface

### Project Profitability Admin

**Features:**
- View profitability metrics for all projects
- Filter by firm and calculation date
- Search by project or client name
- Bulk recalculate action
- Read-only calculated fields

**Actions:**
- `recalculate_profitability`: Recalculate profitability for selected records

**Fieldsets:**
1. Project: Firm and project selection
2. Revenue: Total and recognized revenue
3. Costs: Labor, expense, and overhead costs
4. Margins: Gross and net margin calculations
5. Metrics: Hours and utilization tracking
6. Forecasting: Completion estimates
7. Timestamps: Audit trail

### Service Line Profitability Admin

**Features:**
- View aggregated metrics by service line
- Filter by firm and period
- Search by service line name
- Read-only calculated fields

**Fieldsets:**
1. Service Line: Name and description
2. Period: Start and end dates
3. Metrics: Revenue, costs, and margins
4. Projects: Project count tracking
5. Timestamps: Audit trail

---

## Usage Examples

### Create Project Profitability Record

```python
from modules.finance.models import ProjectProfitability
from modules.projects.models import Project

# Get the project
project = Project.objects.get(id=42)

# Create profitability record
profitability = ProjectProfitability.objects.create(
    firm=project.firm,
    project=project
)

# Calculate metrics
profitability.calculate_profitability()
```

### Query Top Performing Projects

```python
# Get projects with highest gross margin percentage
top_projects = ProjectProfitability.objects.filter(
    firm=request.firm
).order_by('-gross_margin_percentage')[:10]

for prof in top_projects:
    print(f"{prof.project.name}: {prof.gross_margin_percentage}%")
```

### Create Service Line Report

```python
from modules.finance.models import ServiceLineProfitability
from datetime import date

# Create quarterly report
service_line = ServiceLineProfitability.objects.create(
    firm=firm,
    name="Management Consulting",
    period_start=date(2025, 10, 1),
    period_end=date(2025, 12, 31)
)

# Manually calculate or use periodic task
# service_line.calculate_metrics()
```

---

## Security & Permissions

### Tenant Isolation
- All models use `FirmScopedManager` for automatic tenant isolation
- Records belong to exactly one Firm (TIER 0 requirement)
- API endpoints use `FirmScopedMixin` to enforce tenant boundaries

### Access Control
- **Staff Users:** Full CRUD access to profitability records
- **Portal Users:** Explicitly denied access via `DenyPortalAccess` permission
- **Read-Only Fields:** All calculated fields are read-only to prevent manual tampering

### Audit Trail
- `created_at`: Record creation timestamp
- `last_calculated_at`: Last calculation timestamp (auto-updated)

---

## Performance Considerations

### Indexes
- `(firm, last_calculated_at)`: Fast filtering by firm and recency
- `(firm, gross_margin_percentage)`: Fast sorting by margin
- `(firm, period_start, period_end)`: Fast service line period queries

### Optimization Tips
1. **Batch Calculations:** Use `recalculate_all` endpoint during off-peak hours
2. **Periodic Updates:** Schedule nightly calculations via Celery task
3. **Selective Queries:** Use `select_related` for project/client relationships
4. **Caching:** Consider caching frequently accessed profitability records

### Query Timeouts
- All ViewSets inherit `QueryTimeoutMixin` to prevent long-running queries
- Default timeout: 30 seconds (configurable)

---

## Integration Points

### Related Models
- **Project:** One-to-one relationship for project-level analysis
- **Invoice:** Source of revenue data
- **TimeEntry:** Source of labor cost data
- **Expense:** Source of expense cost data
- **Firm:** Tenant isolation

### Data Flow
1. TimeEntry logged → labor_cost updated
2. Expense approved → expense_cost updated
3. Invoice paid → total_revenue updated
4. Calculation triggered → margins computed
5. Dashboard displays results

---

## Future Enhancements

### Planned Features
1. **Automated Recalculation:** Celery task to recalculate nightly
2. **Trend Analysis:** Historical margin tracking and visualization
3. **Anomaly Detection:** Alert on projects with declining margins
4. **Budget vs. Actual:** Compare projected vs. actual profitability
5. **Client Profitability:** Aggregate profitability across all client projects
6. **Customizable Overhead:** Per-project overhead allocation rates
7. **What-If Analysis:** Model profitability changes with rate adjustments

### API Enhancements
1. Bulk create/update endpoints
2. Export to Excel/CSV
3. Graphical trend data endpoints
4. Comparative analysis endpoints

---

## Testing

### Unit Tests
```python
def test_profitability_calculation():
    """Test profitability calculation logic."""
    project = create_test_project()
    profitability = ProjectProfitability.objects.create(
        firm=project.firm,
        project=project
    )
    profitability.calculate_profitability()
    
    assert profitability.total_revenue > 0
    assert profitability.gross_margin_percentage >= 0
```

### Integration Tests
- Test API endpoint access control
- Test calculation with real project data
- Test service line aggregation logic

---

## Migration

**File:** `0010_profitability_reporting.py`

**Changes:**
- Created `ProjectProfitability` model
- Created `ServiceLineProfitability` model
- Added indexes for performance
- Added unique constraint on service line periods

**No Data Migration Required:** Tables start empty and are populated on-demand.

---

## References

- **Related Tasks:** 
  - Task 3.1: Account & Contact relationship graph
  - Task 3.2: Resource planning & allocation system
- **Related Models:**
  - `projects.Project`
  - `finance.Invoice`
  - `projects.TimeEntry`
  - `projects.Expense`
- **API Documentation:** `/api/docs/` (Swagger UI)

---

## Support

For questions or issues:
1. Review this documentation
2. Check API documentation at `/api/docs/`
3. Review admin interface at `/admin/finance/projectprofitability/`
4. Contact development team
