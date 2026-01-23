#!/bin/bash
# validate-pr-body.sh
# Validates PR body contains required sections per governance framework
#
# Usage: ./scripts/validate-pr-body.sh [pr-body-file] OR reads from stdin
#   pr-body-file: Path to file containing PR body text

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Read PR body from file or stdin
if [[ $# -ge 1 ]] && [[ -f "$1" ]]; then
    PR_BODY=$(cat "$1")
else
    PR_BODY=$(cat)
fi

ERRORS=0
WARNINGS=0

# Required sections per Principle 17: PR Narration
REQUIRED_SECTIONS=(
    "what"
    "why"
    "filepaths"
    "verification"
    "risks"
    "rollback"
)

echo "Validating PR body format..."

# Check for required sections (case-insensitive, flexible matching)
for section in "${REQUIRED_SECTIONS[@]}"; do
    if echo "$PR_BODY" | grep -qiE "(^|\n|##?)\s*${section}|${section}\s*:"; then
        echo -e "${GREEN}✓ Found: $section${NC}"
    else
        echo -e "${RED}✗ Missing: $section${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check for filepaths (Principle: global rule - filepaths required everywhere)
if echo "$PR_BODY" | grep -qE "(filepath|file path|files?:\s*|modified files?|changed files?)" -i; then
    echo -e "${GREEN}✓ Filepaths mentioned${NC}"
else
    echo -e "${YELLOW}⚠ Filepaths not clearly mentioned (required per global rule)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for HITL references if security-related keywords present
SECURITY_KEYWORDS=("security" "auth" "login" "payment" "money" "credential" "secret" "token" "key")
HAS_SECURITY=$(echo "$PR_BODY" | grep -qiE "$(IFS='|'; echo "${SECURITY_KEYWORDS[*]}")" && echo "yes" || echo "no")

if [[ "$HAS_SECURITY" == "yes" ]]; then
    if echo "$PR_BODY" | grep -qiE "(HITL|hitl|human.*loop|human.*required)"; then
        echo -e "${GREEN}✓ Security-related change mentions HITL${NC}"
    else
        echo -e "${YELLOW}⚠ Security-related change detected but HITL not mentioned (may require HITL per SECURITY_BASELINE.md)${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check for task reference (Article 5: Strict Traceability)
if echo "$PR_BODY" | grep -qiE "(TASK-|task|backlog|todo)"; then
    echo -e "${GREEN}✓ Task reference found${NC}"
else
    echo -e "${YELLOW}⚠ No task reference found (required per Article 5: Strict Traceability)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}✗ PR body validation FAILED with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Required sections:"
    for section in "${REQUIRED_SECTIONS[@]}"; do
        echo "  - $section"
    done
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠ PR body validation passed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${GREEN}✓ PR body validation PASSED${NC}"
    exit 0
fi
