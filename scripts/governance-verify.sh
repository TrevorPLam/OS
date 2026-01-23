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

# Check 5: Trace log schema validation
log_info "Checking trace log schema..."
TRACE_SCHEMA=".repo/templates/AGENT_TRACE_SCHEMA.json"
if [[ -f "$TRACE_SCHEMA" ]]; then
    log_success "Trace log schema exists: $TRACE_SCHEMA"

    # Check if Python is available for JSON schema validation
    if command -v python3 &> /dev/null; then
        # Validate schema itself is valid JSON
        if python3 -m json.tool "$TRACE_SCHEMA" > /dev/null 2>&1; then
            log_success "Trace log schema is valid JSON"
        else
            log_error "Trace log schema is not valid JSON: $TRACE_SCHEMA"
        fi
    fi
else
    log_warning "Trace log schema not found: $TRACE_SCHEMA (optional, but recommended)"
fi

# Check 6: Trace log validation (if trace logs exist in current changes)
log_info "Checking for trace logs in recent changes..."
TRACE_DIR=".repo/traces"
if [[ -d "$TRACE_DIR" ]]; then
    log_success "Trace log directory exists: $TRACE_DIR"

    # Check for trace logs in git changes
    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        # Check for trace log files in staged/unstaged changes
        TRACE_LOGS=$(git diff --name-only --cached HEAD 2>/dev/null | grep -E "\.repo/traces/.*\.json$" || true)
        TRACE_LOGS="$TRACE_LOGS $(git diff --name-only HEAD 2>/dev/null | grep -E "\.repo/traces/.*\.json$" || true)"

        # Also check for trace logs in the directory
        if [[ -n "$(find "$TRACE_DIR" -name "*.json" 2>/dev/null)" ]]; then
            TRACE_LOGS="$TRACE_LOGS $(find "$TRACE_DIR" -name "*.json" -type f)"
        fi

        if [[ -n "$TRACE_LOGS" ]] && [[ -f "$TRACE_SCHEMA" ]] && command -v python3 &> /dev/null; then
            # Use validate-trace-log.sh if available, otherwise basic validation
            VALIDATOR="scripts/validate-trace-log.sh"
            for trace_file in $TRACE_LOGS; do
                if [[ -f "$trace_file" ]]; then
                    if [[ -f "$VALIDATOR" ]] && [[ -x "$VALIDATOR" ]]; then
                        if "$VALIDATOR" "$trace_file" > /dev/null 2>&1; then
                            log_success "Trace log validated: $trace_file"
                        else
                            log_warning "Trace log validation failed: $trace_file (run: $VALIDATOR $trace_file)"
                        fi
                    else
                        # Basic validation fallback
                        if python3 -m json.tool "$trace_file" > /dev/null 2>&1; then
                            # Check for required fields
                            if grep -q '"intent"' "$trace_file" && \
                               grep -q '"files"' "$trace_file" && \
                               grep -q '"commands"' "$trace_file" && \
                               grep -q '"evidence"' "$trace_file" && \
                               grep -q '"hitl"' "$trace_file" && \
                               grep -q '"unknowns"' "$trace_file"; then
                                log_success "Trace log is valid: $trace_file"
                            else
                                log_warning "Trace log missing required fields: $trace_file"
                            fi
                        else
                            log_warning "Trace log is not valid JSON: $trace_file"
                        fi
                    fi
                fi
            done
        fi
    fi
else
    log_warning "Trace log directory not found: $TRACE_DIR (create with: mkdir -p $TRACE_DIR)"
fi

