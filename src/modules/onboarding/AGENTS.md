# AGENTS.md — Onboarding Module

Last Updated: 2026-01-06
Applies To: `src/modules/onboarding/`

## Purpose

Client onboarding workflows and checklist templates.

## Key Components

| File | Purpose |
|------|---------|
| `models.py` | OnboardingTemplate, OnboardingChecklist, OnboardingTask |
| `views.py` | Onboarding endpoints |
| `serializers.py` | Onboarding serializers |

## Domain Model

```
OnboardingTemplate (reusable checklist template)
    └── OnboardingTemplateTask (template items)

OnboardingChecklist (instance for a client)
    └── OnboardingTask (checklist items)
```

## Key Models

### OnboardingTemplate

Reusable template:

```python
class OnboardingTemplate(models.Model):
    firm: FK[Firm]
    
    name: str
    description: str
    
    # Auto-apply
    auto_apply_to_new_clients: bool
```

### OnboardingChecklist

Client-specific instance:

```python
class OnboardingChecklist(models.Model):
    firm: FK[Firm]
    client: FK[Client]
    template: FK[OnboardingTemplate]
    
    status: str                       # not_started, in_progress, completed
    
    started_at: DateTime
    completed_at: DateTime
    
    # Progress
    total_tasks: int
    completed_tasks: int
```

### OnboardingTask

Individual checklist item:

```python
class OnboardingTask(models.Model):
    checklist: FK[OnboardingChecklist]
    
    title: str
    description: str
    
    order: int
    is_required: bool
    
    # Assignment
    owner_type: str                   # staff, client
    assigned_to: FK[User]
    
    # Status
    status: str                       # pending, in_progress, completed, skipped
    completed_at: DateTime
    completed_by: FK[User]
    
    # Due date
    due_days_offset: int              # Days from checklist start
```

## Onboarding Flow

```
1. New client created (from accepted Proposal)
2. OnboardingTemplate auto-applied (or manually selected)
3. OnboardingChecklist created with tasks
4. Tasks assigned to staff and/or client
5. Progress tracked via portal and notifications
6. Checklist marked complete when all required tasks done
```

## Dependencies

- **Depends on**: `firm/`, `clients/`
- **Used by**: Client portal (view onboarding tasks)
- **Triggered by**: Client creation

## URLs

All routes under `/api/v1/onboarding/`:

```
# Templates
GET/POST   /templates/
GET/PUT    /templates/{id}/
GET/POST   /templates/{id}/tasks/

# Checklists
GET        /checklists/
GET        /checklists/{id}/
POST       /checklists/{id}/start/

# Tasks
GET/PUT    /tasks/{id}/
POST       /tasks/{id}/complete/
POST       /tasks/{id}/skip/
```
