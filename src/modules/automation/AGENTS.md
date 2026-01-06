# AGENTS.md — Automation Module (Visual Workflow Builder)

Last Updated: 2026-01-06
Applies To: `src/modules/automation/`

## Purpose

Visual workflow automation with drag-and-drop canvas, triggers, actions, and contact flow tracking.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution, ContactFlowState (~1047 LOC) |
| `views.py` | Workflow CRUD, execution management |
| `serializers.py` | Workflow serializers |
| `triggers.py` | Trigger definitions and handlers |
| `actions.py` | Action definitions and executors |
| `executor.py` | Workflow execution engine |
| `analytics.py` | Workflow performance analytics |

## Domain Model

```
Workflow (visual automation)
    ├── WorkflowNode (actions, conditions, waits)
    ├── WorkflowEdge (connections between nodes)
    ├── WorkflowTrigger (what starts it)
    └── WorkflowGoal (conversion tracking)

WorkflowExecution (single run)
    └── ContactFlowState (per-contact tracking)
```

## Key Models

### Workflow

Visual automation workflow:

```python
class Workflow(models.Model):
    firm: FK[Firm]
    name: str
    description: str
    
    status: str                       # draft, active, paused, archived
    activated_at: DateTime
    
    # Trigger configuration
    trigger_type: str
    trigger_config: JSONField
    
    # Canvas data (for visual builder)
    canvas_data: JSONField            # { nodes: [...], edges: [...], viewport: {...} }
```

### WorkflowNode

Individual node in workflow:

```python
class WorkflowNode(models.Model):
    workflow: FK[Workflow]
    node_id: str                      # Unique within workflow
    node_type: str                    # trigger, action, condition, wait, goal
    
    # Node configuration
    action_type: str                  # send_email, wait_delay, branch, etc.
    config: JSONField                 # Action-specific config
    
    # Canvas position
    position_x: int
    position_y: int
```

### WorkflowEdge

Connection between nodes:

```python
class WorkflowEdge(models.Model):
    workflow: FK[Workflow]
    source_node: FK[WorkflowNode]
    target_node: FK[WorkflowNode]
    
    # For conditional branches
    condition_label: str              # "yes", "no", "default"
```

### WorkflowExecution

Single execution instance:

```python
class WorkflowExecution(models.Model):
    workflow: FK[Workflow]
    
    status: str                       # running, completed, failed, cancelled
    started_at: DateTime
    completed_at: DateTime
    
    trigger_data: JSONField           # What triggered this
    error_message: str
```

### ContactFlowState

Per-contact progress through workflow:

```python
class ContactFlowState(models.Model):
    execution: FK[WorkflowExecution]
    contact: FK[Contact]              # Or Lead/Prospect
    
    current_node: FK[WorkflowNode]
    status: str                       # waiting, processing, completed, exited
    
    # Wait state
    wait_until: DateTime
    
    # History
    visited_nodes: JSONField          # List of node IDs visited
    entered_at: DateTime
```

## Node Types

### Triggers

| Type | Description |
|------|-------------|
| `form_submitted` | Web form submission |
| `email_opened` | Email opened |
| `email_clicked` | Email link clicked |
| `tag_added` | Tag applied to contact |
| `deal_stage_changed` | Deal moved in pipeline |
| `appointment_booked` | Calendar booking |
| `webhook_received` | External webhook |
| `manual` | Manually triggered |

### Actions

| Type | Description |
|------|-------------|
| `send_email` | Send email from template |
| `send_sms` | Send SMS message |
| `add_tag` | Add tag to contact |
| `remove_tag` | Remove tag from contact |
| `update_field` | Update contact field |
| `create_task` | Create task for staff |
| `notify_user` | Send internal notification |
| `webhook` | Call external webhook |
| `add_to_campaign` | Add to email campaign |

### Flow Control

| Type | Description |
|------|-------------|
| `wait_delay` | Wait fixed duration |
| `wait_until` | Wait until date/time |
| `wait_condition` | Wait for condition |
| `branch` | If/else branch |
| `split` | A/B test split |
| `goal` | Conversion goal (exits on match) |
| `exit` | Exit workflow |

## Execution Engine

```python
from modules.automation.executor import WorkflowExecutor

executor = WorkflowExecutor(workflow)

# Start execution for contact
execution = executor.start(contact, trigger_data)

# Process next step (called by background job)
executor.process_contact(contact_flow_state)
```

## Visual Builder Integration

The frontend sends canvas data:

```json
{
  "nodes": [
    { "id": "node-1", "type": "trigger", "position": { "x": 100, "y": 100 }, "data": {...} },
    { "id": "node-2", "type": "action", "position": { "x": 100, "y": 200 }, "data": {...} }
  ],
  "edges": [
    { "source": "node-1", "target": "node-2" }
  ]
}
```

Backend validates and creates WorkflowNode/WorkflowEdge records.

## Dependencies

- **Depends on**: `firm/`, `clients/`, `crm/`, `communications/`, `marketing/`
- **Used by**: Marketing automation, CRM workflows
- **Related**: `orchestration/` (for backend multi-step processes)

## URLs

All routes under `/api/v1/automation/`:

```
GET/POST   /workflows/
GET/PUT    /workflows/{id}/
POST       /workflows/{id}/activate/
POST       /workflows/{id}/pause/
POST       /workflows/{id}/archive/

GET        /workflows/{id}/executions/
GET        /workflows/{id}/analytics/

POST       /workflows/{id}/test/           # Test with sample contact

# Manual trigger
POST       /workflows/{id}/trigger/
```
