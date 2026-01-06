# AGENTS.md — Projects Module (Project Execution)

Last Updated: 2026-01-06
Applies To: `src/modules/projects/`

## Purpose

Project execution, task management, and time tracking for client engagements.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | Project, Task, TimeEntry, Expense, Milestone (~2188 LOC) |
| `critical_path.py` | Critical path calculation |
| `signals.py` | Project event hooks |

## Domain Model

```
Project (client engagement execution)
    ├── Milestone (key deliverables)
    │       └── Task (individual work items)
    │               └── TimeEntry (time logged)
    └── Expense (project expenses)
```

## Key Models

### Project

Client engagement:

```python
class Project(models.Model):
    firm: FK[Firm]
    client: FK[Client]
    
    name: str
    description: str
    
    status: str                       # planning, active, on_hold, completed
    
    # Timeline
    start_date: Date
    end_date: Date
    
    # Budget
    budget_hours: Decimal
    budget_amount: Decimal
    
    # Billing
    billing_type: str                 # fixed, hourly, retainer
    hourly_rate: Decimal
    
    # Tracking
    total_hours_logged: Decimal
    total_expenses: Decimal
```

### Task

Work item:

```python
class Task(models.Model):
    project: FK[Project]
    milestone: FK[Milestone]
    parent: FK[self]                  # Subtasks
    
    title: str
    description: str
    
    status: str                       # todo, in_progress, review, done
    priority: str                     # low, medium, high, urgent
    
    # Assignment
    assigned_to: FK[User]
    
    # Timeline
    due_date: Date
    estimated_hours: Decimal
    
    # Dependencies
    depends_on: M2M[Task]
```

### TimeEntry

Time logged:

```python
class TimeEntry(models.Model):
    task: FK[Task]
    user: FK[User]
    
    date: Date
    hours: Decimal
    description: str
    
    # Billing
    is_billable: bool
    hourly_rate: Decimal
    
    status: str                       # draft, submitted, approved
```

### Expense

Project expense:

```python
class Expense(models.Model):
    project: FK[Project]
    submitted_by: FK[User]
    
    category: str                     # travel, meals, software, etc.
    description: str
    amount: Decimal
    date: Date
    
    is_billable: bool
    status: str                       # draft, submitted, approved
```

## Critical Path

`critical_path.py` calculates project critical path based on task dependencies.

## Dependencies

- **Depends on**: `firm/`, `clients/`
- **Used by**: Finance (billing), Documents (project files)

## URLs

All routes under `/api/v1/projects/`:

```
GET/POST   /projects/
GET/PUT    /projects/{id}/

GET/POST   /projects/{id}/milestones/
GET/POST   /projects/{id}/tasks/
GET/PUT    /tasks/{id}/

GET/POST   /time-entries/
GET/PUT    /time-entries/{id}/

GET/POST   /expenses/
GET/PUT    /expenses/{id}/
```
