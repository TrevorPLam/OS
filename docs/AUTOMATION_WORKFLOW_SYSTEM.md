# Automation Workflow System Documentation

## Overview

The Automation Workflow System provides visual workflow automation capabilities with triggers, actions, and comprehensive analytics. It extends the orchestration engine with marketing automation features for complex, multi-step workflows.

## Architecture

### Components

1. **Workflow Model** - Visual automation workflows with drag-and-drop canvas
2. **Triggers (AUTO-2)** - Event-based workflow initiation
3. **Actions (AUTO-3)** - Executable actions within workflows
4. **Execution Engine (AUTO-5)** - Workflow execution scheduler with retry logic
5. **Visual Builder (AUTO-4)** - Drag-and-drop workflow canvas UI
6. **Analytics (AUTO-6)** - Flow visualization and performance metrics

### Technology Stack

- **Backend**: Django REST Framework
- **Frontend**: React + TypeScript
- **State Management**: TanStack Query (React Query)
- **Database**: PostgreSQL 15+
- **Job Queue**: Custom job queue system with DLQ

## Models

### Workflow

Main workflow container with nodes, edges, and triggers.

**Fields:**
- `name` - Human-readable workflow name
- `description` - Workflow description
- `status` - draft, active, paused, archived
- `version` - Workflow version number
- `canvas_data` - Visual canvas state

**Key Methods:**
- `activate(user)` - Activate workflow
- `pause(user)` - Pause workflow
- `validate_workflow()` - Validate before activation

### WorkflowTrigger (AUTO-2)

Event-based triggers that start workflows.

**Trigger Types:**

**Form Triggers:**
- `form_submitted` - Form submission

**Email Triggers:**
- `email_opened` - Email opened
- `email_clicked` - Link clicked
- `email_replied` - Email replied
- `email_bounced` - Email bounced
- `email_unsubscribed` - Unsubscribed

**Site Tracking:**
- `page_visited` - Page visited
- `site_activity` - Site activity detected

**CRM Triggers:**
- `contact_created` - Contact created
- `contact_updated` - Contact updated
- `contact_tag_added` - Tag added
- `contact_tag_removed` - Tag removed
- `contact_list_added` - Added to list
- `contact_list_removed` - Removed from list

**Deal Triggers:**
- `deal_created` - Deal created
- `deal_stage_changed` - Stage changed
- `deal_value_changed` - Value changed
- `deal_won` - Deal won
- `deal_lost` - Deal lost

**Score Triggers:**
- `score_threshold_reached` - Score threshold reached
- `score_threshold_dropped` - Score dropped

**Date/Time Triggers:**
- `date_reached` - Specific date
- `date_field_reached` - Date field reached
- `time_delay` - Time delay
- `anniversary` - Anniversary

**Manual Triggers:**
- `manual` - Manual trigger
- `api` - API trigger

### WorkflowNode (AUTO-3, AUTO-4)

Individual nodes in workflow canvas.

**Action Nodes:**
- `send_email` - Send email to contact
- `send_sms` - Send SMS message
- `create_task` - Create task
- `create_deal` - Create deal
- `update_deal` - Update deal
- `update_contact` - Update contact field
- `add_tag` - Add tag
- `remove_tag` - Remove tag
- `add_to_list` - Add to list
- `remove_from_list` - Remove from list
- `webhook` - Send webhook
- `internal_notification` - Send notification

**Control Flow Nodes:**
- `condition` - If/else branching
- `wait_time` - Wait for time
- `wait_until` - Wait until date
- `wait_condition` - Wait for condition
- `split` - A/B split test

**Goal Nodes:**
- `goal` - Goal reached

### WorkflowEdge

Connection between nodes defining workflow flow.

**Fields:**
- `source_node` - Starting node
- `target_node` - Ending node
- `condition_type` - Condition (yes/no for if/else)
- `condition_config` - Condition configuration
- `label` - Edge label

### WorkflowExecution (AUTO-5)

Execution instance for a specific contact.

**Fields:**
- `contact` - Contact being processed
- `status` - running, waiting, completed, goal_reached, failed, canceled
- `current_node` - Current node
- `execution_path` - Ordered list of executed nodes
- `context_data` - Execution context
- `trigger_type` - What triggered execution
- `goal_reached` - Whether goal was reached
- `idempotency_key` - Execution idempotency key

**Key Methods:**
- `compute_idempotency_key()` - Generate idempotency key

### ContactFlowState (AUTO-5)

Per-contact node visit tracking for analytics.

**Fields:**
- `execution` - Parent execution
- `node` - Node visited
- `entered_at` - Entry timestamp
- `exited_at` - Exit timestamp
- `action_status` - Action result status
- `action_result` - Action result data
- `variant` - A/B test variant

### WorkflowGoal (AUTO-6)

Conversion goal tracking.

**Fields:**
- `name` - Goal name
- `goal_node` - Goal node
- `goal_value` - Revenue value
- `total_conversions` - Total conversions
- `conversion_rate` - Conversion rate %
- `total_value` - Total revenue

**Key Methods:**
- `update_analytics()` - Recalculate analytics

