#!/usr/bin/env python3
"""
Archive completed task from TODO.md to ARCHIVE.md.

This script:
1. Reads the current task from .repo/tasks/TODO.md
2. Checks if all acceptance criteria are marked complete
3. Moves task to .repo/tasks/ARCHIVE.md (prepends)
4. Promotes next task from BACKLOG.md to TODO.md

Usage:
    python scripts/archive-task.py [--force]

    --force: Archive even if not all criteria are complete
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
TODO_FILE = REPO_ROOT / ".repo" / "tasks" / "TODO.md"
BACKLOG_FILE = REPO_ROOT / ".repo" / "tasks" / "BACKLOG.md"
ARCHIVE_FILE = REPO_ROOT / ".repo" / "tasks" / "ARCHIVE.md"


def parse_task(content: str) -> Optional[Dict]:
    """Parse task from markdown content."""
    lines = content.split('\n')
    task = {
        'header': '',
        'metadata': {},
        'acceptance_criteria': [],
        'notes': [],
        'raw': content
    }

    in_criteria = False
    in_notes = False
    criteria_start = None

    for i, line in enumerate(lines):
        # Task header
        if line.startswith('### [TASK-'):
            task['header'] = line
            continue

        # Metadata
        if line.startswith('- **'):
            match = re.match(r'- \*\*([^:]+):\*\*\s*(.+)', line)
            if match:
                key = match.group(1).lower().replace(' ', '_')
                task['metadata'][key] = match.group(2).strip()
            continue

        # Acceptance criteria section
        if '#### Acceptance Criteria' in line:
            in_criteria = True
            criteria_start = i
            continue

        if '#### Notes' in line:
            in_criteria = False
            in_notes = True
            continue

        if in_criteria and line.strip().startswith('- ['):
            task['acceptance_criteria'].append(line)

        if in_notes and line.strip():
            task['notes'].append(line)

    return task if task['header'] else None


def is_task_complete(task: Dict) -> bool:
    """Check if all acceptance criteria are complete."""
    if not task['acceptance_criteria']:
        return False

    for criterion in task['acceptance_criteria']:
        if not criterion.strip().startswith('- [x]'):
            return False

    return True


def extract_task_from_file(filepath: Path) -> Optional[Dict]:
    """Extract task from TODO.md or BACKLOG.md."""
    if not filepath.exists():
        return None

    content = filepath.read_text(encoding='utf-8')

    # Find task block (between "## Active Task" or "### [TASK-" and next "### [TASK-" or end)
    match = re.search(r'### \[TASK-\d+\].*?(?=\n### \[TASK-|\Z)', content, re.DOTALL)
    if match:
        return parse_task(match.group(0))

    return None


def get_next_task_from_backlog() -> Optional[Dict]:
    """Get highest priority task from backlog."""
    if not BACKLOG_FILE.exists():
        return None

    content = BACKLOG_FILE.read_text(encoding='utf-8')

    # Find first task (highest priority)
    match = re.search(r'### \[TASK-\d+\].*?(?=\n### \[TASK-|\Z)', content, re.DOTALL)
    if match:
        return parse_task(match.group(0))

    return None


def archive_task(task: Dict) -> None:
    """Add task to archive file."""
    # Add completion date if not present
    if 'completed' not in task['metadata']:
        task['metadata']['completed'] = datetime.now().strftime('%Y-%m-%d')

    # Format archived task
    archived = f"\n{task['header']}\n"
    for key, value in task['metadata'].items():
        formatted_key = key.replace('_', ' ').title()
        archived += f"- **{formatted_key}:** {value}\n"

    archived += "\n#### Acceptance Criteria\n"
    for criterion in task['acceptance_criteria']:
        archived += f"{criterion}\n"

    if task['notes']:
        archived += "\n#### Notes\n"
        archived += '\n'.join(task['notes']) + '\n'

    archived += "\n---\n"

    # Prepend to archive
    if ARCHIVE_FILE.exists():
        existing = ARCHIVE_FILE.read_text(encoding='utf-8')
        ARCHIVE_FILE.write_text(archived + existing, encoding='utf-8')
    else:
        ARCHIVE_FILE.write_text(f"# Archived Tasks\n\n{archived}", encoding='utf-8')


def update_todo_file(new_task: Optional[Dict]) -> None:
    """Update TODO.md with new task or clear it."""
    if new_task:
        # Format new task
        content = "# 🎯 Current Task\n\n"
        content += "> **Single Active Task** — Only ONE task should be in this file at any time.\n\n"
        content += "---\n\n"
        content += f"{new_task['header']}\n"
        for key, value in new_task['metadata'].items():
            formatted_key = key.replace('_', ' ').title()
            content += f"- **{formatted_key}:** {value}\n"
        content += "\n#### Acceptance Criteria\n"
        for criterion in new_task['acceptance_criteria']:
            content += f"{criterion}\n"
        if new_task['notes']:
            content += "\n#### Notes\n"
            content += '\n'.join(new_task['notes']) + '\n'

        TODO_FILE.write_text(content, encoding='utf-8')
    else:
        # Clear TODO file
        TODO_FILE.write_text(
            "# 🎯 Current Task\n\n"
            "> **No active task** — Promote a task from BACKLOG.md\n\n",
            encoding='utf-8'
        )


def remove_task_from_backlog(task_id: str) -> None:
    """Remove task from backlog file."""
    if not BACKLOG_FILE.exists():
        return

    content = BACKLOG_FILE.read_text(encoding='utf-8')

    # Remove task block
    pattern = rf'### \[{re.escape(task_id)}\].*?(?=\n### \[TASK-|\Z)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)

    BACKLOG_FILE.write_text(content, encoding='utf-8')


def update_archive_statistics():
    """Update statistics in ARCHIVE.md."""
    if not ARCHIVE_FILE.exists():
        return

    content = ARCHIVE_FILE.read_text(encoding='utf-8')

    # Count tasks by priority
    p0_count = len(re.findall(r'\*\*Priority:\*\*\s*P0', content))
    p1_count = len(re.findall(r'\*\*Priority:\*\*\s*P1', content))
    p2_count = len(re.findall(r'\*\*Priority:\*\*\s*P2', content))
    p3_count = len(re.findall(r'\*\*Priority:\*\*\s*P3', content))
    total = p0_count + p1_count + p2_count + p3_count

    # Update statistics section
    stats_section = f"""## Statistics
