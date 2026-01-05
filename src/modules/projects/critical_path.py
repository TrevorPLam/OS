"""
Critical path calculation utilities for project timelines.

Implements CPM-style scheduling for TaskSchedule using TaskDependency edges.
Supports finish-to-start, start-to-start, finish-to-finish, start-to-finish
dependency types with lag offsets (in days).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class TaskNode:
    task_id: int
    duration_days: int
    planned_start_date: date | None = None


@dataclass(frozen=True)
class DependencyEdge:
    predecessor_id: int
    successor_id: int
    dependency_type: str = "finish_to_start"
    lag_days: int = 0


@dataclass(frozen=True)
class TaskScheduleResult:
    early_start: date
    early_finish: date
    late_start: date
    late_finish: date
    total_slack_days: int
    is_critical: bool


def _add_days(start: date, days: int) -> date:
    return start + timedelta(days=days)


def _finish_date(start: date, duration_days: int) -> date:
    return _add_days(start, max(duration_days, 1) - 1)


def _topological_sort(task_ids: Iterable[int], edges: List[DependencyEdge]) -> List[int]:
    in_degree = {task_id: 0 for task_id in task_ids}
    graph: Dict[int, List[int]] = {task_id: [] for task_id in task_ids}
    for edge in edges:
        graph.setdefault(edge.predecessor_id, []).append(edge.successor_id)
        in_degree[edge.successor_id] = in_degree.get(edge.successor_id, 0) + 1
        in_degree.setdefault(edge.predecessor_id, 0)

    queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
    sorted_nodes: List[int] = []

    while queue:
        node = queue.pop(0)
        sorted_nodes.append(node)
        for successor in graph.get(node, []):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)

    if len(sorted_nodes) != len(in_degree):
        raise ValueError("Dependency graph contains a cycle.")

    return sorted_nodes


def calculate_critical_path(
    tasks: List[TaskNode],
    dependencies: List[DependencyEdge],
    project_start_date: date,
) -> Tuple[Dict[int, TaskScheduleResult], List[int], int]:
    """
    Calculate critical path schedule for tasks.

    Returns:
        schedule_by_task_id: Computed schedule values
        critical_path_task_ids: Task IDs with zero total slack
        critical_path_duration_days: Total duration from project start to latest finish
    """
    task_lookup = {task.task_id: task for task in tasks}
    if not task_lookup:
        return {}, [], 0

    topo_order = _topological_sort(task_lookup.keys(), dependencies)
    early_start: Dict[int, date] = {}
    early_finish: Dict[int, date] = {}

    dependency_lookup: Dict[int, List[DependencyEdge]] = {}
    successor_lookup: Dict[int, List[DependencyEdge]] = {}
    for edge in dependencies:
        dependency_lookup.setdefault(edge.successor_id, []).append(edge)
        successor_lookup.setdefault(edge.predecessor_id, []).append(edge)

    for task_id in topo_order:
        task = task_lookup[task_id]
        base_start = task.planned_start_date or project_start_date
        candidate_start = base_start

        for edge in dependency_lookup.get(task_id, []):
            predecessor = edge.predecessor_id
            lag = edge.lag_days
            duration_days = task.duration_days
            if predecessor not in early_start:
                continue

            if edge.dependency_type == "start_to_start":
                constraint = _add_days(early_start[predecessor], lag)
            elif edge.dependency_type == "finish_to_finish":
                constraint = _add_days(early_finish[predecessor], lag - (duration_days - 1))
            elif edge.dependency_type == "start_to_finish":
                constraint = _add_days(early_start[predecessor], lag - (duration_days - 1))
            else:
                constraint = _add_days(early_finish[predecessor], lag)

            if constraint > candidate_start:
                candidate_start = constraint

        early_start[task_id] = candidate_start
        early_finish[task_id] = _finish_date(candidate_start, task.duration_days)

    project_finish = max(early_finish.values())
    late_finish: Dict[int, date] = {}
    late_start: Dict[int, date] = {}

    for task_id in reversed(topo_order):
        task = task_lookup[task_id]
        duration_days = task.duration_days
        candidate_finish = project_finish

        for edge in successor_lookup.get(task_id, []):
            successor_id = edge.successor_id
            lag = edge.lag_days
            if successor_id not in late_start:
                continue

            if edge.dependency_type == "start_to_start":
                candidate_start = _add_days(late_start[successor_id], -lag)
                constraint_finish = _finish_date(candidate_start, duration_days)
            elif edge.dependency_type == "finish_to_finish":
                constraint_finish = _add_days(late_finish[successor_id], -lag)
            elif edge.dependency_type == "start_to_finish":
                candidate_start = _add_days(late_finish[successor_id], -lag)
                constraint_finish = _finish_date(candidate_start, duration_days)
            else:
                constraint_finish = _add_days(late_start[successor_id], -lag)

            if constraint_finish < candidate_finish:
                candidate_finish = constraint_finish

        late_finish[task_id] = candidate_finish
        late_start[task_id] = _add_days(candidate_finish, -(duration_days - 1))

    schedule_by_task_id: Dict[int, TaskScheduleResult] = {}
    critical_path_task_ids: List[int] = []

    for task_id, task in task_lookup.items():
        es = early_start[task_id]
        ef = early_finish[task_id]
        ls = late_start[task_id]
        lf = late_finish[task_id]
        slack_days = (ls - es).days
        is_critical = slack_days == 0

        schedule_by_task_id[task_id] = TaskScheduleResult(
            early_start=es,
            early_finish=ef,
            late_start=ls,
            late_finish=lf,
            total_slack_days=slack_days,
            is_critical=is_critical,
        )

        if is_critical:
            critical_path_task_ids.append(task_id)

    critical_path_duration_days = (project_finish - project_start_date).days + 1

    return schedule_by_task_id, critical_path_task_ids, critical_path_duration_days
