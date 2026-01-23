#!/bin/bash
# governance-verify.sh
# Enforces quality gates per .repo/policy/QUALITY_GATES.md
#
# Exit codes:
#   0 = pass (all checks pass)
#   1 = fail (hard gate failure - blocks merge)
#   2 = waiverable failure (requires waiver)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0
WARNINGS=0
HARD_FAILURES=()

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

log_error() {
    echo -e "${RED}❌ ERROR:${NC} $1" >&2
    ERRORS=$((ERRORS + 1))
    HARD_FAILURES+=("$1")
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1" >&2
    WARNINGS=$((WARNINGS + 1))
}

log_info() {
    echo -e "${GREEN}ℹ️  INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

# Check 1: Required policy files exist
log_info "Checking required policy files..."
REQUIRED_POLICY_FILES=(
    ".repo/policy/CONSTITUTION.md"
    ".repo/policy/PRINCIPLES.md"
    ".repo/policy/QUALITY_GATES.md"
    ".repo/policy/SECURITY_BASELINE.md"
    ".repo/policy/HITL.md"
    ".repo/policy/BOUNDARIES.md"
)

for file in "${REQUIRED_POLICY_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        log_error "Required policy file missing: $file"
    else
        log_success "Policy file exists: $file"
    fi
done

# Check 2: Manifest exists
log_info "Checking repository manifest..."
if [[ ! -f ".repo/repo.manifest.yaml" ]]; then
    log_error "Repository manifest missing: .repo/repo.manifest.yaml"
else
    log_success "Manifest exists: .repo/repo.manifest.yaml"
    # Check for UNKNOWN placeholders (hard failure)
    if grep -q "<UNKNOWN>" ".repo/repo.manifest.yaml"; then
        log_error "Manifest contains <UNKNOWN> placeholders (must be resolved via HITL)"
    fi
fi

# Check 3: HITL items status (if HITL.md exists)
log_info "Checking HITL items status..."
if [[ -f ".repo/policy/HITL.md" ]]; then
    # Check if there are any active HITL items that are not Completed
    # This is a simplified check - in practice, you'd parse the HITL.md table
    # For now, we just verify the file exists and is readable
    if grep -q "|.*Pending\|.*In Progress\|.*Blocked" ".repo/policy/HITL.md" 2>/dev/null; then
        log_warning "Active HITL items found that are not Completed (check .repo/policy/HITL.md)"
    else
        log_success "No blocking HITL items found"
    fi
else
    log_warning "HITL index file not found: .repo/policy/HITL.md"
fi

# Check 4: Repository structure compliance
log_info "Checking repository structure..."
REQUIRED_DIRS=(
    ".repo"
    ".repo/policy"
    ".repo/hitl"
    "backend"
    "frontend"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ ! -d "$dir" ]]; then
        log_error "Required directory missing: $dir"
    else
        log_success "Directory exists: $dir"
    fi
done

# Check 5: Trace log schema (if it exists)
log_info "Checking trace log schema..."
TRACE_SCHEMA=".repo/templates/AGENT_TRACE_SCHEMA.json"
if [[ -f "$TRACE_SCHEMA" ]]; then
    log_success "Trace log schema exists: $TRACE_SCHEMA"
    # In a full implementation, we'd validate trace logs against this schema
    # For now, we just check it exists
else
    log_warning "Trace log schema not found: $TRACE_SCHEMA (optional, but recommended)"
fi

# Check 6: Governance-verify script itself is executable
if [[ ! -x "scripts/governance-verify.sh" ]]; then
    log_warning "governance-verify.sh is not executable (chmod +x scripts/governance-verify.sh)"
fi

# Summary
echo ""
echo "=========================================="
echo "Governance Verification Summary"
echo "=========================================="
echo "Errors (hard failures): $ERRORS"
echo "Warnings (waiverable): $WARNINGS"
echo ""

if [[ $ERRORS -gt 0 ]]; then
    echo "Hard failures (blocks merge):"
    for failure in "${HARD_FAILURES[@]}"; do
        echo "  - $failure"
    done
    echo ""
    echo "❌ Governance verification FAILED (hard gate)"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo "⚠️  Governance verification passed with warnings (may require waiver)"
    exit 2
else
    echo "✅ Governance verification PASSED"
    exit 0
fi
