#!/bin/bash
# detect-adr-triggers.sh
# Detects if ADR is required based on code changes
#
# Usage: ./scripts/detect-adr-triggers.sh [base-branch]
#   base-branch: Base branch to compare against (default: main)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_BRANCH="${1:-main}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error:${NC} git is required for ADR trigger detection"
    exit 1
fi

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning:${NC} Not in a git repository"
    exit 0
fi

# Get changed files
CHANGED_FILES=$(git diff --name-only "$BASE_BRANCH" HEAD 2>/dev/null || \
    git diff --name-only HEAD 2>/dev/null || echo "")

if [[ -z "$CHANGED_FILES" ]]; then
    echo "No changed files detected"
    exit 0
fi

ADR_REQUIRED=false
REASONS=()

# Check for cross-feature imports (ADR trigger per BOUNDARIES.md)
echo "Checking for cross-feature imports..."

# Python files: check for imports across module boundaries
PYTHON_FILES=$(echo "$CHANGED_FILES" | grep -E "\.py$" || true)
if [[ -n "$PYTHON_FILES" ]]; then
    for file in $PYTHON_FILES; do
        # Skip if file doesn't exist (deleted)
        [[ ! -f "$file" ]] && continue

        # Check for imports from other modules
        # Pattern: from modules.X import or import modules.X
        IMPORTS=$(grep -E "^(from|import)\s+modules\." "$file" 2>/dev/null || true)

        if [[ -n "$IMPORTS" ]]; then
            # Extract module names
            MODULE_FROM=$(echo "$file" | sed -n 's|.*modules/\([^/]*\)/.*|\1|p')

            while IFS= read -r import_line; do
                MODULE_TO=$(echo "$import_line" | sed -n 's|.*modules\.\([^./]*\)\..*|\1|p')

                if [[ -n "$MODULE_FROM" ]] && [[ -n "$MODULE_TO" ]] && [[ "$MODULE_FROM" != "$MODULE_TO" ]]; then
                    ADR_REQUIRED=true
                    REASONS+=("Cross-module import: $file imports from modules.$MODULE_TO (current module: $MODULE_FROM)")
                fi
            done <<< "$IMPORTS"
        fi
    done
fi

# Check for API contract changes (may require ADR)
API_FILES=$(echo "$CHANGED_FILES" | grep -E "(api/|serializers\.py|views\.py)" || true)
if [[ -n "$API_FILES" ]]; then
    # Check if OpenAPI schema was updated
    if ! echo "$CHANGED_FILES" | grep -q "openapi.yaml"; then
        REASONS+=("API changes detected but openapi.yaml not updated (may require ADR)")
    fi
fi

# Check for schema/migration changes (may require ADR)
MIGRATION_FILES=$(echo "$CHANGED_FILES" | grep -E "migrations/.*\.py$" || true)
if [[ -n "$MIGRATION_FILES" ]]; then
    # Schema changes often require ADR
    REASONS+=("Database schema changes detected (migrations) - may require ADR")
fi

# Summary
echo ""
if [[ "$ADR_REQUIRED" == true ]] || [[ ${#REASONS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠ ADR may be required${NC}"
    echo ""
    echo "Reasons:"
    for reason in "${REASONS[@]}"; do
        echo "  - $reason"
    done
    echo ""
    echo "Per Principle 23 (ADR Required When Triggered) and BOUNDARIES.md:"
    echo "  - Cross-feature imports require ADR"
    echo "  - Large exceptions to boundaries require ADR"
    echo ""
    echo "Check if ADR is needed and create one if required:"
    echo "  - Template: .repo/templates/ADR_TEMPLATE.md"
    echo "  - Location: docs/adr/"
    exit 1
else
    echo -e "${GREEN}✓ No ADR triggers detected${NC}"
    exit 0
fi
