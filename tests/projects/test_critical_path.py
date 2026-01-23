from datetime import date

from modules.projects.critical_path import (
    DependencyEdge,
    TaskNode,
    calculate_critical_path,
)


def test_critical_path_linear_chain():
    tasks = [
        TaskNode(task_id=1, duration_days=2),
        TaskNode(task_id=2, duration_days=1),
        TaskNode(task_id=3, duration_days=3),
    ]
    dependencies = [
        DependencyEdge(predecessor_id=1, successor_id=2),
        DependencyEdge(predecessor_id=2, successor_id=3),
    ]

    schedule_map, critical_ids, duration = calculate_critical_path(
        tasks=tasks,
        dependencies=dependencies,
        project_start_date=date(2026, 1, 1),
    )

    assert duration == 6
    assert critical_ids == [1, 2, 3]
    assert schedule_map[1].total_slack_days == 0
    assert schedule_map[2].total_slack_days == 0
    assert schedule_map[3].total_slack_days == 0


def test_critical_path_parallel_tasks():
    tasks = [
        TaskNode(task_id=1, duration_days=3),
        TaskNode(task_id=2, duration_days=2),
        TaskNode(task_id=3, duration_days=2),
    ]
    dependencies = [
        DependencyEdge(predecessor_id=1, successor_id=3),
        DependencyEdge(predecessor_id=2, successor_id=3),
    ]

    schedule_map, critical_ids, duration = calculate_critical_path(
        tasks=tasks,
        dependencies=dependencies,
        project_start_date=date(2026, 1, 1),
    )

    assert duration == 4
    assert 1 in critical_ids
    assert 3 in critical_ids
    assert schedule_map[2].total_slack_days == 1