### WorkflowAnalytics (AUTO-6)

Aggregated workflow performance metrics.

**Fields:**
- `period_start` - Analytics period start
- `period_end` - Analytics period end
- `total_executions` - Total executions
- `completed_executions` - Completed count
- `failed_executions` - Failed count
- `goal_reached_executions` - Goal reached count
- `avg_completion_time_seconds` - Average time
- `median_completion_time_seconds` - Median time
- `drop_off_points` - Drop-off analysis
- `node_performance` - Per-node metrics
- `goal_conversion_rate` - Conversion rate

## API Endpoints

### Workflows

```
GET    /api/v1/automation/workflows/              List workflows
POST   /api/v1/automation/workflows/              Create workflow
GET    /api/v1/automation/workflows/{id}/         Get workflow
PATCH  /api/v1/automation/workflows/{id}/         Update workflow
DELETE /api/v1/automation/workflows/{id}/         Delete workflow
POST   /api/v1/automation/workflows/{id}/activate/     Activate workflow
POST   /api/v1/automation/workflows/{id}/pause/        Pause workflow
POST   /api/v1/automation/workflows/{id}/duplicate/    Duplicate workflow
GET    /api/v1/automation/workflows/{id}/analytics/    Get analytics
GET    /api/v1/automation/workflows/{id}/executions/   Get executions
```

### Triggers

```
GET    /api/v1/automation/triggers/               List triggers
POST   /api/v1/automation/triggers/               Create trigger
PATCH  /api/v1/automation/triggers/{id}/          Update trigger
DELETE /api/v1/automation/triggers/{id}/          Delete trigger
```

### Nodes

```
GET    /api/v1/automation/nodes/                  List nodes
POST   /api/v1/automation/nodes/                  Create node
PATCH  /api/v1/automation/nodes/{id}/             Update node
DELETE /api/v1/automation/nodes/{id}/             Delete node
```

### Edges

```
GET    /api/v1/automation/edges/                  List edges
POST   /api/v1/automation/edges/                  Create edge
DELETE /api/v1/automation/edges/{id}/             Delete edge
```

### Executions

```
GET    /api/v1/automation/executions/             List executions
GET    /api/v1/automation/executions/{id}/        Get execution
POST   /api/v1/automation/executions/{id}/cancel/ Cancel execution
POST   /api/v1/automation/executions/{id}/retry/  Retry execution
GET    /api/v1/automation/executions/{id}/flow_visualization/ Get flow viz
```

### Goals

```
GET    /api/v1/automation/goals/                  List goals
POST   /api/v1/automation/goals/                  Create goal
PATCH  /api/v1/automation/goals/{id}/             Update goal
DELETE /api/v1/automation/goals/{id}/             Delete goal
POST   /api/v1/automation/goals/{id}/update_analytics/ Update analytics
```

### Analytics

```
GET    /api/v1/automation/analytics/              List analytics
GET    /api/v1/automation/analytics/{id}/         Get analytics
```

## Frontend Components

### Pages

1. **Automation.tsx** - Main workflow list page
   - Create/edit/delete workflows
   - Activate/pause workflows
   - View analytics
   - Duplicate workflows

2. **WorkflowBuilder.tsx** - Visual workflow builder
   - Drag-and-drop canvas
   - Node configuration
   - Trigger management
   - Settings

### Routes

```
/automation                    - Workflow list
/automation/builder/:id        - Workflow builder
/automation/analytics/:id      - Analytics dashboard
```

## Usage Examples

### Creating a Workflow

```python
from modules.automation.models import Workflow

workflow = Workflow.objects.create(
    firm=firm,
    name="Welcome Campaign",
    description="Welcome new contacts",
    status="draft",
    created_by=user,
)
```

### Adding a Trigger

```python
from modules.automation.models import WorkflowTrigger

trigger = WorkflowTrigger.objects.create(
    firm=firm,
    workflow=workflow,
    trigger_type="contact_created",
    configuration={},
    is_active=True,
)
```

### Adding Nodes

```python
from modules.automation.models import WorkflowNode

# Send email node
email_node = WorkflowNode.objects.create(
    firm=firm,
    workflow=workflow,
    node_id="send_welcome_email",
    node_type="send_email",
    label="Send Welcome Email",
    position_x=100,
    position_y=100,
    configuration={
        "template_id": 123,
        "subject": "Welcome!",
    },
)

# Wait node
wait_node = WorkflowNode.objects.create(
    firm=firm,
    workflow=workflow,
    node_id="wait_2_days",
    node_type="wait_time",
    label="Wait 2 Days",
    position_x=100,
    position_y=200,
    configuration={
        "wait_type": "time",
        "wait_duration_hours": 48,
    },
)
```

### Connecting Nodes

```python
from modules.automation.models import WorkflowEdge

edge = WorkflowEdge.objects.create(
    firm=firm,
    workflow=workflow,
    source_node=email_node,
    target_node=wait_node,
)
```

### Activating Workflow

```python
workflow.activate(user=user)
```

### Manual Trigger

```python
from modules.automation.triggers import trigger_manual

execution = trigger_manual(
    firm=firm,
    workflow_id=workflow.id,
    contact=contact,
    context={"source": "manual"},
)
```