| Metric | Count |
|--------|-------|
| Total Completed | {total} |
| P0 Completed | {p0_count} |
| P1 Completed | {p1_count} |
| P2 Completed | {p2_count} |
| P3 Completed | {p3_count} |

*Statistics auto-updated on {datetime.now().strftime('%Y-%m-%d')}*
"""

    # Replace or add statistics section
    if re.search(r'^## Statistics', content, re.MULTILINE):
        content = re.sub(
            r'^## Statistics.*?(?=^## |\Z)',
            stats_section,
            content,
            flags=re.MULTILINE | re.DOTALL
        )
    else:
        # Add statistics after header
        content = re.sub(
            r'^(# .*?\n)',
            r'\1\n' + stats_section + '\n',
            content,
            flags=re.MULTILINE
        )

    ARCHIVE_FILE.write_text(content, encoding='utf-8')


def main():
    """Main entry point."""
    force = '--force' in sys.argv

    # Read current task
    current_task = extract_task_from_file(TODO_FILE)
    if not current_task:
        print("No task found in TODO.md")
        return 1

    # Check if complete
    if not is_task_complete(current_task) and not force:
        print("Task is not complete. All acceptance criteria must be marked [x].")
        print("Use --force to archive anyway.")
        return 1

    # Extract task ID
    task_id_match = re.search(r'\[TASK-(\d+)\]', current_task['header'])
    if not task_id_match:
        print("Could not extract task ID")
        return 1

    task_id = f"TASK-{task_id_match.group(1)}"

    # Archive task
    print(f"Archiving {task_id}...")
    archive_task(current_task)

    # Update statistics
    print("Updating archive statistics...")
    update_archive_statistics()

    # Get next task from backlog
    next_task = get_next_task_from_backlog()
    if next_task:
        next_id_match = re.search(r'\[TASK-(\d+)\]', next_task['header'])
        if next_id_match:
            next_id = f"TASK-{next_id_match.group(1)}"
            print(f"Promoting {next_id} to TODO.md...")
            next_task['metadata']['status'] = 'In Progress'
            update_todo_file(next_task)
            remove_task_from_backlog(next_id)
    else:
        print("No tasks in backlog. Clearing TODO.md...")
        update_todo_file(None)

    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
