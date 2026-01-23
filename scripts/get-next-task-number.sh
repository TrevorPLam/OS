#!/bin/bash
# get-next-task-number.sh
# Gets the next available task number by scanning TODO.md, BACKLOG.md, and ARCHIVE.md
#
# Usage: ./scripts/get-next-task-number.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

TASKS_DIR=".repo/tasks"
TODO_FILE="$TASKS_DIR/TODO.md"
BACKLOG_FILE="$TASKS_DIR/BACKLOG.md"
ARCHIVE_FILE="$TASKS_DIR/ARCHIVE.md"

# Find all task numbers
ALL_TASK_NUMS=$(cat "$TODO_FILE" "$BACKLOG_FILE" "$ARCHIVE_FILE" 2>/dev/null | \
    grep -oE '\[TASK-[0-9]+\]' | \
    sed 's/\[TASK-\([0-9]*\)\]/\1/' | \
    sort -n)

# Get highest number
LAST_NUM=$(echo "$ALL_TASK_NUMS" | tail -1 || echo "0")

# Next number
NEXT_NUM=$((LAST_NUM + 1))

# Format as TASK-XXX (zero-padded to 3 digits)
printf "TASK-%03d\n" "$NEXT_NUM"
