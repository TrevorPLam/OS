#!/bin/bash
# generate-trace-log.sh
# Generates a trace log file from template
#
# Usage: ./scripts/generate-trace-log.sh [task-id] [intent]
#   task-id: Task identifier (e.g., TASK-001)
#   intent: Brief description of what this change does

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Validate arguments
if [[ $# -lt 2 ]]; then
    echo -e "${RED}Error:${NC} Missing required arguments"
    echo "Usage: $0 [task-id] [intent]"
    echo "  task-id: Task identifier (e.g., TASK-001)"
    echo "  intent: Brief description of what this change does"
    exit 1
fi

TASK_ID="$1"
INTENT="$2"
TRACE_DIR=".repo/traces"
TRACE_SCHEMA=".repo/templates/AGENT_TRACE_SCHEMA.json"

mkdir -p "$TRACE_DIR"

# Generate filename from task ID and timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TRACE_FILE="$TRACE_DIR/${TASK_ID}-trace-${TIMESTAMP}.json"

# Create trace log from schema template
cat > "$TRACE_FILE" <<EOF
{
  "intent": "$INTENT",
  "task_id": "$TASK_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "files": [],
  "commands": [],
  "evidence": [],
  "hitl": [],
  "unknowns": []
}
EOF

# Validate against schema if Python is available
if command -v python3 &> /dev/null && [[ -f "$TRACE_SCHEMA" ]]; then
    if python3 -c "import json, sys; json.load(open('$TRACE_FILE'))" 2>/dev/null; then
        echo -e "${GREEN}✓ Trace log created and validated${NC}"
    else
        echo -e "${RED}Warning:${NC} Trace log may be invalid JSON"
    fi
else
    echo -e "${GREEN}✓ Trace log created${NC}"
fi

echo "  File: $TRACE_FILE"
echo ""
echo "Next steps:"
echo "  1. Add modified files to 'files' array"
echo "  2. Add commands run to 'commands' array"
echo "  3. Add evidence (test results, outputs) to 'evidence' array"
echo "  4. Add HITL item IDs to 'hitl' array if applicable"
echo "  5. Add UNKNOWN items to 'unknowns' array if any"
