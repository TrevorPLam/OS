# Gantt Chart & Timeline View System

## Overview

The Gantt Chart & Timeline View System (Task 3.6) provides comprehensive project scheduling, task dependency management, and critical path analysis for projects. It enables firms to visualize project timelines, manage task dependencies, and identify critical paths that determine project completion dates.

## Models

### ProjectTimeline

Stores timeline configuration and calculated critical path data for a project. This is a cached view of the project schedule for performance optimization.

**Key Features:**
- Project-level timeline tracking
- Critical path analysis and caching
- Task completion tracking
- Milestone counting
- Risk assessment based on critical path
- Calculation metadata storage

**Fields:**
- `project`: Project this timeline belongs to (OneToOne, required)
- `planned_start_date`: Planned project start date
- `planned_end_date`: Planned project end date
- `actual_start_date`: Actual project start date
- `actual_end_date`: Actual project end date
- `critical_path_task_ids`: List of task IDs on the critical path (JSONField)
- `critical_path_duration_days`: Duration of critical path in days
- `total_tasks`: Total number of tasks in project
- `completed_tasks`: Number of completed tasks
- `milestone_count`: Number of milestones in project
- `last_calculated_at`: When timeline was last calculated
- `calculation_metadata`: Metadata about timeline calculation (JSONField)

**Computed Properties:**
- `completion_percentage`: Project completion percentage (0-100)
- `is_on_critical_path_risk`: Whether project is at risk based on critical path analysis

**TIER 0 Compliance:**
- Inherits firm from project relationship
- Automatically scoped to firm through project

**API Endpoints:**
- `GET /api/projects/project-timelines/` - List timelines
- `POST /api/projects/project-timelines/` - Create timeline
- `GET /api/projects/project-timelines/{id}/` - Retrieve timeline
- `PUT /api/projects/project-timelines/{id}/` - Update timeline
- `DELETE /api/projects/project-timelines/{id}/` - Delete timeline
- `POST /api/projects/project-timelines/{id}/recalculate/` - Recalculate critical path

**Recalculate Endpoint:**
```
POST /api/projects/project-timelines/{id}/recalculate/
```

Triggers recalculation of critical path and timeline data. This would update:
- `critical_path_task_ids`
- `critical_path_duration_days`
- TaskSchedule early/late dates
- TaskSchedule slack values

**Note:** Full critical path algorithm (CPM - Critical Path Method) implementation is pending. Currently returns placeholder response.

### TaskSchedule

Stores scheduling information for individual tasks including calculated dates based on dependencies and constraints.

**Key Features:**
- Planned and actual schedule tracking
- Critical path analysis per task
- Scheduling constraints (ASAP, ALAP, must start/finish on date)
- Slack/float calculation
- Milestone support
- Progress tracking
- Behind-schedule detection

**Fields:**
- `task`: Task this schedule belongs to (OneToOne, required)
- `planned_start_date`: Planned start date
- `planned_end_date`: Planned end date
- `planned_duration_days`: Planned duration in days (minimum 1)
- `actual_start_date`: Actual start date
- `actual_end_date`: Actual end date
- `actual_duration_days`: Actual duration in days
- `constraint_type`: Scheduling constraint type (see choices below)
- `constraint_date`: Date for constraint (if applicable)
- `is_on_critical_path`: Whether this task is on the critical path
- `total_slack_days`: Total slack/float in days (can delay without affecting project)
- `free_slack_days`: Free slack in days (can delay without affecting successor tasks)
- `early_start_date`: Earliest possible start date (calculated)
- `early_finish_date`: Earliest possible finish date (calculated)
- `late_start_date`: Latest possible start date without delaying project (calculated)
- `late_finish_date`: Latest possible finish date without delaying project (calculated)
- `completion_percentage`: Task completion percentage (0-100)
- `is_milestone`: Whether this task is a milestone (zero duration marker)
- `milestone_date`: Date for milestone

