#!/bin/bash
# promote-task.sh
# Promotes a task from BACKLOG.md to TODO.md
#
# Usage: ./scripts/promote-task.sh [task-id]
#   task-id: Optional task ID (e.g., TASK-001). If not provided, promotes highest priority task.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TODO_FILE=".repo/tasks/TODO.md"
BACKLOG_FILE=".repo/tasks/BACKLOG.md"

# Check if TODO.md already has a task
if grep -q "^### \[TASK-" "$TODO_FILE" 2>/dev/null; then
    CURRENT_TASK=$(grep "^### \[TASK-" "$TODO_FILE" | head -1 | sed 's/^### \[\(TASK-[0-9]*\)\].*/\1/')
    echo -e "${YELLOW}Warning:${NC} TODO.md already contains task: $CURRENT_TASK"
    echo "Only one task should be in TODO.md at a time."
    echo "Archive the current task first, or remove it manually."
    exit 1
fi

# If task ID provided, promote that specific task
if [[ $# -ge 1 ]]; then
    TASK_ID="$1"

    # Find task in BACKLOG
    if ! grep -q "^### \[$TASK_ID\]" "$BACKLOG_FILE" 2>/dev/null; then
        echo -e "${RED}Error:${NC} Task $TASK_ID not found in BACKLOG.md"
        exit 1
    fi

    # Extract task block from BACKLOG
    TASK_START=$(grep -n "^### \[$TASK_ID\]" "$BACKLOG_FILE" | cut -d: -f1)
    if [[ -z "$TASK_START" ]]; then
        echo -e "${RED}Error:${NC} Could not find task $TASK_ID in BACKLOG.md"
        exit 1
    fi

    # Read task block (until next ### or end of file)
    TASK_BLOCK=""
    LINE_NUM=$TASK_START
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ $LINE_NUM -lt $TASK_START ]]; then
            LINE_NUM=$((LINE_NUM + 1))
            continue
        fi

        # Stop at next task or end of file
        if [[ $LINE_NUM -gt $TASK_START ]] && [[ "$line" =~ ^###\ \[TASK- ]]; then
            break
        fi

        TASK_BLOCK+="$line"$'\n'
        LINE_NUM=$((LINE_NUM + 1))
    done < "$BACKLOG_FILE"

    # Update status to "In Progress"
    TASK_BLOCK=$(echo "$TASK_BLOCK" | sed 's/\*\*Status:\*\* Pending/\*\*Status:\*\* In Progress/')

    # Add to TODO.md
    {
        echo "# 🎯 Current Task"
        echo ""
        echo "> **Single Active Task** — Only ONE task should be in this file at any time."
        echo ""
        echo "---"
        echo ""
        echo "$TASK_BLOCK"
    } > "$TODO_FILE"

    # Remove from BACKLOG.md
    TEMP_FILE=$(mktemp)
    IN_TASK=false
    SKIP_TASK=false

    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" =~ ^###\ \[$TASK_ID\] ]]; then
            SKIP_TASK=true
            continue
        fi

        if [[ "$SKIP_TASK" == true ]]; then
            # Stop skipping when we hit next task or section
            if [[ "$line" =~ ^###\ \[TASK- ]] || [[ "$line" =~ ^##\  ]]; then
                SKIP_TASK=false
                echo "$line"
            fi
            continue
        fi

        echo "$line"
    done < "$BACKLOG_FILE" > "$TEMP_FILE"

    mv "$TEMP_FILE" "$BACKLOG_FILE"

    echo -e "${GREEN}✓ Task $TASK_ID promoted to TODO.md${NC}"
    echo "  Updated status to: In Progress"
    echo "  Removed from BACKLOG.md"

else
    # Promote highest priority task (first P0, then P1, etc.)
    echo "Finding highest priority task in BACKLOG..."

    # Find first task in BACKLOG (should be highest priority)
    FIRST_TASK=$(grep "^### \[TASK-" "$BACKLOG_FILE" | head -1 | sed 's/^### \[\(TASK-[0-9]*\)\].*/\1/')

    if [[ -z "$FIRST_TASK" ]]; then
        echo -e "${RED}Error:${NC} No tasks found in BACKLOG.md"
        exit 1
    fi

    echo "Promoting task: $FIRST_TASK"
    # Recursively call with task ID
    exec "$0" "$FIRST_TASK"
fi
