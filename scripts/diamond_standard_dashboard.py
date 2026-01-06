#!/usr/bin/env python3
"""
Diamond Standard Dashboard Generator

Parses TODO.md and generates a comprehensive status report tracking
progress toward Diamond Standard (95/100) achievement.

Usage:
    python scripts/diamond_standard_dashboard.py
    make dashboard

Output:
    DIAMOND_STANDARD_STATUS.md (auto-generated, do not edit manually)
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class Task:
    """Represents a single task from TODO.md"""

    def __init__(self, task_id: str, title: str, priority: str, task_type: str,
                 owner: str, status: str, effort: str, phase: str = "Unknown"):
        self.task_id = task_id
        self.title = title
        self.priority = priority
        self.task_type = task_type
        self.owner = owner
        self.status = status
        self.effort = effort
        self.phase = phase

    def __repr__(self):
        return f"Task({self.task_id}, {self.priority}, {self.status})"


def parse_todo_file(todo_path: Path) -> List[Task]:
    """Parse TODO.md and extract all tasks"""
    tasks = []
    content = todo_path.read_text()

    # Pattern to match task headers: ### T-###: Title
    task_pattern = r"^### (T-\d+|SEC-\d+|LLM-\d+): (.+)$"
    
    # Split into task blocks
    lines = content.split('\n')
    current_task = None
    task_data = {}
    
    for line in lines:
        # Check if this is a new task header
        match = re.match(task_pattern, line)
        if match:
            # Save previous task if exists
            if current_task and task_data:
                tasks.append(Task(
                    task_id=current_task,
                    title=task_data.get('title', ''),
                    priority=task_data.get('priority', 'P3'),
                    task_type=task_data.get('type', 'UNKNOWN'),
                    owner=task_data.get('owner', 'UNKNOWN'),
                    status=task_data.get('status', 'READY'),
                    effort=task_data.get('effort', 'M'),
                    phase=task_data.get('phase', 'Unknown')
                ))
            
            # Start new task
            current_task = match.group(1)
            task_data = {'title': match.group(2)}
            continue
        
        # Parse task attributes
        if current_task:
            if line.startswith('Priority:'):
                task_data['priority'] = line.split(':')[1].strip()
            elif line.startswith('Type:'):
                task_data['type'] = line.split(':')[1].strip()
            elif line.startswith('Owner:'):
                task_data['owner'] = line.split(':')[1].strip()
            elif line.startswith('Status:'):
                task_data['status'] = line.split(':')[1].strip()
            elif line.startswith('Effort:'):
                task_data['effort'] = line.split(':')[1].strip()
    
    # Don't forget the last task
    if current_task and task_data:
        tasks.append(Task(
            task_id=current_task,
            title=task_data.get('title', ''),
            priority=task_data.get('priority', 'P3'),
            task_type=task_data.get('type', 'UNKNOWN'),
            owner=task_data.get('owner', 'UNKNOWN'),
            status=task_data.get('status', 'READY'),
            effort=task_data.get('effort', 'M'),
            phase=task_data.get('phase', 'Unknown')
        ))
    
    return tasks


def assign_phases(tasks: List[Task]) -> List[Task]:
    """Assign diamond standard phases to tasks based on task ID ranges"""
    phase_mapping = {
        # Phase 0: Production Blockers
        'T-042': 'Phase 0: Unblock Production',
        'T-062': 'Phase 0: Unblock Production',
        'T-063': 'Phase 0: Unblock Production',
        
        # Phase 1: Security Hardening
        'SEC-6': 'Phase 1: Security Hardening',
        'SEC-7': 'Phase 1: Security Hardening',
        'T-043': 'Phase 1: Security Hardening',
        'T-044': 'Phase 1: Security Hardening',
        'T-045': 'Phase 1: Security Hardening',
        
        # Phase 2: Dependency Health
        'T-031': 'Phase 2: Dependency Health',
        'T-032': 'Phase 2: Dependency Health',
        'T-033': 'Phase 2: Dependency Health',
        'T-034': 'Phase 2: Dependency Health',
        
        # Phase 3: Test Coverage
        'T-025': 'Phase 3: Test Coverage Expansion',
        'T-048': 'Phase 3: Test Coverage Expansion',
        'T-049': 'Phase 3: Test Coverage Expansion',
        
        # Phase 4: Operations Maturity
        'T-046': 'Phase 4: Operations Maturity',
        'T-047': 'Phase 4: Operations Maturity',
        'T-050': 'Phase 4: Operations Maturity',
        'T-051': 'Phase 4: Operations Maturity',
        
        # Phase 5: Code Quality
        'T-026': 'Phase 5: Code Quality & Maintainability',
        'T-027': 'Phase 5: Code Quality & Maintainability',
        'T-028': 'Phase 5: Code Quality & Maintainability',
        'T-029': 'Phase 5: Code Quality & Maintainability',
        'T-030': 'Phase 5: Code Quality & Maintainability',
        'T-052': 'Phase 5: Code Quality & Maintainability',
        
        # Phase 6: Documentation Excellence
        'T-022': 'Phase 6: Documentation Excellence',
        'T-023': 'Phase 6: Documentation Excellence',
        'T-024': 'Phase 6: Documentation Excellence',
        'T-038': 'Phase 6: Documentation Excellence',
        'T-040': 'Phase 6: Documentation Excellence',
        'T-053': 'Phase 6: Documentation Excellence',
        
        # Phase 7: Developer Experience
        'T-013': 'Phase 7: Developer Experience',
        'T-016': 'Phase 7: Developer Experience',
        'T-054': 'Phase 7: Developer Experience',
        'T-055': 'Phase 7: Developer Experience',
        
        # Phase 8: Performance & Monitoring
        'T-056': 'Phase 8: Performance & Monitoring',
        'T-057': 'Phase 8: Performance & Monitoring',
        'T-058': 'Phase 8: Performance & Monitoring',
        'T-059': 'Phase 8: Performance & Monitoring',
        
        # Phase 9: Long-term Excellence
        'T-011': 'Phase 9: Long-term Excellence',
        'T-014': 'Phase 9: Long-term Excellence',
        'T-017': 'Phase 9: Long-term Excellence',
        'T-018': 'Phase 9: Long-term Excellence',
        'T-019': 'Phase 9: Long-term Excellence',
        'T-020': 'Phase 9: Long-term Excellence',
        'T-021': 'Phase 9: Long-term Excellence',
        'T-035': 'Phase 9: Long-term Excellence',
        'T-036': 'Phase 9: Long-term Excellence',
        'T-037': 'Phase 9: Long-term Excellence',
        'T-039': 'Phase 9: Long-term Excellence',
        'T-041': 'Phase 9: Long-term Excellence',
        'T-060': 'Phase 9: Long-term Excellence',
        'T-061': 'Phase 9: Long-term Excellence',
        'LLM-1': 'Phase 9: Long-term Excellence',
        'LLM-2': 'Phase 9: Long-term Excellence',
    }
    
    # Assign phases
    for task in tasks:
        task.phase = phase_mapping.get(task.task_id, 'Unassigned')
    
    return tasks


def calculate_metrics(tasks: List[Task]) -> Dict:
    """Calculate dashboard metrics"""
    total = len(tasks)
    
    # By status
    ready = sum(1 for t in tasks if t.status == 'READY')
    in_progress = sum(1 for t in tasks if t.status == 'IN-PROGRESS')
    blocked = sum(1 for t in tasks if t.status == 'BLOCKED')
    completed = sum(1 for t in tasks if t.status == 'COMPLETED')
    
    # By priority
    p0 = sum(1 for t in tasks if t.priority == 'P0')
    p1 = sum(1 for t in tasks if t.priority == 'P1')
    p2 = sum(1 for t in tasks if t.priority == 'P2')
    p3 = sum(1 for t in tasks if t.priority == 'P3')
    
    # By owner
    agent = sum(1 for t in tasks if t.owner == 'AGENT')
    trevor = sum(1 for t in tasks if t.owner == 'Trevor')
    
    # By phase
    phases = {}
    for task in tasks:
        phases[task.phase] = phases.get(task.phase, 0) + 1
    
    # Calculate completion percentage
    completion_pct = (completed / total * 100) if total > 0 else 0
    
    # Calculate diamond standard score (baseline 78, each P0/P1 task worth points)
    baseline_score = 78.0
    critical_tasks_total = p0 + p1
    critical_tasks_done = sum(1 for t in tasks if t.priority in ['P0', 'P1'] and t.status == 'COMPLETED')
    points_per_critical = 17.0 / max(critical_tasks_total, 1)  # 17 points needed to reach 95
    current_score = baseline_score + (critical_tasks_done * points_per_critical)
    
    return {
        'total': total,
        'ready': ready,
        'in_progress': in_progress,
        'blocked': blocked,
        'completed': completed,
        'p0': p0,
        'p1': p1,
        'p2': p2,
        'p3': p3,
        'agent': agent,
        'trevor': trevor,
        'phases': phases,
        'completion_pct': completion_pct,
        'current_score': current_score,
        'target_score': 95.0,
    }


def generate_dashboard(tasks: List[Task], metrics: Dict) -> str:
    """Generate markdown dashboard report"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    md = f"""# Diamond Standard Dashboard

