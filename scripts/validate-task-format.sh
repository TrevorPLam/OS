#!/bin/bash
# validate-task-format.sh
# Validates task format in TODO.md, BACKLOG.md, or ARCHIVE.md
#
# Usage: ./scripts/validate-task-format.sh [task-file]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate arguments
if [[ $# -lt 1 ]]; then
    echo -e "${RED}Error:${NC} Missing task file"
    echo "Usage: $0 [task-file]"
    echo "  task-file: .repo/tasks/TODO.md, BACKLOG.md, or ARCHIVE.md"
    exit 1
fi

TASK_FILE="$1"

if [[ ! -f "$TASK_FILE" ]]; then
    echo -e "${RED}Error:${NC} Task file not found: $TASK_FILE"
    exit 1
fi

ERRORS=0
WARNINGS=0

# Check for task format
echo "Validating task format in $TASK_FILE..."

# Check for task headers (### [TASK-XXX])
TASK_COUNT=$(grep -c "^### \[TASK-" "$TASK_FILE" || echo "0")
if [[ "$TASK_COUNT" -eq 0 ]]; then
    echo -e "${YELLOW}⚠ Warning:${NC} No tasks found in file"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✓ Found $TASK_COUNT task(s)${NC}"
fi

# Validate each task
while IFS= read -r line; do
    if [[ "$line" =~ ^###\ \[TASK- ]]; then
        TASK_ID=$(echo "$line" | sed -n 's/^### \[\(TASK-[0-9]*\)\].*/\1/p')
        TASK_TITLE=$(echo "$line" | sed -n 's/^### \[TASK-[0-9]*\] \(.*\)/\1/p')

        # Read task block (until next ### or end of file)
        TASK_BLOCK=""
        IN_TASK=true
        while IFS= read -r task_line && [[ "$IN_TASK" == true ]]; do
            if [[ "$task_line" =~ ^###\ \[TASK- ]] && [[ "$task_line" != "$line" ]]; then
                IN_TASK=false
                break
            fi
            TASK_BLOCK+="$task_line"$'\n'
        done <<< "$(tail -n +$(grep -n "^### \[TASK-" "$TASK_FILE" | grep -n "$line" | cut -d: -f1 | head -1) "$TASK_FILE")"

        # Check required fields
        if ! echo "$TASK_BLOCK" | grep -q "^\*\*Priority:\*\*"; then
            echo -e "${RED}✗ $TASK_ID: Missing Priority field${NC}"
            ERRORS=$((ERRORS + 1))
        fi

        if ! echo "$TASK_BLOCK" | grep -q "^\*\*Status:\*\*"; then
            echo -e "${RED}✗ $TASK_ID: Missing Status field${NC}"
            ERRORS=$((ERRORS + 1))
        fi

        if ! echo "$TASK_BLOCK" | grep -q "^\*\*Created:\*\*"; then
            echo -e "${RED}✗ $TASK_ID: Missing Created field${NC}"
            ERRORS=$((ERRORS + 1))
        fi

        if ! echo "$TASK_BLOCK" | grep -q "^#### Acceptance Criteria"; then
            echo -e "${YELLOW}⚠ $TASK_ID: Missing Acceptance Criteria section${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi

        # Check priority format
        PRIORITY=$(echo "$TASK_BLOCK" | grep "^\*\*Priority:\*\*" | sed 's/.*\*\*Priority:\*\* *\(P[0-3]\).*/\1/')
        if [[ ! "$PRIORITY" =~ ^P[0-3]$ ]]; then
            echo -e "${RED}✗ $TASK_ID: Invalid priority format (should be P0, P1, P2, or P3)${NC}"
            ERRORS=$((ERRORS + 1))
        fi

        # Check status format
        STATUS=$(echo "$TASK_BLOCK" | grep "^\*\*Status:\*\*" | sed 's/.*\*\*Status:\*\* *\([^ ]*\).*/\1/')
        VALID_STATUSES=("Pending" "In Progress" "Completed" "Blocked")
        if [[ ! " ${VALID_STATUSES[@]} " =~ " ${STATUS} " ]]; then
            echo -e "${YELLOW}⚠ $TASK_ID: Unusual status: $STATUS${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
done < "$TASK_FILE"

# Summary
echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}✗ Validation FAILED with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Validation passed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${GREEN}✓ Validation PASSED${NC}"
    exit 0
fi