**Constraint Types:**
- `asap`: As Soon As Possible (default)
- `alap`: As Late As Possible
- `must_start_on`: Must Start On (specific date)
- `must_finish_on`: Must Finish On (specific date)
- `start_no_earlier`: Start No Earlier Than (specific date)
- `start_no_later`: Start No Later Than (specific date)
- `finish_no_earlier`: Finish No Earlier Than (specific date)
- `finish_no_later`: Finish No Later Than (specific date)

**Computed Properties:**
- `is_behind_schedule`: True if task is past planned end date and not 100% complete
- `days_remaining`: Number of days until planned end date (negative if overdue)

**Validation:**
- Duration calculation from dates if both start and end dates are set
- Milestone date automatically set from planned start date
- Milestones must have duration of 1 day

**TIER 0 Compliance:**
- Inherits firm from task.project relationship
- Automatically scoped to firm through task

**API Endpoints:**
- `GET /api/projects/task-schedules/` - List schedules
- `POST /api/projects/task-schedules/` - Create schedule
- `GET /api/projects/task-schedules/{id}/` - Retrieve schedule
- `PUT /api/projects/task-schedules/{id}/` - Update schedule
- `DELETE /api/projects/task-schedules/{id}/` - Delete schedule
- `GET /api/projects/task-schedules/critical_path_tasks/` - Get critical path tasks for a project
- `GET /api/projects/task-schedules/milestones/` - Get milestones for a project

**Critical Path Tasks Endpoint:**
```
GET /api/projects/task-schedules/critical_path_tasks/?project=123
```

Returns all tasks on the critical path for the specified project.

**Milestones Endpoint:**
```
GET /api/projects/task-schedules/milestones/?project=123
```

Returns all milestones for the specified project, ordered by milestone date.

### TaskDependency

Explicit representation of task dependencies with dependency types for sophisticated Gantt chart visualizations.

**Key Features:**
- Four dependency types (Finish-to-Start, Start-to-Start, Finish-to-Finish, Start-to-Finish)
- Lag/lead time support
- Dependency validation (no self-dependencies, same-project only)
- Notes for documenting dependency rationale

**Fields:**
- `predecessor`: Task that must be completed first (ForeignKey, required)
- `successor`: Task that depends on the predecessor (ForeignKey, required)
- `dependency_type`: Type of dependency relationship (see choices below)
- `lag_days`: Lag time in days (positive = delay, negative = lead time)
- `notes`: Notes about this dependency

**Dependency Types:**
- `finish_to_start` (FS): Most common - successor cannot start until predecessor finishes
- `start_to_start` (SS): Successor cannot start until predecessor starts
- `finish_to_finish` (FF): Successor cannot finish until predecessor finishes
- `start_to_finish` (SF): Rarely used - successor cannot finish until predecessor starts

**Lag/Lead Time:**
- Positive lag: Delay between tasks (e.g., +3 days = wait 3 days after predecessor)
- Negative lag (lead): Overlap between tasks (e.g., -2 days = start 2 days before predecessor finishes)
- Zero: No delay (immediate succession)

**Validation:**
- Cannot create self-dependencies (task depending on itself)
- Both tasks must be in the same project
- Prevents circular dependencies (validated at model level)

**TIER 0 Compliance:**
- Inherits firm from predecessor/successor tasks
- Automatically scoped to firm through task relationships

**API Endpoints:**
- `GET /api/projects/task-dependencies/` - List dependencies
- `POST /api/projects/task-dependencies/` - Create dependency
- `GET /api/projects/task-dependencies/{id}/` - Retrieve dependency
- `PUT /api/projects/task-dependencies/{id}/` - Update dependency
- `DELETE /api/projects/task-dependencies/{id}/` - Delete dependency
- `GET /api/projects/task-dependencies/project_dependencies/` - Get all dependencies for a project

**Project Dependencies Endpoint:**
```
GET /api/projects/task-dependencies/project_dependencies/?project=123
```

Returns all dependencies for the specified project, including predecessor and successor details.

## Usage Examples

### Creating a Project Timeline

