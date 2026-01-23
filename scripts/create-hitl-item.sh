#!/bin/bash
# create-hitl-item.sh
# Creates a new HITL item from template and adds it to HITL.md index
#
# Usage: ./scripts/create-hitl-item.sh [category] [summary]
#   category: External Integration | Clarification | Risk | Feedback | Vendor
#   summary: Brief description of the HITL item

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate arguments
if [[ $# -lt 2 ]]; then
    echo -e "${RED}Error:${NC} Missing required arguments"
    echo "Usage: $0 [category] [summary]"
    echo "  category: External Integration | Clarification | Risk | Feedback | Vendor"
    echo "  summary: Brief description of the HITL item"
    exit 1
fi

CATEGORY="$1"
SUMMARY="$2"

# Validate category
VALID_CATEGORIES=("External Integration" "Clarification" "Risk" "Feedback" "Vendor")
if [[ ! " ${VALID_CATEGORIES[@]} " =~ " ${CATEGORY} " ]]; then
    echo -e "${RED}Error:${NC} Invalid category: $CATEGORY"
    echo "Valid categories: ${VALID_CATEGORIES[*]}"
    exit 1
fi

# Get next HITL ID
HITL_DIR=".repo/hitl"
HITL_INDEX=".repo/policy/HITL.md"
mkdir -p "$HITL_DIR"

# Find highest existing HITL ID
LAST_ID=$(find "$HITL_DIR" -name "HITL-*.md" 2>/dev/null | \
    sed 's/.*HITL-\([0-9]*\)\.md/\1/' | \
    sort -n | \
    tail -1 || echo "0")

NEXT_ID=$((LAST_ID + 1))
HITL_ID=$(printf "HITL-%04d" "$NEXT_ID")
HITL_FILE="$HITL_DIR/$HITL_ID.md"

# Create HITL item file
cat > "$HITL_FILE" <<EOF
# $HITL_ID: $SUMMARY

**Category:** $CATEGORY
**Required For:** [Change types that require this HITL]
**Owner:** [Human Name]
**Reviewer:** [Human Name]
**Status:** Pending
**Date Required:** $(date +%Y-%m-%d)
**Date Completed:**

## Summary

$SUMMARY

## Required Human Action Steps

1. [Action step 1]
2. [Action step 2]
3. [Action step 3]

## Evidence of Completion

- [Evidence will be added here when completed]

## Related Artifacts

- **PR:** [PR number or link]
- **Task Packet:** [Task reference]
- **ADR:** [ADR reference if applicable]
- **Waiver:** [Waiver reference if applicable]

## Notes

[Additional context or notes]
EOF

echo -e "${GREEN}Created:${NC} $HITL_FILE"

# Add to HITL.md index (Active table)
if [[ -f "$HITL_INDEX" ]]; then
    # Find the Active table and add entry
    # This is a simple implementation - assumes table format
    TEMP_FILE=$(mktemp)
    IN_ACTIVE_TABLE=false
    TABLE_ENDED=false

    while IFS= read -r line; do
        if [[ "$line" =~ "### Active" ]]; then
            IN_ACTIVE_TABLE=true
            echo "$line"
            # Print header if next line is table header
            continue
        fi

        if [[ "$IN_ACTIVE_TABLE" == true ]] && [[ "$line" =~ "^\|.*ID\|" ]]; then
            echo "$line"
            echo "|$HITL_ID|$CATEGORY|Pending|$SUMMARY|$HITL_FILE|"
            continue
        fi

        if [[ "$IN_ACTIVE_TABLE" == true ]] && [[ "$line" =~ "### Archived" ]]; then
            IN_ACTIVE_TABLE=false
            TABLE_ENDED=true
        fi

        echo "$line"
    done < "$HITL_INDEX" > "$TEMP_FILE"

    mv "$TEMP_FILE" "$HITL_INDEX"
    echo -e "${GREEN}Updated:${NC} $HITL_INDEX (added to Active table)"
else
    echo -e "${YELLOW}Warning:${NC} $HITL_INDEX not found. Please add entry manually:"
    echo "|$HITL_ID|$CATEGORY|Pending|$SUMMARY|$HITL_FILE|"
fi

echo ""
echo -e "${GREEN}✓ HITL item created successfully${NC}"
echo "  File: $HITL_FILE"
echo "  ID: $HITL_ID"
echo "  Category: $CATEGORY"
echo ""
echo "Next steps:"
echo "  1. Edit $HITL_FILE to fill in details"
echo "  2. Update Required Human Action Steps"
echo "  3. Link to related PR/task/ADR"
