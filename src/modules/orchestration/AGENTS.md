# AGENTS.md — Orchestration Module (Multi-Step Workflow Engine)

Last Updated: 2026-01-06
Applies To: `src/modules/orchestration/`

## Purpose

Backend engine for executing multi-step workflows with retry logic, compensation, and DLQ routing.

**Note**: This is the **backend execution engine**. For visual marketing automation, see `modules/automation/`.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | OrchestrationDefinition, OrchestrationExecution, StepExecution (~563 LOC) |
| `executor.py` | Step execution engine |

## Domain Model

```
OrchestrationDefinition (workflow template)
    └── Steps (defined in JSON)
    └── Policies (retry, timeout, concurrency)

OrchestrationExecution (single run)
    └── StepExecution (individual step attempts)
```

## Key Models

### OrchestrationDefinition

Workflow template:

```python
class OrchestrationDefinition(models.Model):
    firm: FK[Firm]
    
    name: str
    code: str                         # Stable identifier
    version: int                      # Monotonic version
    
    status: str                       # draft, published, deprecated
    
    # Step definitions
    steps_json: JSONField             # Array of step definitions
    
    # Policies
    policies: JSONField               # Timeout, retry, concurrency rules
    
    # Schemas
    input_schema: JSONField           # JSON schema for input validation
    output_schema: JSONField          # JSON schema for output
```

### OrchestrationExecution

Single execution instance:

```python
class OrchestrationExecution(models.Model):
    definition: FK[OrchestrationDefinition]
    firm: FK[Firm]
    
    # Idempotency
    idempotency_key: str              # Unique key for deduplication
    
    status: str                       # pending, running, completed, failed, compensating
    
    # Input/Output
    input_data: JSONField
    output_data: JSONField
    
    # Tracking
    current_step: str
    started_at: DateTime
    completed_at: DateTime
    
    # Error handling
    error_code: str
    error_message: str
    dlq_at: DateTime                  # When moved to DLQ
```

### StepExecution

Individual step attempt:

```python
class StepExecution(models.Model):
    orchestration: FK[OrchestrationExecution]
    
    step_code: str
    attempt_number: int
    
    status: str                       # pending, running, completed, failed, skipped
    
    # Timing
    started_at: DateTime
    completed_at: DateTime
    
    # Results
    output_data: JSONField
    error_code: str
    error_message: str
```

## Step Definition Schema

```json
{
  "steps": [
    {
      "code": "validate_input",
      "name": "Validate Input",
      "type": "sync",
      "handler": "modules.crm.handlers.validate_proposal",
      "timeout_seconds": 30,
      "retry_policy": {
        "max_attempts": 3,
        "backoff": "exponential",
        "base_delay_seconds": 5
      }
    },
    {
      "code": "create_client",
      "name": "Create Client",
      "type": "sync",
      "handler": "modules.clients.handlers.create_from_proposal",
      "depends_on": ["validate_input"],
      "compensation": "modules.clients.handlers.rollback_client"
    }
  ]
}
```

## Execution Flow

```
1. Execution created with idempotency_key
2. If duplicate key → return existing execution
3. Input validated against input_schema
4. Steps executed in dependency order
5. Each step:
   a. Create StepExecution
   b. Call handler
   c. On success → next step
   d. On failure → retry per policy
   e. Max retries exceeded → DLQ or compensation
6. All steps complete → execution completed
```

## Retry Policies

```python
# Retry policy options
{
    "max_attempts": 3,
    "backoff": "exponential",       # or "linear", "fixed"
    "base_delay_seconds": 5,
    "max_delay_seconds": 300,
    "retryable_errors": ["TIMEOUT", "RATE_LIMITED"]
}
```

## Compensation (Saga Pattern)

If a step fails after previous steps succeeded:

```
1. Step 3 fails permanently
2. Orchestration enters "compensating" status
3. Compensation handlers called in reverse order:
   - step_2.compensation()
   - step_1.compensation()
4. Orchestration marked "failed" with compensation complete
```

## Error Classification

| Error Type | Action |
|------------|--------|
| `TRANSIENT` | Retry with backoff |
| `RATE_LIMITED` | Retry with longer delay |
| `PERMANENT` | No retry, fail or compensate |
| `TIMEOUT` | Retry (configurable) |

## Idempotency

**Critical**: Always provide idempotency_key:

```python
from modules.orchestration.executor import OrchestrationExecutor

executor = OrchestrationExecutor(definition)

# Idempotent - safe to call multiple times
execution = executor.start(
    input_data={"proposal_id": 123},
    idempotency_key=f"proposal-accept-{proposal.id}",
)
```

## Dependencies

- **Depends on**: `firm/`, `jobs/` (for background execution)
- **Used by**: CRM (proposal acceptance), Finance (payment workflows)
- **Related**: `automation/` (visual workflows call orchestrations)

## Usage Example

```python
# Define orchestration
definition = OrchestrationDefinition.objects.create(
    firm=firm,
    name="Proposal Acceptance",
    code="proposal_accept",
    steps_json=[
        {"code": "validate", "handler": "..."},
        {"code": "create_client", "handler": "..."},
        {"code": "create_engagement", "handler": "...", "depends_on": ["create_client"]},
        {"code": "send_welcome", "handler": "...", "depends_on": ["create_engagement"]},
    ],
    status="published",
)

# Execute
executor = OrchestrationExecutor(definition)
execution = executor.start(
    input_data={"proposal_id": proposal.id},
    idempotency_key=f"accept-{proposal.id}",
)
```
