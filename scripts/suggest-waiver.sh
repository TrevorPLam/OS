#!/bin/bash
# suggest-waiver.sh
# Suggests waiver creation based on governance-verify failures
#
# Usage: ./scripts/suggest-waiver.sh [governance-verify-output-file]
#   If no file provided, runs governance-verify and captures output

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ $# -ge 1 ]] && [[ -f "$1" ]]; then
    VERIFY_OUTPUT=$(cat "$1")
else
    # Run governance-verify and capture output
    VERIFY_OUTPUT=$(./scripts/governance-verify.sh 2>&1 || true)
fi

WAIVERABLE_FAILURES=()
FAILURE_TYPE=""

# Parse governance-verify output for waiverable failures
while IFS= read -r line; do
    # Check for waiverable gate failures
    if echo "$line" | grep -qiE "(warning|waiverable|coverage|performance|bundle|budget)"; then
        WAIVERABLE_FAILURES+=("$line")
    fi

    # Detect failure type
    if echo "$line" | grep -qiE "coverage"; then
        FAILURE_TYPE="coverage"
    elif echo "$line" | grep -qiE "(performance|bundle|budget)"; then
        FAILURE_TYPE="performance"
    elif echo "$line" | grep -qiE "warning"; then
        FAILURE_TYPE="warnings"
    fi
done <<< "$VERIFY_OUTPUT"

if [[ ${#WAIVERABLE_FAILURES[@]} -eq 0 ]]; then
    echo -e "${GREEN}✓ No waiverable failures detected${NC}"
    exit 0
fi

echo -e "${YELLOW}⚠ Waiverable failures detected${NC}"
echo ""
echo "The following failures may be waived:"
for failure in "${WAIVERABLE_FAILURES[@]}"; do
    echo "  - $failure"
done
echo ""

# Generate waiver suggestion
WAIVER_ID=$(./scripts/get-next-task-number.sh | sed 's/TASK/WAIVER/')
WHAT_WAIVES=""
WHY=""

case "$FAILURE_TYPE" in
    coverage)
        WHAT_WAIVES="Coverage target (gradual ratchet)"
        WHY="Temporary coverage reduction during refactoring/feature development"
        ;;
    performance)
        WHAT_WAIVES="Performance/bundle budget"
        WHY="Temporary budget exceedance with remediation plan"
        ;;
    warnings)
        WHAT_WAIVES="Warning budget (zero warnings)"
        WHY="Temporary warnings with fix timeline"
        ;;
    *)
        WHAT_WAIVES="Quality gate failure"
        WHY="Temporary exception with remediation plan"
        ;;
esac

echo -e "${BLUE}Suggested waiver:${NC}"
echo ""
echo "Waiver ID: $WAIVER_ID"
echo "What it waives: $WHAT_WAIVES"
echo "Why: $WHY"
echo ""
echo "To create this waiver, run:"
echo -e "${GREEN}./scripts/create-waiver.sh \"$WAIVER_ID\" \"$WHAT_WAIVES\" \"$WHY\"${NC}"
echo ""
echo "Or create manually with details:"
echo "  - Scope: [Describe what this waiver covers]"
echo "  - Remediation plan: [How will this be fixed? Timeline?]"
echo "  - Expiration: [Set expiration date]"