```python
from modules.projects.models import Project, ProjectTimeline

project = Project.objects.get(project_code="PROJ-001")
timeline = ProjectTimeline.objects.create(
    project=project,
    planned_start_date="2026-01-15",
    planned_end_date="2026-06-30",
    total_tasks=10,
    completed_tasks=3,
    milestone_count=3
)
```

### Creating Task Schedules

```python
from modules.projects.models import Task, TaskSchedule

task = Task.objects.get(id=1)
schedule = TaskSchedule.objects.create(
    task=task,
    planned_start_date="2026-01-15",
    planned_end_date="2026-01-31",
    planned_duration_days=15,
    constraint_type="asap",
    completion_percentage=25.00
)
```

### Creating a Milestone

```python
milestone_task = Task.objects.get(id=5)
milestone_schedule = TaskSchedule.objects.create(
    task=milestone_task,
    planned_start_date="2026-03-31",
    planned_end_date="2026-03-31",
    planned_duration_days=1,
    is_milestone=True,
    milestone_date="2026-03-31"
)
```

### Creating Task Dependencies

```python
from modules.projects.models import Task, TaskDependency

task_a = Task.objects.get(id=1)
task_b = Task.objects.get(id=2)

# Task B cannot start until Task A finishes (most common)
dependency = TaskDependency.objects.create(
    predecessor=task_a,
    successor=task_b,
    dependency_type="finish_to_start",
    lag_days=2,  # Wait 2 days after Task A finishes
    notes="Task B requires outputs from Task A"
)
```

### Creating Dependencies with Lead Time

```python
# Task D can start 3 days before Task C finishes (overlap)
TaskDependency.objects.create(
    predecessor=task_c,
    successor=task_d,
    dependency_type="finish_to_start",
    lag_days=-3,  # Start 3 days early (lead time)
    notes="Task D can begin in parallel with final days of Task C"
)
```

## API Usage Examples

### List Project Timelines

```bash
GET /api/projects/project-timelines/
```

Response:
```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "project": 123,
      "project_name": "Website Redesign",
      "project_code": "PROJ-001",
      "planned_start_date": "2026-01-15",
      "planned_end_date": "2026-06-30",
      "actual_start_date": "2026-01-15",
      "actual_end_date": null,
      "critical_path_task_ids": [1, 3, 5, 7],
      "critical_path_duration_days": 120,
      "total_tasks": 10,
      "completed_tasks": 3,
      "milestone_count": 3,
      "completion_percentage": "30.00",
      "is_on_critical_path_risk": false,
      "last_calculated_at": "2026-01-01T10:00:00Z",
      "calculation_metadata": {},
      "created_at": "2026-01-01T09:00:00Z",
      "updated_at": "2026-01-01T10:00:00Z"
    }
  ]
}
```

### Get Critical Path Tasks

```bash
GET /api/projects/task-schedules/critical_path_tasks/?project=123
```

Response:
```json
[
  {
    "id": 1,
    "task": 1,
    "task_title": "Requirements Gathering",
    "task_project_name": "Website Redesign",
    "planned_start_date": "2026-01-15",
    "planned_end_date": "2026-01-31",
    "is_on_critical_path": true,
    "total_slack_days": 0,
    "completion_percentage": "100.00"
  },
  {
    "id": 3,
    "task": 3,
    "task_title": "Design Mockups",
    "task_project_name": "Website Redesign",
    "planned_start_date": "2026-02-01",
    "planned_end_date": "2026-02-28",
    "is_on_critical_path": true,
    "total_slack_days": 0,
    "completion_percentage": "50.00"
  }
]
```

### Get Milestones

```bash
GET /api/projects/task-schedules/milestones/?project=123
```

Response:
```json
[
  {
    "id": 5,
    "task": 5,
    "task_title": "Design Approval",
    "task_project_name": "Website Redesign",
    "is_milestone": true,
    "milestone_date": "2026-02-28",
    "completion_percentage": "0.00"
  },
  {
    "id": 8,
    "task": 8,
    "task_title": "Launch",
    "task_project_name": "Website Redesign",
    "is_milestone": true,
    "milestone_date": "2026-06-30",
    "completion_percentage": "0.00"
  }
]
```

