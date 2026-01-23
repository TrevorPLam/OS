#!/bin/bash
# create-waiver.sh
# Creates a new waiver from template
#
# Usage: ./scripts/create-waiver.sh [waiver-id] [what-it-waives] [why]
#   waiver-id: Unique waiver identifier (e.g., WAIVER-001)
#   what-it-waives: What gate/rule is being waived
#   why: Brief justification

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Validate arguments
if [[ $# -lt 3 ]]; then
    echo -e "${RED}Error:${NC} Missing required arguments"
    echo "Usage: $0 [waiver-id] [what-it-waives] [why]"
    echo "  waiver-id: Unique identifier (e.g., WAIVER-001)"
    echo "  what-it-waives: What gate/rule is being waived"
    echo "  why: Brief justification"
    exit 1
fi

WAIVER_ID="$1"
WHAT_WAIVES="$2"
WHY="$3"
WAIVER_DIR=".repo/waivers"
WAIVER_FILE="$WAIVER_DIR/${WAIVER_ID}.md"
WAIVER_INDEX=".repo/policy/WAIVERS.md"
WAIVER_TEMPLATE=".repo/templates/WAIVER_TEMPLATE.md"

mkdir -p "$WAIVER_DIR"

# Read template if it exists
if [[ -f "$WAIVER_TEMPLATE" ]]; then
    TEMPLATE_CONTENT=$(cat "$WAIVER_TEMPLATE")
else
    # Use default template
    TEMPLATE_CONTENT='{
  "waives": "",
  "why": "",
  "scope": "",
  "owner": "",
  "expiration": "",
  "remediation_plan": "",
  "link": "",
  "notes": "Auto-generated waivers allowed for gate failures only."
}'
fi

# Create waiver file (JSON format)
cat > "$WAIVER_FILE" <<EOF
# $WAIVER_ID

**Created:** $(date +%Y-%m-%d)
**Expires:** [SET EXPIRATION DATE]
**Status:** Active

## What This Waives

$WHAT_WAIVES

## Why

$WHY

## Scope

[Describe scope of waiver - specific PR, feature, time period]

## Owner

[Human name responsible for this waiver]

## Remediation Plan

[How will this be fixed? Timeline?]

## Related Artifacts

- **PR:** [PR number or link]
- **Task:** [Task reference]
- **HITL:** [HITL item if applicable]

## Notes

[Additional context]
EOF

echo -e "${GREEN}Created:${NC} $WAIVER_FILE"

# Add to WAIVERS.md index if it exists, or create it
if [[ ! -f "$WAIVER_INDEX" ]]; then
    cat > "$WAIVER_INDEX" <<EOF
# Active Waivers

**File**: `.repo/policy/WAIVERS.md`

This file tracks active policy waivers. See `.repo/policy/QUALITY_GATES.md` for waiver policy.

## Active Waivers

| ID | What It Waives | Owner | Expires | Status | Filepath |
|---|---|---|---|---|---|
EOF
fi

# Add entry to index
TEMP_FILE=$(mktemp)
IN_ACTIVE_TABLE=false
TABLE_HEADER_ADDED=false

while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ "## Active Waivers" ]]; then
        IN_ACTIVE_TABLE=true
        echo "$line"
        continue
    fi

    if [[ "$IN_ACTIVE_TABLE" == true ]] && [[ "$line" =~ "^\|.*ID\|" ]] && [[ "$TABLE_HEADER_ADDED" == false ]]; then
        echo "$line"
        echo "|$WAIVER_ID|$WHAT_WAIVES|[Owner]|$(date +%Y-%m-%d)|Active|$WAIVER_FILE|"
        TABLE_HEADER_ADDED=true
        continue
    fi

    if [[ "$IN_ACTIVE_TABLE" == true ]] && [[ "$line" =~ "## Archived" ]]; then
        IN_ACTIVE_TABLE=false
    fi

    echo "$line"
done < "$WAIVER_INDEX" > "$TEMP_FILE" 2>/dev/null || {
    # If file doesn't exist or is empty, create it
    cat > "$WAIVER_INDEX" <<EOF
# Active Waivers

**File**: `.repo/policy/WAIVERS.md`

This file tracks active policy waivers. See `.repo/policy/QUALITY_GATES.md` for waiver policy.

## Active Waivers

| ID | What It Waives | Owner | Expires | Status | Filepath |
|---|---|---|---|---|---|
|$WAIVER_ID|$WHAT_WAIVES|[Owner]|$(date +%Y-%m-%d)|Active|$WAIVER_FILE|

## Archived Waivers

| ID | What It Waives | Owner | Expired | Status | Filepath |
|---|---|---|---|---|---|
EOF
    TEMP_FILE="$WAIVER_INDEX"
}

mv "$TEMP_FILE" "$WAIVER_INDEX"
echo -e "${GREEN}Updated:${NC} $WAIVER_INDEX"

echo ""
echo -e "${GREEN}✓ Waiver created successfully${NC}"
echo "  File: $WAIVER_FILE"
echo "  ID: $WAIVER_ID"
echo ""
echo "Next steps:"
echo "  1. Edit $WAIVER_FILE to fill in details"
echo "  2. Set expiration date"
echo "  3. Add owner and remediation plan"
echo "  4. Link to related PR/task/HITL"
