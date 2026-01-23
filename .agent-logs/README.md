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