# Check 7: HITL items detailed parsing
log_info "Parsing HITL items status..."
if [[ -f ".repo/policy/HITL.md" ]]; then
    # Extract active HITL items from the table
    # Look for table rows with Status that's not "Completed" or "Superseded"
    BLOCKING_HITL=$(grep -E "^\|.*\|.*\|.*\|.*\|" ".repo/policy/HITL.md" | \
        grep -v "^\|.*ID\|" | \
        grep -v "^\|.*---\|" | \
        awk -F'|' '{print $2, $4}' | \
        grep -vE "Completed|Superseded" | \
        awk '{print $1}' | \
        tr -d ' ' || true)

    if [[ -n "$BLOCKING_HITL" ]]; then
        log_warning "Active HITL items found (not Completed): $BLOCKING_HITL"
        log_warning "  → Check .repo/policy/HITL.md for details"
        log_warning "  → PR merge may be blocked until HITL items are Completed"
    else
        log_success "No blocking HITL items found"
    fi

    # Check for HITL item files
    HITL_ITEM_COUNT=$(find .repo/hitl -name "HITL-*.md" 2>/dev/null | wc -l || echo "0")
    if [[ "$HITL_ITEM_COUNT" -gt 0 ]]; then
        log_info "Found $HITL_ITEM_COUNT HITL item file(s) in .repo/hitl/"
    fi
fi

# Check 8: Required artifacts for change types (basic check)
log_info "Checking for required artifacts..."
# This is a simplified check - in practice, you'd parse PR description or git commit messages
# to determine change type and check for corresponding artifacts
if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    # Check if there are any ADR triggers in changed files
    CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | head -20 || true)
    if echo "$CHANGED_FILES" | grep -qE "(api/|modules/)" && \
       ! find docs/adr -name "ADR-*.md" -newer "$(git merge-base HEAD origin/main 2>/dev/null || echo "HEAD~10")" 2>/dev/null | grep -q .; then
        log_warning "API/module changes detected but no recent ADR found (cross-feature imports may require ADR per Principle 23)"
    fi
fi

# Check 9: Boundary checker configuration
log_info "Checking boundary checker configuration..."
if [[ -f ".importlinter" ]]; then
    log_success "Import linter config exists: .importlinter"
    if command -v lint-imports &> /dev/null || command -v import-linter &> /dev/null; then
        log_success "Boundary checker tool available"
    else
        log_warning "Boundary checker tool not found (install: pip install import-linter)"
    fi
else
    log_warning "Import linter config not found: .importlinter (boundary checking may not work)"
fi

# Check 10: Governance-verify script itself is executable
if [[ ! -x "scripts/governance-verify.sh" ]]; then
    log_warning "governance-verify.sh is not executable (chmod +x scripts/governance-verify.sh)"
fi

# Check 11: Trace log directory exists
log_info "Checking trace log directory..."
if [[ -d ".repo/traces" ]]; then
    log_success "Trace log directory exists: .repo/traces"
else
    log_warning "Trace log directory missing: .repo/traces (create with: mkdir -p .repo/traces)"
fi

# Check 12: Validate task format (if task files exist)
log_info "Checking task format..."
TASK_VALIDATOR="scripts/validate-task-format.sh"
if [[ -f "$TASK_VALIDATOR" ]] && [[ -x "$TASK_VALIDATOR" ]]; then
    for task_file in ".repo/tasks/TODO.md" ".repo/tasks/BACKLOG.md"; do
        if [[ -f "$task_file" ]]; then
            if "$TASK_VALIDATOR" "$task_file" > /dev/null 2>&1; then
                log_success "Task format valid: $task_file"
            else
                log_warning "Task format issues in: $task_file (run: $TASK_VALIDATOR $task_file)"
            fi
        fi
    done
fi

# Check 13: ADR trigger detection
log_info "Checking for ADR triggers..."
ADR_DETECTOR="scripts/detect-adr-triggers.sh"
if [[ -f "$ADR_DETECTOR" ]] && [[ -x "$ADR_DETECTOR" ]] && command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
    if "$ADR_DETECTOR" > /dev/null 2>&1; then
        log_success "No ADR triggers detected"
    else
        log_warning "ADR may be required (run: $ADR_DETECTOR for details)"
    fi
fi

# Check 14: Expired waivers
log_info "Checking for expired waivers..."
WAIVER_CHECKER="scripts/check-expired-waivers.sh"
if [[ -f "$WAIVER_CHECKER" ]] && [[ -x "$WAIVER_CHECKER" ]]; then
    if "$WAIVER_CHECKER" > /dev/null 2>&1; then
        log_success "No expired waivers found"
    else
        log_warning "Expired waivers detected (run: $WAIVER_CHECKER for details)"
    fi
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