### Calculating Analytics

```python
from modules.automation.analytics import AnalyticsCalculator
from datetime import date, timedelta

end_date = date.today()
start_date = end_date - timedelta(days=30)

analytics = AnalyticsCalculator.calculate_workflow_analytics(
    workflow=workflow,
    period_start=start_date,
    period_end=end_date,
)

print(f"Total executions: {analytics.total_executions}")
print(f"Conversion rate: {analytics.goal_conversion_rate}%")
```

## Signal-Based Triggers

The automation system automatically detects events via Django signals:

**Contact Signals:**
- `post_save(Contact)` → `contact_created` or `contact_updated`

**Deal Signals:**
- `post_save(Deal)` → `deal_created`
- `pre_save(Deal)` → `deal_stage_changed`, `deal_won`, `deal_lost`

**Custom Triggers:**
Use helper functions to trigger workflows:

```python
from modules.automation.triggers import (
    trigger_form_submitted,
    trigger_email_opened,
    trigger_email_clicked,
    trigger_score_threshold,
    trigger_page_visited,
)

# Form submission
trigger_form_submitted(firm, form_id=123, submission_data={...})

# Email opened
trigger_email_opened(firm, contact, email_id=456)

# Email clicked
trigger_email_clicked(firm, contact, email_id=456, link_url="https://...")

# Score threshold
trigger_score_threshold(firm, contact, score=85, threshold=80)

# Page visited
trigger_page_visited(firm, contact, page_url="/pricing", visit_data={...})
```

## Action Executors

Action executors implement the `ActionExecutor` interface:

```python
class ActionExecutor:
    @staticmethod
    def execute(execution, node, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action and return result."""
        pass
```

**Available Executors:**
- `SendEmailAction` - Send email
- `SendSMSAction` - Send SMS
- `CreateTaskAction` - Create task
- `CreateDealAction` - Create deal
- `UpdateDealAction` - Update deal
- `UpdateContactAction` - Update contact fields
- `AddTagAction` - Add tag
- `RemoveTagAction` - Remove tag
- `WebhookAction` - Send webhook
- `InternalNotificationAction` - Send notification

## Execution Engine

The execution engine processes workflows node-by-node:

```python
from modules.automation.executor import WorkflowExecutor

executor = WorkflowExecutor(execution)
executor.execute()
```

**Features:**
- Node-by-node execution
- If/else branching
- Wait conditions
- A/B split testing
- Goal tracking
- Error handling with retry
- Idempotent execution

**Wait Processing:**
```python
from modules.automation.executor import process_waiting_executions

# Call periodically (cron/scheduler)
process_waiting_executions()
```

## Analytics System

Calculate analytics for all workflows:

```python
from modules.automation.analytics import run_daily_analytics

# Run daily
run_daily_analytics()
```

Get flow visualization:

```python
from modules.automation.analytics import AnalyticsCalculator

viz_data = AnalyticsCalculator.get_flow_visualization_data(workflow)

# Returns:
# {
#   "nodes": [{"id": "...", "visits": 100, "drop_off": 10}, ...],
#   "edges": [{"source": "...", "target": "...", "transitions": 90}, ...]
# }
```

## Security & Multi-Tenancy

All models enforce TIER 0 firm-level isolation:

- **FirmScopedManager** - Auto-filters by firm
- **Firm FK** - All models require firm
- **Permissions** - `IsAuthenticated` + `DenyPortalAccess`
- **Idempotency** - SHA-256 hashed keys
- **Audit Logging** - All triggers and actions logged

## Performance Considerations

1. **Indexing** - Comprehensive indexes on firm_id, status, dates
2. **Prefetching** - Related objects prefetched in viewsets
3. **Job Queue** - Async execution via job system
4. **Pagination** - Cursor pagination for large datasets
5. **Analytics** - Pre-calculated and cached
6. **Idempotency** - Prevents duplicate executions

## Testing

Run automation tests:

```bash
python manage.py test modules.automation
```

## Future Enhancements

1. **Advanced Visual Builder** - React Flow integration
2. **Template Library** - Pre-built workflow templates
3. **External Integrations** - Zapier, Make.com connectors
4. **Advanced Analytics** - Cohort analysis, funnel visualization
5. **A/B Testing** - Statistical significance tracking
6. **Collaboration** - Workflow comments and approvals
7. **Version Control** - Workflow versioning and rollback

## Related Documentation

- **Orchestration Engine**: docs/11 ORCHESTRATION_ENGINE_SPEC.md
- **Job Queue**: docs/20 JOB_QUEUE_SPEC.md
- **Webhooks**: docs/WEBHOOKS_SPEC.md
- **API Versioning**: docs/API_VERSIONING_POLICY.md

## Support

For questions or issues:
1. Check API documentation at `/api/docs/`
2. Review error logs in job DLQ
3. Monitor workflow analytics for drop-offs
4. Test workflows in draft mode before activating

---

**Version**: 1.0.0
**Last Updated**: 2026-01-02
**Module**: `modules.automation`
**Tasks**: AUTO-1 through AUTO-6
