#!/bin/bash
# generate-agent-log.sh
# Generates an agent log file from template
#
# Usage: ./scripts/generate-agent-log.sh [task-id] [action]
#   task-id: Task identifier (e.g., TASK-001)
#   action: Brief description of action taken

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
    echo "Usage: $0 [task-id] [action]"
    echo "  task-id: Task identifier (e.g., TASK-001)"
    echo "  action: Brief description of action taken"
    exit 1
fi

TASK_ID="$1"
ACTION="$2"
LOG_TEMPLATE=".repo/templates/AGENT_LOG_TEMPLATE.md"

# Generate log file
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE=".repo/logs/${TASK_ID}-log-${TIMESTAMP}.json"
mkdir -p "$(dirname "$LOG_FILE")"

# Read template if it exists, otherwise use default JSON structure
if [[ -f "$LOG_TEMPLATE" ]]; then
    LOG_CONTENT=$(cat "$LOG_TEMPLATE")
    # Replace empty intent with action
    LOG_CONTENT=$(echo "$LOG_CONTENT" | sed "s/\"intent\": \"\"/\"intent\": \"$ACTION\"/")
else
    # Use default JSON template
    LOG_CONTENT=$(cat <<EOF
{
  "intent": "$ACTION",
  "task_id": "$TASK_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "plan": [],
  "actions": [],
  "evidence": [],
  "decisions": [],
  "risks": [],
  "follow_ups": [],
  "reasoning_summary": "",
  "notes": "No secrets. No private data. No raw chain-of-thought."
}
EOF
)
fi

echo "$LOG_CONTENT" > "$LOG_FILE"

# Validate JSON
if command -v python3 &> /dev/null; then
    if python3 -m json.tool "$LOG_FILE" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Valid JSON${NC}"
    else
        echo -e "${RED}Warning: Invalid JSON generated${NC}"
    fi
fi

echo -e "${GREEN}✓ Agent log created${NC}"
echo "  File: $LOG_FILE"
echo ""
echo "Next steps:"
echo "  1. Fill in Files Modified section"
echo "  2. Add Commands Run"
echo "  3. Add Evidence (test results, outputs)"
echo "  4. Add HITL item IDs if applicable"
echo "  5. Add UNKNOWN items if any"