### Create Task Dependency

```bash
POST /api/projects/task-dependencies/
Content-Type: application/json

{
  "predecessor": 1,
  "successor": 2,
  "dependency_type": "finish_to_start",
  "lag_days": 0,
  "notes": "Task 2 requires completion of Task 1"
}
```

Response:
```json
{
  "id": 1,
  "predecessor": 1,
  "predecessor_title": "Requirements Gathering",
  "predecessor_project": "Website Redesign",
  "successor": 2,
  "successor_title": "Technical Specification",
  "successor_project": "Website Redesign",
  "dependency_type": "finish_to_start",
  "lag_days": 0,
  "notes": "Task 2 requires completion of Task 1",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-01T10:00:00Z"
}
```

## Critical Path Method (CPM) Algorithm

The critical path is the sequence of tasks that determines the minimum project duration. Tasks on the critical path have zero slack/float, meaning any delay in these tasks will delay the entire project.

### Algorithm Steps (To Be Implemented)

1. **Forward Pass**: Calculate early start and early finish dates
   - Start from project start date
   - For each task, early start = max(early finish of all predecessors)
   - Early finish = early start + duration

2. **Backward Pass**: Calculate late start and late finish dates
   - Start from project end date
   - For each task (in reverse order), late finish = min(late start of all successors)
   - Late start = late finish - duration

3. **Calculate Slack**: 
   - Total slack = late start - early start (or late finish - early finish)
   - Free slack = early start of successor - early finish of current task

4. **Identify Critical Path**:
   - Tasks with zero total slack are on the critical path
   - Critical path duration = sum of durations of critical path tasks

### Dependencies and Constraints

- **Finish-to-Start (FS)**: Successor early start = predecessor early finish + lag
- **Start-to-Start (SS)**: Successor early start = predecessor early start + lag
- **Finish-to-Finish (FF)**: Successor early finish = predecessor early finish + lag
- **Start-to-Finish (SF)**: Successor early finish = predecessor early start + lag

### Resource Leveling (Future Enhancement)

After critical path calculation, resource leveling can be applied to:
- Smooth resource usage
- Avoid over-allocation
- Minimize peak resource requirements
- Extend non-critical tasks to use available slack

## Database Schema

### ProjectTimeline Table

