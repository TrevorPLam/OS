# Pipeline & Deal Management

**Status:** DEAL-1 and DEAL-2 Complete  
**Date:** January 2, 2026  
**Implementation:** CRM Module Enhancement

## Overview

The Pipeline & Deal Management feature provides a comprehensive sales pipeline system for tracking opportunities from initial contact through close. This system replaces and extends the simpler Prospect-based workflow with a more flexible, configurable pipeline approach.

## Architecture

### Models

#### Pipeline
- **Purpose:** Represents a customizable sales workflow
- **Key Features:**
  - Configurable stages with ordering
  - Default pipeline support per firm
  - Active/inactive status tracking
  - Multi-tenant isolation via firm relationship

#### PipelineStage
- **Purpose:** Represents steps within a pipeline
- **Key Features:**
  - Ordered stages with display_order
  - Configurable probability per stage
  - Closed won/lost stage designation
  - Auto-task configuration (future automation)

#### Deal
- **Purpose:** Sales opportunity tracking
- **Key Features:**
  - Financial tracking (value, probability, weighted_value)
  - Stage progression with history
  - Account and contact associations
  - Team member assignment
  - Deal splitting for multiple owners
  - Stale deal detection
  - Project conversion workflow
  - Activity tracking

#### DealTask
- **Purpose:** Action items related to deals
- **Key Features:**
  - Priority levels (low, medium, high, urgent)
  - Status tracking (pending, in_progress, completed, cancelled)
  - Assignment to team members
  - Due date tracking

## Database Schema

### Key Relationships

```
Firm
  ├── Pipeline (1:N)
  │   ├── PipelineStage (1:N)
  │   └── Deal (1:N)
  │       └── DealTask (1:N)
  ├── Account (1:N)
  │   └── Deal (1:N)
  └── Campaign (1:N)
      └── Deal (1:N)
```

### Indexes

For optimal query performance, the following indexes are created:

**Pipeline:**
- `(firm, is_active)` - Filter active pipelines by firm
- `(firm, is_default)` - Find default pipeline

**PipelineStage:**
- `(pipeline, display_order)` - Ordered stage listing
- `(pipeline, is_active)` - Filter active stages

**Deal:**
- `(firm, pipeline, stage)` - Pipeline board views
- `(firm, owner)` - Owner's deals
- `(firm, is_active)` - Active deals
- `(firm, expected_close_date)` - Forecast queries
- `(firm, is_stale)` - Stale deal reports
- `(account)` - Account deals
- `(contact)` - Contact deals

**DealTask:**
- `(deal, status)` - Deal tasks by status
- `(assigned_to, status)` - User's tasks
- `(due_date)` - Due date sorting

## API Endpoints

### Pipelines

```
GET    /api/crm/pipelines/              # List all pipelines
POST   /api/crm/pipelines/              # Create pipeline
GET    /api/crm/pipelines/{id}/         # Get pipeline details
PATCH  /api/crm/pipelines/{id}/         # Update pipeline
DELETE /api/crm/pipelines/{id}/         # Delete pipeline
POST   /api/crm/pipelines/{id}/set_default/  # Set as default
GET    /api/crm/pipelines/{id}/analytics/    # Pipeline analytics
```

### Pipeline Stages

```
GET    /api/crm/pipeline-stages/        # List all stages
POST   /api/crm/pipeline-stages/        # Create stage
GET    /api/crm/pipeline-stages/{id}/   # Get stage details
PATCH  /api/crm/pipeline-stages/{id}/   # Update stage
DELETE /api/crm/pipeline-stages/{id}/   # Delete stage
POST   /api/crm/pipeline-stages/{id}/reorder/  # Reorder stage
```

### Deals

```
GET    /api/crm/deals/                  # List all deals
POST   /api/crm/deals/                  # Create deal
GET    /api/crm/deals/{id}/             # Get deal details
PATCH  /api/crm/deals/{id}/             # Update deal
DELETE /api/crm/deals/{id}/             # Delete deal
POST   /api/crm/deals/{id}/move_stage/  # Move to different stage
POST   /api/crm/deals/{id}/mark_won/    # Mark deal as won
POST   /api/crm/deals/{id}/mark_lost/   # Mark deal as lost
POST   /api/crm/deals/{id}/convert_to_project/  # Convert to project
GET    /api/crm/deals/stale/            # List stale deals
GET    /api/crm/deals/forecast/         # Pipeline forecast
```

### Deal Tasks

```
GET    /api/crm/deal-tasks/             # List all tasks
POST   /api/crm/deal-tasks/             # Create task
GET    /api/crm/deal-tasks/{id}/        # Get task details
PATCH  /api/crm/deal-tasks/{id}/        # Update task
DELETE /api/crm/deal-tasks/{id}/        # Delete task
POST   /api/crm/deal-tasks/{id}/complete/  # Mark as completed
```

## Usage Examples

### Creating a Pipeline

```python
POST /api/crm/pipelines/
{
    "name": "Sales Pipeline",
    "description": "Standard sales process",
    "is_default": true,
    "display_order": 1
}
```

### Creating Pipeline Stages

```python
POST /api/crm/pipeline-stages/
{
    "pipeline": 1,
    "name": "Discovery",
    "probability": 10,
    "display_order": 1
}

POST /api/crm/pipeline-stages/
{
    "pipeline": 1,
    "name": "Proposal",
    "probability": 50,
    "display_order": 2
}

POST /api/crm/pipeline-stages/
{
    "pipeline": 1,
    "name": "Closed Won",
    "probability": 100,
    "is_closed_won": true,
    "display_order": 3
}
```

### Creating a Deal

