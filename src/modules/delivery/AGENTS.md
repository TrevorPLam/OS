# AGENTS.md — Delivery Module (Delivery Templates)

Last Updated: 2026-01-06

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.
Applies To: `src/modules/delivery/`

## Purpose

DAG-based delivery templates for creating WorkItems when engagements are activated.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | DeliveryTemplate, DeliveryNode, DeliveryEdge, TemplateInstantiation (~692 LOC) |
| `instantiator.py` | Template → WorkItem conversion |

## Domain Model

```
DeliveryTemplate (DAG template)
    ├── DeliveryNode (individual tasks/deliverables)
    └── DeliveryEdge (dependencies between nodes)

TemplateInstantiation (when template was applied)
    └── Creates WorkItems in clients module
```

## Key Models

### DeliveryTemplate

Versioned delivery template:

```python
class DeliveryTemplate(models.Model):
    firm: FK[Firm]
    
    name: str
    code: str                         # Stable identifier
    version: int                      # Increments on publish
    
    status: str                       # draft, published, deprecated
    
    applies_to: str                   # engagement, engagement_line, service_code
    
    # DAG validation
    is_valid_dag: bool                # Computed on save
    
    # Metadata
    estimated_hours: Decimal
    estimated_duration_days: int
```

### DeliveryNode

Individual deliverable in template:

```python
class DeliveryNode(models.Model):
    template: FK[DeliveryTemplate]
    
    node_id: str                      # Unique within template
    name: str
    description: str
    
    # Timing
    estimated_hours: Decimal
    offset_days: int                  # Days from engagement start
    duration_days: int
    
    # Assignment
    default_role: str                 # Role to assign to
    
    # Recurrence (optional)
    recurrence_rule: FK[RecurrenceRule]
```

### DeliveryEdge

Dependency between nodes:

```python
class DeliveryEdge(models.Model):
    template: FK[DeliveryTemplate]
    
    source_node: FK[DeliveryNode]
    target_node: FK[DeliveryNode]
    
    edge_type: str                    # finish_to_start, start_to_start, etc.
    lag_days: int                     # Delay between nodes
```

### TemplateInstantiation

Record of when template was applied:

```python
class TemplateInstantiation(models.Model):
    template: FK[DeliveryTemplate]
    template_version: int             # Version at instantiation
    
    # Target
    engagement: FK[ClientEngagement]
    
    instantiated_at: DateTime
    instantiated_by: FK[User]
    
    # Results
    work_items_created: JSONField     # List of WorkItem IDs created
```

## DAG Validation

Templates are validated on save:

```python
def validate_dag(template):
    """
    Validates:
    1. No cycles (is acyclic)
    2. All edges reference valid nodes
    3. Exactly one root node (no incoming edges)
    4. All nodes reachable from root
    """
```

## Instantiation Flow

```python
from modules.delivery.instantiator import TemplateInstantiator

instantiator = TemplateInstantiator(template)

work_items = instantiator.instantiate(
    engagement=engagement,
    start_date=engagement.start_date,
    assignee_map={
        "senior_consultant": user_1,
        "analyst": user_2,
    }
)

# Returns list of WorkItem objects with:
# - Correct dependencies (based on edges)
# - Due dates (based on offset_days + duration_days)
# - Assignments (based on role mapping)
```

## Template Applies To

| Value | Description |
|-------|-------------|
| `engagement` | Apply to entire engagement |
| `engagement_line` | Apply per line item |
| `service_code` | Apply when specific service ordered |
| `product_code` | Apply when specific product ordered |

## Edge Types

| Type | Description |
|------|-------------|
| `finish_to_start` | Target starts after source finishes |
| `start_to_start` | Target starts when source starts |
| `finish_to_finish` | Target finishes when source finishes |
| `start_to_finish` | Target finishes when source starts |

## Immutability

- **Published templates** cannot be modified
- **Instantiations** record exact version used
- **Changes** require new version (version number increments)

## Dependencies

- **Depends on**: `firm/`, `clients/`
- **Used by**: Engagement activation
- **Related**: `recurrence/` (for recurring deliverables)

## URLs

All routes under `/api/v1/delivery/` (internal):

```
GET/POST   /templates/
GET        /templates/{id}/
POST       /templates/{id}/publish/
GET        /templates/{id}/versions/

# Nodes and edges
GET/POST   /templates/{id}/nodes/
GET/PUT    /templates/{id}/nodes/{node_id}/
GET/POST   /templates/{id}/edges/

# Instantiation
POST       /templates/{id}/instantiate/
GET        /templates/{id}/instantiations/
```