```sql
CREATE TABLE projects_timeline (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL UNIQUE REFERENCES projects_project(id),
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    critical_path_task_ids JSONB DEFAULT '[]',
    critical_path_duration_days INTEGER DEFAULT 0,
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    milestone_count INTEGER DEFAULT 0,
    last_calculated_at TIMESTAMP WITH TIME ZONE,
    calculation_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### TaskSchedule Table

```sql
CREATE TABLE projects_task_schedule (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL UNIQUE REFERENCES projects_task(id),
    planned_start_date DATE,
    planned_end_date DATE,
    planned_duration_days INTEGER DEFAULT 1 CHECK (planned_duration_days >= 1),
    actual_start_date DATE,
    actual_end_date DATE,
    actual_duration_days INTEGER,
    constraint_type VARCHAR(20) DEFAULT 'asap',
    constraint_date DATE,
    is_on_critical_path BOOLEAN DEFAULT FALSE,
    total_slack_days INTEGER DEFAULT 0,
    free_slack_days INTEGER DEFAULT 0,
    early_start_date DATE,
    early_finish_date DATE,
    late_start_date DATE,
    late_finish_date DATE,
    completion_percentage NUMERIC(5,2) DEFAULT 0.00 CHECK (completion_percentage >= 0),
    is_milestone BOOLEAN DEFAULT FALSE,
    milestone_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX proj_sch_task_idx ON projects_task_schedule(task_id);
CREATE INDEX proj_sch_crit_idx ON projects_task_schedule(is_on_critical_path);
CREATE INDEX proj_sch_mile_idx ON projects_task_schedule(is_milestone);
CREATE INDEX proj_sch_start_idx ON projects_task_schedule(planned_start_date);
```

### TaskDependency Table

```sql
CREATE TABLE projects_task_dependency (
    id BIGSERIAL PRIMARY KEY,
    predecessor_id BIGINT NOT NULL REFERENCES projects_task(id),
    successor_id BIGINT NOT NULL REFERENCES projects_task(id),
    dependency_type VARCHAR(20) DEFAULT 'finish_to_start',
    lag_days INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (predecessor_id, successor_id)
);

CREATE INDEX proj_dep_pred_idx ON projects_task_dependency(predecessor_id);
CREATE INDEX proj_dep_succ_idx ON projects_task_dependency(successor_id);
```

## Integration Points

### With Resource Planning Module

- Task schedules can be correlated with resource allocations
- Over-allocated resources can be identified when combined with task schedules
- Resource availability can influence task scheduling

### With Time Tracking Module

- Actual task completion feeds into schedule updates
- Time entry data can update `actual_start_date` and `actual_end_date`
- Variance between planned and actual durations can be tracked

### With Client Portal

- Clients can view project timelines (if permissions allow)
- Milestone dates can trigger client notifications
- Behind-schedule tasks can be flagged for client attention

## Admin Interface

All models have comprehensive Django Admin interfaces:

### ProjectTimelineAdmin
- List view with completion percentage and risk indicators
- Fieldsets for timeline dates, critical path, statistics, and calculation metadata
- Read-only fields for calculated values

### TaskScheduleAdmin
- List view with schedule dates, progress, and critical path indicators
- Fieldsets for planned/actual schedule, constraints, critical path analysis, and milestones
- Read-only fields for computed properties

### TaskDependencyAdmin
- List view with predecessor, successor, and dependency type
- Validation display for same-project check
- Search by task titles and project names

## Future Enhancements

1. **Critical Path Algorithm Implementation**
   - Full CPM calculation with forward/backward pass
   - Automatic slack calculation
   - Real-time critical path updates

2. **Resource Leveling**
   - Smooth resource usage across timeline
   - Automatic task rescheduling to avoid conflicts
   - Resource-constrained scheduling

3. **Gantt Chart Visualization**
   - Interactive Gantt chart UI component
   - Drag-and-drop task rescheduling
   - Dependency visualization with arrows
   - Zoom and pan capabilities

4. **Baseline Tracking**
   - Save baseline schedules for comparison
   - Variance analysis (planned vs. actual)
   - Schedule performance index (SPI) calculation

5. **What-If Analysis**
   - Simulate schedule changes
   - Impact analysis for delays
   - Resource reallocation scenarios

6. **Monte Carlo Simulation**
   - Probabilistic schedule forecasting
   - Risk analysis for task durations
   - Confidence intervals for project completion

## Testing Considerations

### Unit Tests
- Model validation (dates, constraints, dependencies)
- Computed properties (completion percentage, slack, etc.)
- Critical path calculation logic

### Integration Tests
- API endpoint responses
- Dependency creation and validation
- Critical path recalculation

### Performance Tests
- Large project timelines (1000+ tasks)
- Complex dependency graphs
- Query optimization for timeline views

## Security & Privacy

- **TIER 0 Compliance**: All models automatically scoped to firm
- **Portal Access**: Denied by default via DenyPortalAccess permission
- **Admin Access**: Full CRUD operations for firm staff
- **API Access**: Authenticated users with firm-scoped queries

## Migration

Database migration: `0005_add_gantt_chart_timeline_models.py`

To apply:
```bash
python manage.py migrate projects
```

## Related Documentation

- [Resource Planning & Allocation](./resource-planning.md) - Task 3.2
- [CRM Module](./crm-module.md) - Task 3.1
- [Profitability Reporting](./profitability-reporting.md) - Task 3.3
- [Complex Tasks Implementation Summary](./complex-tasks-implementation-summary.md)