```python
POST /api/crm/deals/
{
    "pipeline": 1,
    "stage": 1,
    "name": "Acme Corp - Consulting Services",
    "account": 5,
    "contact": 12,
    "value": "50000.00",
    "probability": 10,
    "expected_close_date": "2026-03-31",
    "owner": 3,
    "source": "Website"
}
```

### Moving Deal Through Stages

```python
POST /api/crm/deals/123/move_stage/
{
    "stage_id": 2,
    "notes": "Proposal sent and under review"
}
```

### Marking Deal as Won

```python
POST /api/crm/deals/123/mark_won/
```

### Converting Deal to Project

```python
POST /api/crm/deals/123/convert_to_project/
{
    "start_date": "2026-04-01",
    "end_date": "2026-12-31",
    "description": "Custom project description"
}
```

### Getting Pipeline Forecast

```python
GET /api/crm/deals/forecast/
Response:
{
    "total_pipeline_value": "1500000.00",
    "total_weighted_value": "750000.00",
    "monthly_forecast": [
        {
            "month": "2026-02-01",
            "deal_count": 5,
            "total_value": "250000.00",
            "weighted_value": "125000.00"
        },
        {
            "month": "2026-03-01",
            "deal_count": 8,
            "total_value": "500000.00",
            "weighted_value": "300000.00"
        }
    ]
}
```

### Getting Pipeline Analytics

```python
GET /api/crm/pipelines/1/analytics/
Response:
{
    "total_deals": 15,
    "total_value": "1500000.00",
    "total_weighted_value": "750000.00",
    "average_deal_value": "100000.00",
    "average_probability": 50,
    "stage_breakdown": [
        {
            "stage_id": 1,
            "stage_name": "Discovery",
            "deal_count": 5,
            "total_value": "300000.00",
            "weighted_value": "30000.00"
        },
        {
            "stage_id": 2,
            "stage_name": "Proposal",
            "deal_count": 7,
            "total_value": "800000.00",
            "weighted_value": "400000.00"
        }
    ]
}
```

## Features Implemented

### ✅ DEAL-1: Design Pipeline and Deal Models
- Pipeline model with configurable stages
- PipelineStage model with ordering and probability
- Deal model with financial tracking and associations
- DealTask model for action items
- Deal-to-Project conversion workflow
- Stale deal detection
- Deal splitting support

### ✅ DEAL-2: Implement Deal CRUD Operations and API
- Complete REST API with ViewSets
- Deal stage transition logic
- Deal associations (contacts, accounts, tasks)
- Validation rules and constraints
- Mark won/lost actions
- Convert to project endpoint
- Stale deals endpoint
- Forecast endpoint
- Pipeline analytics endpoint
- Django Admin interface with custom actions

## Remaining Tasks (TODO.md)

### DEAL-3: Build Pipeline Visualization UI (8-12 hours)
- Kanban board view of deals by stage
- Drag-and-drop stage transitions
- Pipeline filtering and search
- Deal card UI with key metrics

### DEAL-4: Add Forecasting and Analytics (8-12 hours)
- ✅ Weighted pipeline forecasting (implemented in API)
- Win/loss tracking
- Pipeline performance reports
- Revenue projection calculations

### DEAL-5: Implement Assignment Automation (6-8 hours)
- Round-robin deal assignment
- Territory-based routing
- Deal stage automation triggers

### DEAL-6: Add Deal Splitting and Rotting Alerts (6-8 hours)
- ✅ Deal splitting for multiple owners (implemented in model)
- ✅ Stale deal detection (implemented in model)
- Automated reminder system

## Security & Multi-Tenancy

All pipeline and deal operations enforce firm-level isolation:

1. **FirmScopedMixin:** Automatically filters queries by `request.user.firm`
2. **Portal Access Denial:** Portal users explicitly denied access to deal management
3. **Validation:** Stage-pipeline consistency enforced at API level
4. **Audit Trail:** Created_by and timestamp tracking on all models

## Performance Considerations

1. **Indexes:** Comprehensive indexing for common query patterns
2. **Query Optimization:** QueryTimeoutMixin prevents long-running queries
3. **Weighted Values:** Pre-calculated and stored for fast forecasting
4. **Bounded Search:** BoundedSearchFilter limits search result sets

## Testing Recommendations

1. **Model Tests:**
   - Pipeline default logic (only one default per firm)
   - Deal weighted value calculation
   - Stale deal detection logic
   - Deal-to-project conversion
   
2. **API Tests:**
   - CRUD operations for all endpoints
   - Stage transition validation
   - Firm scoping (users can't see other firms' deals)
   - Win/loss marking
   - Forecast calculations

3. **Integration Tests:**
   - Complete deal lifecycle (create → move stages → close)
   - Project conversion workflow
   - Task completion and deal activity updates

## Migration

The migration file `0007_add_pipeline_and_deal_models.py` creates:
- Pipeline table with indexes
- PipelineStage table with indexes
- Deal table with indexes
- DealTask table with indexes

Run migration:
```bash
python manage.py migrate crm
```

## Admin Interface

The Django admin provides:
- Pipeline management with default setting action
- Stage management with reordering capability
- Deal management with won/lost actions and stale deal checking
- Task management with completion action
- Inline task editing within deal admin

## Future Enhancements

1. **Automation:** Auto-task creation when deals enter stages
2. **Round-robin Assignment:** Automatic deal distribution
3. **Territory Routing:** Geographic-based assignment
4. **Reminder System:** Automated notifications for stale deals
5. **UI Components:** Kanban board, drag-and-drop, visual pipeline
6. **Advanced Analytics:** Win/loss analysis, conversion rates, velocity metrics
