#!/bin/bash
# Setup agent interaction logging infrastructure
# Creates .agent-logs/ directory structure

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LOGS_DIR="${REPO_ROOT}/.agent-logs"

echo "Setting up agent interaction logging..."

# Create directory structure
mkdir -p "${LOGS_DIR}/interactions"
mkdir -p "${LOGS_DIR}/metrics"
mkdir -p "${LOGS_DIR}/errors"

# Create README
cat > "${LOGS_DIR}/README.md" << 'EOF'
# Agent Interaction Logs

This directory contains logs of agent interactions with the repository.

## Structure

- `interactions/` - Individual interaction logs (JSONL format)
- `metrics/` - Aggregated metrics (JSON format)
- `errors/` - Error logs

## Log Format

Each interaction log entry is a JSON object:

```json
{
  "timestamp": "2026-01-23T10:30:00Z",
  "agent": "Auto",
  "action": "read_file",
  "file": "backend/modules/clients/models.py",
  "duration_ms": 45,
  "success": true,
  "context": {
    "task": "TASK-001",
    "folder": "backend/modules/clients"
  }
}
```

## Metrics

Metrics are aggregated daily and stored in `metrics/` directory.

## Privacy

Logs may contain file paths and action types but should not contain:
- Code content
- Secrets or credentials
- Personal information

EOF

echo "✅ Agent logging infrastructure created at ${LOGS_DIR}"
echo "📁 Directory structure:"
tree -L 2 "${LOGS_DIR}" || find "${LOGS_DIR}" -type d | head -10
