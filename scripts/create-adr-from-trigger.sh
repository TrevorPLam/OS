#!/bin/bash
# create-adr-from-trigger.sh
# Creates an ADR from detected ADR triggers
#
# Usage: ./scripts/create-adr-from-trigger.sh [trigger-details]
#   Or run detect-adr-triggers.sh first and pipe output

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ADR_DIR="docs/adr"
ADR_TEMPLATE=".repo/templates/ADR_TEMPLATE.md"
mkdir -p "$ADR_DIR"

# Get next ADR number
LAST_ADR=$(find "$ADR_DIR" -name "ADR-*.md" 2>/dev/null | \
    sed 's/.*ADR-\([0-9]*\)\.md/\1/' | \
    sort -n | \
    tail -1 || echo "0")

NEXT_ADR=$((LAST_ADR + 1))
ADR_ID=$(printf "ADR-%04d" "$NEXT_ADR")
ADR_FILE="$ADR_DIR/$ADR_ID.md"

# Run ADR trigger detection to get context
TRIGGER_OUTPUT=$(./scripts/detect-adr-triggers.sh 2>&1 || true)

# Extract trigger information
CROSS_MODULE_IMPORTS=$(echo "$TRIGGER_OUTPUT" | grep -i "cross-module" || true)
API_CHANGES=$(echo "$TRIGGER_OUTPUT" | grep -i "API" || true)
SCHEMA_CHANGES=$(echo "$TRIGGER_OUTPUT" | grep -i "schema\|migration" || true)

# Build context
CONTEXT=""
if [[ -n "$CROSS_MODULE_IMPORTS" ]]; then
    CONTEXT+="Cross-module imports detected. "
fi
if [[ -n "$API_CHANGES" ]]; then
    CONTEXT+="API contract changes detected. "
fi
if [[ -n "$SCHEMA_CHANGES" ]]; then
    CONTEXT+="Database schema changes detected. "
fi

if [[ -z "$CONTEXT" ]]; then
    CONTEXT="ADR required per governance framework (Principle 23: ADR Required When Triggered)"
fi

# Read template
if [[ -f "$ADR_TEMPLATE" ]]; then
    TEMPLATE_CONTENT=$(cat "$ADR_TEMPLATE")
else
    # Default template
    TEMPLATE_CONTENT='{
  "context": "",
  "decision_drivers": [],
  "options": [],
  "decision": "",
  "consequences": [],
  "modules": [],
  "commands": [],
  "migration": [],
  "boundary_impact": "",
  "hitl": []
}'
fi

# Create ADR file
cat > "$ADR_FILE" <<EOF
# $ADR_ID: [Decision Title]

**Status:** Proposed
**Date:** $(date +%Y-%m-%d)
**Context:** $CONTEXT

## Context

$CONTEXT

This ADR was auto-generated from detected triggers. Please fill in the decision details.

## Decision Drivers

- [Driver 1: e.g., Need to share functionality across modules]
- [Driver 2: e.g., Performance requirements]
- [Driver 3: e.g., Maintainability concerns]

## Considered Options

### Option 1: [Option name]
- Pros: [List pros]
- Cons: [List cons]

### Option 2: [Option name]
- Pros: [List pros]
- Cons: [List cons]

## Decision

[Chosen option and rationale]

## Consequences

### Positive
- [Positive consequence 1]
- [Positive consequence 2]

### Negative
- [Negative consequence 1]
- [Negative consequence 2]

## Modules Affected

- [List affected modules]

## Boundary Impact

[Describe impact on module boundaries]

## Migration Notes

[If applicable, describe migration steps]

## HITL Items

- [List related HITL items if any]

## Notes

[Additional context or notes]
EOF

echo -e "${GREEN}✓ ADR created: $ADR_FILE${NC}"
echo ""
echo "Next steps:"
echo "  1. Fill in decision title in header"
echo "  2. Complete decision drivers"
echo "  3. Document considered options"
echo "  4. Record decision and rationale"
echo "  5. Document consequences"
echo "  6. List affected modules"
echo ""
echo "Trigger details:"
if [[ -n "$CROSS_MODULE_IMPORTS" ]]; then
    echo "  - Cross-module imports detected"
fi
if [[ -n "$API_CHANGES" ]]; then
    echo "  - API changes detected"
fi
if [[ -n "$SCHEMA_CHANGES" ]]; then
    echo "  - Schema changes detected"
fi