**Generated:** {now}  
**Source:** TODO.md  
**Target:** 95/100 (Diamond Standard)  
**Current:** {metrics['current_score']:.1f}/100

⚠️ **This file is auto-generated. Do not edit manually.**  
Run `make dashboard` or `python scripts/diamond_standard_dashboard.py` to update.

---

## Executive Summary

### Overall Progress

**Diamond Standard Score: {metrics['current_score']:.1f}/100** (Baseline: 78, Target: 95)

Progress: {'█' * int(metrics['current_score'] / 5)}{'░' * (20 - int(metrics['current_score'] / 5))} {metrics['current_score']:.1f}%

**Task Completion: {metrics['completed']}/{metrics['total']} ({metrics['completion_pct']:.1f}%)**

---

## Status Overview

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ COMPLETED | {metrics['completed']} | {metrics['completed']/metrics['total']*100:.1f}% |
| 🔄 IN-PROGRESS | {metrics['in_progress']} | {metrics['in_progress']/metrics['total']*100:.1f}% |
| 🔴 BLOCKED | {metrics['blocked']} | {metrics['blocked']/metrics['total']*100:.1f}% |
| ⚪ READY | {metrics['ready']} | {metrics['ready']/metrics['total']*100:.1f}% |
| **TOTAL** | **{metrics['total']}** | **100%** |

