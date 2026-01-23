#!/bin/bash
# generate-metrics.sh
# Generates metrics report for governance framework
#
# Usage: ./scripts/generate-metrics.sh [output-format]
#   output-format: json, markdown, or text (default: markdown)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

OUTPUT_FORMAT="${1:-markdown}"

# Gather metrics
TODAY=$(date +%Y-%m-%d)

# Task metrics
TODO_COUNT=$(grep -c "^### \[TASK-" ".repo/tasks/TODO.md" 2>/dev/null || echo "0")
BACKLOG_COUNT=$(grep -c "^### \[TASK-" ".repo/tasks/BACKLOG.md" 2>/dev/null || echo "0")
ARCHIVE_COUNT=$(grep -c "^### \[TASK-" ".repo/tasks/ARCHIVE.md" 2>/dev/null || echo "0")

# Count by priority
P0_BACKLOG=$(grep -A 5 "^### \[TASK-" ".repo/tasks/BACKLOG.md" 2>/dev/null | grep -c "P0" || echo "0")
P1_BACKLOG=$(grep -A 5 "^### \[TASK-" ".repo/tasks/BACKLOG.md" 2>/dev/null | grep -c "P1" || echo "0")
P2_BACKLOG=$(grep -A 5 "^### \[TASK-" ".repo/tasks/BACKLOG.md" 2>/dev/null | grep -c "P2" || echo "0")
P3_BACKLOG=$(grep -A 5 "^### \[TASK-" ".repo/tasks/BACKLOG.md" 2>/dev/null | grep -c "P3" || echo "0")

# HITL metrics
HITL_ACTIVE=$(grep -c "^|HITL-" ".repo/policy/HITL.md" 2>/dev/null || echo "0")
HITL_PENDING=$(grep "|.*Pending" ".repo/policy/HITL.md" 2>/dev/null | grep -c "Pending" || echo "0")
HITL_COMPLETED=$(grep "|.*Completed" ".repo/policy/HITL.md" 2>/dev/null | grep -c "Completed" || echo "0")
HITL_TOTAL=$(find ".repo/hitl" -name "HITL-*.md" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Waiver metrics
if [[ -f ".repo/policy/WAIVERS.md" ]]; then
    WAIVER_ACTIVE=$(grep -c "^|WAIVER-" ".repo/policy/WAIVERS.md" 2>/dev/null || echo "0")
    WAIVER_EXPIRED=0
    if [[ -f "scripts/check-expired-waivers.sh" ]]; then
        WAIVER_EXPIRED=$(./scripts/check-expired-waivers.sh 2>&1 | grep -c "EXPIRED" || echo "0")
    fi
else
    WAIVER_ACTIVE=0
    WAIVER_EXPIRED=0
fi

# Trace log metrics
TRACE_COUNT=$(find ".repo/traces" -name "*.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Agent log metrics
LOG_COUNT=$(find ".repo/logs" -name "*.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# ADR metrics
ADR_COUNT=$(find "docs/adr" -name "ADR-*.md" 2>/dev/null | wc -l | tr -d ' ' || echo "0")

# Generate output
case "$OUTPUT_FORMAT" in
    json)
        cat <<EOF
{
  "date": "$TODAY",
  "tasks": {
    "todo": $TODO_COUNT,
    "backlog": $BACKLOG_COUNT,
    "archive": $ARCHIVE_COUNT,
    "by_priority": {
      "p0": $P0_BACKLOG,
      "p1": $P1_BACKLOG,
      "p2": $P2_BACKLOG,
      "p3": $P3_BACKLOG
    }
  },
  "hitl": {
    "active": $HITL_ACTIVE,
    "pending": $HITL_PENDING,
    "completed": $HITL_COMPLETED,
    "total": $HITL_TOTAL
  },
  "waivers": {
    "active": $WAIVER_ACTIVE,
    "expired": $WAIVER_EXPIRED
  },
  "artifacts": {
    "trace_logs": $TRACE_COUNT,
    "agent_logs": $LOG_COUNT,
    "adrs": $ADR_COUNT
  }
}
EOF
        ;;
    markdown)
        cat <<EOF
# Governance Framework Metrics

**Generated:** $TODAY

## Tasks

| Metric | Count |
|--------|-------|
| Active (TODO) | $TODO_COUNT |
| Backlog | $BACKLOG_COUNT |
| Archived | $ARCHIVE_COUNT |
| **Total** | **$((TODO_COUNT + BACKLOG_COUNT + ARCHIVE_COUNT))** |

### Backlog by Priority

| Priority | Count |
|----------|-------|
| P0 (Critical) | $P0_BACKLOG |
| P1 (High) | $P1_BACKLOG |
| P2 (Medium) | $P2_BACKLOG |
| P3 (Low) | $P3_BACKLOG |

## HITL Items

| Metric | Count |
|--------|-------|
| Active | $HITL_ACTIVE |
| Pending | $HITL_PENDING |
| Completed | $HITL_COMPLETED |
| Total Files | $HITL_TOTAL |

## Waivers

| Metric | Count |
|--------|-------|
| Active | $WAIVER_ACTIVE |
| Expired | $WAIVER_EXPIRED |

## Artifacts

| Type | Count |
|------|-------|
| Trace Logs | $TRACE_COUNT |
| Agent Logs | $LOG_COUNT |
| ADRs | $ADR_COUNT |

---
*Run \`./scripts/generate-metrics.sh\` to regenerate this report*
EOF
        ;;
    text)
        cat <<EOF
Governance Framework Metrics
Generated: $TODAY

TASKS:
  Active (TODO): $TODO_COUNT
  Backlog: $BACKLOG_COUNT
  Archived: $ARCHIVE_COUNT
  Total: $((TODO_COUNT + BACKLOG_COUNT + ARCHIVE_COUNT))

  Backlog by Priority:
    P0 (Critical): $P0_BACKLOG
    P1 (High): $P1_BACKLOG
    P2 (Medium): $P2_BACKLOG
    P3 (Low): $P3_BACKLOG

HITL ITEMS:
  Active: $HITL_ACTIVE
  Pending: $HITL_PENDING
  Completed: $HITL_COMPLETED
  Total Files: $HITL_TOTAL

WAIVERS:
  Active: $WAIVER_ACTIVE
  Expired: $WAIVER_EXPIRED

ARTIFACTS:
  Trace Logs: $TRACE_COUNT
  Agent Logs: $LOG_COUNT
  ADRs: $ADR_COUNT
EOF
        ;;
    *)
        echo "Unknown output format: $OUTPUT_FORMAT"
        echo "Supported formats: json, markdown, text"
        exit 1
        ;;
esac
