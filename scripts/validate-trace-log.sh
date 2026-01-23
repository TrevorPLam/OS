#!/bin/bash
# validate-trace-log.sh
# Validates a trace log file against AGENT_TRACE_SCHEMA.json
#
# Usage: ./scripts/validate-trace-log.sh [trace-log-file]

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
    echo -e "${RED}Error:${NC} Missing trace log file"
    echo "Usage: $0 [trace-log-file]"
    exit 1
fi

TRACE_FILE="$1"
TRACE_SCHEMA=".repo/templates/AGENT_TRACE_SCHEMA.json"

if [[ ! -f "$TRACE_FILE" ]]; then
    echo -e "${RED}Error:${NC} Trace log file not found: $TRACE_FILE"
    exit 1
fi

if [[ ! -f "$TRACE_SCHEMA" ]]; then
    echo -e "${RED}Error:${NC} Schema file not found: $TRACE_SCHEMA"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error:${NC} Python 3 is required for validation"
    exit 1
fi

# Validate JSON syntax
echo "Validating JSON syntax..."
if ! python3 -m json.tool "$TRACE_FILE" > /dev/null 2>&1; then
    echo -e "${RED}✗ Invalid JSON syntax${NC}"
    python3 -m json.tool "$TRACE_FILE" 2>&1 | head -10
    exit 1
fi
echo -e "${GREEN}✓ Valid JSON syntax${NC}"

# Load schema and trace log
SCHEMA=$(python3 -c "import json; print(json.dumps(json.load(open('$TRACE_SCHEMA'))))" 2>/dev/null)
TRACE=$(python3 -c "import json; print(json.dumps(json.load(open('$TRACE_FILE'))))" 2>/dev/null)

# Check required fields
REQUIRED_FIELDS=("intent" "files" "commands" "evidence" "hitl" "unknowns")
MISSING_FIELDS=()

for field in "${REQUIRED_FIELDS[@]}"; do
    if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if '$field' in data else 1)" 2>/dev/null; then
        MISSING_FIELDS+=("$field")
    fi
done

if [[ ${#MISSING_FIELDS[@]} -gt 0 ]]; then
    echo -e "${RED}✗ Missing required fields:${NC} ${MISSING_FIELDS[*]}"
    exit 1
fi
echo -e "${GREEN}✓ All required fields present${NC}"

# Validate field types
echo "Validating field types..."

# Check files is array
if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if isinstance(data.get('files'), list) else 1)" 2>/dev/null; then
    echo -e "${RED}✗ 'files' must be an array${NC}"
    exit 1
fi

# Check commands is array
if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if isinstance(data.get('commands'), list) else 1)" 2>/dev/null; then
    echo -e "${RED}✗ 'commands' must be an array${NC}"
    exit 1
fi

# Check evidence is array
if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if isinstance(data.get('evidence'), list) else 1)" 2>/dev/null; then
    echo -e "${RED}✗ 'evidence' must be an array${NC}"
    exit 1
fi

# Check hitl is array
if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if isinstance(data.get('hitl'), list) else 1)" 2>/dev/null; then
    echo -e "${RED}✗ 'hitl' must be an array${NC}"
    exit 1
fi

# Check unknowns is array
if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if isinstance(data.get('unknowns'), list) else 1)" 2>/dev/null; then
    echo -e "${RED}✗ 'unknowns' must be an array${NC}"
    exit 1
fi

# Check intent is string
if ! echo "$TRACE" | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if isinstance(data.get('intent'), str) else 1)" 2>/dev/null; then
    echo -e "${RED}✗ 'intent' must be a string${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All field types valid${NC}"

# Summary
echo ""
echo -e "${GREEN}✓ Trace log validation PASSED${NC}"
echo "  File: $TRACE_FILE"
echo "  Schema: $TRACE_SCHEMA"