---

## Priority Breakdown

| Priority | Count | Status |
|----------|-------|--------|
| 🔴 P0 (Production Blocker) | {metrics['p0']} | {'✅ Clear' if metrics['p0'] == 0 else '⚠️ BLOCKING'} |
| 🟠 P1 (High - 7 days) | {metrics['p1']} | {'✅ Clear' if metrics['p1'] == 0 else '⚠️ URGENT'} |
| 🟡 P2 (Important - 30 days) | {metrics['p2']} | {'✅ On Track' if metrics['p2'] < 10 else '⚠️ Review'} |
| 🟢 P3 (Backlog) | {metrics['p3']} | Planned |

---

## Ownership Distribution

| Owner | Count | Percentage |
|-------|-------|------------|
| 🤖 AGENT | {metrics['agent']} | {metrics['agent']/metrics['total']*100:.1f}% |
| 👤 Trevor | {metrics['trevor']} | {metrics['trevor']/metrics['total']*100:.1f}% |

**Parallel Execution Opportunity:** {metrics['agent']} tasks can be executed by AGENT while Trevor resolves {metrics['trevor']} tasks.

---

## Phase Progress

"""
    
    # Phase-by-phase breakdown
    phase_order = [
        'Phase 0: Unblock Production',
        'Phase 1: Security Hardening',
        'Phase 2: Dependency Health',
        'Phase 3: Test Coverage Expansion',
        'Phase 4: Operations Maturity',
        'Phase 5: Code Quality & Maintainability',
        'Phase 6: Documentation Excellence',
        'Phase 7: Developer Experience',
        'Phase 8: Performance & Monitoring',
        'Phase 9: Long-term Excellence',
        'Unassigned',
    ]
    
    for phase in phase_order:
        phase_tasks = [t for t in tasks if t.phase == phase]
        if not phase_tasks:
            continue
        
        completed = sum(1 for t in phase_tasks if t.status == 'COMPLETED')
        total = len(phase_tasks)
        pct = completed / total * 100 if total > 0 else 0
        
        status_icon = '✅' if pct == 100 else '🔄' if pct > 0 else '⚪'
        
        md += f"\n### {status_icon} {phase}\n\n"
        md += f"**Progress:** {completed}/{total} ({pct:.0f}%)\n\n"
        md += "| Task | Priority | Status | Owner |\n"
        md += "|------|----------|--------|-------|\n"
        
        for task in phase_tasks:
            status_emoji = {
                'COMPLETED': '✅',
                'IN-PROGRESS': '🔄',
                'BLOCKED': '🔴',
                'READY': '⚪',
            }.get(task.status, '❓')
            
            md += f"| [{task.task_id}](TODO.md) {task.title[:50]}{'...' if len(task.title) > 50 else ''} "
            md += f"| {task.priority} | {status_emoji} {task.status} | {task.owner} |\n"
        
        md += "\n"
    
    # Critical blockers
    md += "---\n\n## 🚨 Critical Blockers\n\n"
    blockers = [t for t in tasks if t.status == 'BLOCKED' or t.priority == 'P0']
    
    if blockers:
        md += "The following tasks are blocking production readiness:\n\n"
        for task in blockers:
            md += f"- **[{task.task_id}](TODO.md)**: {task.title} ({task.owner}, {task.status})\n"
    else:
        md += "✅ No critical blockers! Ready to proceed with phased execution.\n"
    
    md += "\n---\n\n## Next Actions\n\n"
    
    # Next actions by priority
    next_ready = [t for t in tasks if t.status == 'READY' and t.priority in ['P0', 'P1']][:5]
    
    if next_ready:
        md += "### Immediate Priorities (Next 5 Tasks)\n\n"
        for i, task in enumerate(next_ready, 1):
            md += f"{i}. **[{task.task_id}](TODO.md)** ({task.priority}, {task.owner}): {task.title}\n"
    
    md += "\n### Parallel Execution Streams\n\n"
    md += "**AGENT Stream:**\n"
    agent_ready = [t for t in tasks if t.owner == 'AGENT' and t.status == 'READY' and t.priority in ['P0', 'P1']][:3]
    for task in agent_ready:
        md += f"- [{task.task_id}](TODO.md): {task.title}\n"
    
    md += "\n**Trevor Stream:**\n"
    trevor_ready = [t for t in tasks if t.owner == 'Trevor' and t.status in ['READY', 'BLOCKED'] and t.priority in ['P0', 'P1']][:3]
    for task in trevor_ready:
        md += f"- [{task.task_id}](TODO.md): {task.title}\n"
    
    md += "\n---\n\n## Timeline Estimate\n\n"
    md += f"**Current Score:** {metrics['current_score']:.1f}/100\n"
    md += f"**Target Score:** {metrics['target_score']}/100\n"
    md += f"**Gap:** {metrics['target_score'] - metrics['current_score']:.1f} points\n\n"
    
    md += "**Estimated Timeline to Diamond Standard:**\n"
    md += "- Phase 0-1 (P0/P1): 1-2 weeks\n"
    md += "- Phase 2-4: 2-3 weeks\n"
    md += "- Phase 5-8: 4-6 weeks\n"
    md += "- Phase 9: Ongoing\n\n"
    md += "**Total:** 3-4 months with systematic execution\n\n"
    
    md += "---\n\n## Diamond Standard Dimensions\n\n"
    md += "| Dimension | Current | Target | Status |\n"
    md += "|-----------|---------|--------|--------|\n"
    md += "| Architecture & Design | 90/100 | 95/100 | 🟡 Good |\n"
    md += "| Code Quality | 85/100 | 95/100 | 🟡 Good |\n"
    md += "| Testing | 75/100 | 95/100 | 🟠 Needs Work |\n"
    md += "| Documentation | 88/100 | 95/100 | 🟡 Good |\n"
    md += "| Security | 92/100 | 95/100 | 🟢 Strong |\n"
    md += "| Performance | 80/100 | 95/100 | 🟡 Good |\n"
    md += "| Developer Experience | 90/100 | 95/100 | 🟡 Good |\n"
    md += "| Operations | 60/100 | 95/100 | 🔴 Critical |\n"
    md += "| Governance | 98/100 | 95/100 | ✅ Excellent |\n\n"
    
    md += "**Key Focus Areas:**\n"
    md += "1. Operations Maturity (35-point gap)\n"
    md += "2. Test Coverage (20-point gap)\n"
    md += "3. Performance Monitoring (15-point gap)\n\n"
    
    md += "---\n\n## Audit Compliance\n\n"
    md += "| Audit | Last Run | Status | P0/P1 Findings |\n"
    md += "|-------|----------|--------|----------------|\n"
    md += "| CODEAUDIT | 2026-01-06 | ✅ Pass | 6 tasks created |\n"
    md += "| SECURITYAUDIT | 2026-01-06 | ⚠️ 2 P1 | SEC-6, SEC-7 pending |\n"
    md += "| DEPENDENCYAUDIT | 2026-01-06 | ⚠️ 4 P1 | Upgrades pending |\n"
    md += "| DOCSAUDIT | 2026-01-06 | ✅ Pass | 3 P3 tasks |\n"
    md += "| RELEASEAUDIT | 2026-01-06 | 🔴 BLOCKED | T-042 blocking |\n\n"
    
    md += "---\n\n## Pre-Launch Checklist Status\n\n"
    md += "See [PRE_LAUNCH_CHECKLIST.md](docs/PRE_LAUNCH_CHECKLIST.md) for detailed requirements.\n\n"
    
    # Count pre-launch items
    critical_p0_p1 = [t for t in tasks if t.priority in ['P0', 'P1']]
    critical_done = [t for t in critical_p0_p1 if t.status == 'COMPLETED']
    
    md += f"**Critical Tasks Completed:** {len(critical_done)}/{len(critical_p0_p1)}\n\n"
    md += f"**Production Ready:** {'✅ YES' if len(critical_done) == len(critical_p0_p1) else '❌ NO - Complete P0/P1 tasks first'}\n\n"
    
    md += "---\n\n*Dashboard auto-generated by scripts/diamond_standard_dashboard.py*\n"
    
    return md


def main():
    """Main execution"""
    # Paths
    repo_root = Path(__file__).parent.parent
    todo_path = repo_root / 'TODO.md'
    output_path = repo_root / 'DIAMOND_STANDARD_STATUS.md'
    
    print(f"📊 Generating Diamond Standard Dashboard...")
    print(f"📁 Reading: {todo_path}")
    
    # Parse tasks
    tasks = parse_todo_file(todo_path)
    print(f"✅ Parsed {len(tasks)} tasks")
    
    # Assign phases
    tasks = assign_phases(tasks)
    print(f"✅ Assigned phases")
    
    # Calculate metrics
    metrics = calculate_metrics(tasks)
    print(f"✅ Calculated metrics")
    
    # Generate dashboard
    dashboard = generate_dashboard(tasks, metrics)
    output_path.write_text(dashboard)
    print(f"✅ Generated: {output_path}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Diamond Standard Score: {metrics['current_score']:.1f}/100")
    print(f"Task Completion: {metrics['completed']}/{metrics['total']} ({metrics['completion_pct']:.1f}%)")
    print(f"P0 Tasks: {metrics['p0']} | P1 Tasks: {metrics['p1']}")
    print(f"Blocked: {metrics['blocked']} | Ready: {metrics['ready']}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
