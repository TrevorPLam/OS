# Automation Scripts

**File**: `.repo/automation/README.md`

This directory contains automation scripts for governance verification and validation.

## Script Naming Convention

### Canonical Scripts (Used in CI/Manifest)

- **`scripts/governance-verify.sh`** - Canonical governance verification script (used in CI)
  - Referenced in `.repo/repo.manifest.yaml` as `check:governance`
  - Used in `.github/workflows/ci.yml` governance job
  - Exit codes: 0=pass, 1=hard failure, 2=waiverable failure

### Alternative Implementations

- **`.repo/automation/scripts/governance-verify.js`** - Node.js version (alternative)
  - Same functionality as bash version
  - Can be used if Node.js is preferred
  - Not currently used in CI (bash version is canonical)

### Validation Scripts

- **`scripts/validate-trace-log.sh`** - Validates trace logs (bash)
- **`.repo/automation/scripts/validate-agent-trace.js`** - Validates trace logs (Node.js)
  - Both validate against `.repo/templates/AGENT_TRACE_SCHEMA.json`
  - Use either one based on preference

## Directory Structure

```
.repo/automation/
├── README.md                    # This file
├── scripts/
│   ├── agent-logger.js          # Agent interaction logging SDK
│   ├── governance-verify.js     # Node.js governance verification
│   ├── validate-agent-context.js # Context file validation (with JSON schema)
│   ├── validate-agent-trace.js  # Node.js trace log validation
│   └── package.json              # Node.js dependencies (ajv for schema validation)
└── ci/
    └── governance-verify.yml    # CI template (not used, CI uses .github/workflows/ci.yml)
```

## Usage

### Governance Verification

```bash
# Canonical (bash) - used in CI
./scripts/governance-verify.sh

# Alternative (Node.js)
node .repo/automation/scripts/governance-verify.js
```

### Trace Log Validation

```bash
# Bash version
./scripts/validate-trace-log.sh .repo/traces/TASK-001-trace-20260123-120000.json

# Node.js version
node .repo/automation/scripts/validate-agent-trace.js .repo/traces/TASK-001-trace-20260123-120000.json
```

## Setup

### Node.js Dependencies

For scripts that use JSON schema validation (e.g., `validate-agent-context.js`), install dependencies:

```bash
cd .repo/automation/scripts
npm install
```

This installs `ajv` for JSON schema validation. If `ajv` is not installed, validation falls back to basic checks.

## Agent Interaction Logging

The `agent-logger.js` module provides logging SDK for agent interactions:

```javascript
const logger = require('.repo/automation/scripts/agent-logger.js');

// Log an interaction
logger.logInteraction({
  agent: 'Auto',
  action: 'read_file',
  file: 'backend/models.py',
  duration_ms: 45,
  success: true,
  context: { task: 'TASK-001' }
});

// Log an error
logger.logError({
  agent: 'Auto',
  action: 'read_file',
  error: 'File not found',
  context: { file: 'missing.txt' }
});

// Generate daily metrics
logger.writeMetrics(); // Generates metrics for today
logger.writeMetrics('2026-01-23'); // Generate for specific date

// Cleanup old logs (keep last 30 days)
logger.cleanupOldLogs(30);
```

Logs are written to:
- `.agent-logs/interactions/` - Individual interaction logs (JSONL)
- `.agent-logs/errors/` - Error logs (JSONL)
- `.agent-logs/metrics/` - Daily aggregated metrics (JSON)

## Context File Validation

The `validate-agent-context.js` script validates `.agent-context.json` files:

```bash
# Basic validation (schema + required fields)
node .repo/automation/scripts/validate-agent-context.js path/to/.agent-context.json

# With file path checking
node .repo/automation/scripts/validate-agent-context.js path/to/.agent-context.json --check-files

# With boundary validation
node .repo/automation/scripts/validate-agent-context.js path/to/.agent-context.json --check-boundaries

# With link validation
node .repo/automation/scripts/validate-agent-context.js path/to/.agent-context.json --check-links

# All checks
node .repo/automation/scripts/validate-agent-context.js path/to/.agent-context.json --check-files --check-boundaries --check-links
```

## Additional Scripts

### Context File Management

**Check for stale context files:**
```bash
node .repo/automation/scripts/check-stale-context.js [--threshold-days=30] [--warn-only]
```

**Update last_verified dates:**
```bash
# Update specific files
node .repo/automation/scripts/update-context-verified.js path/to/.agent-context.json

# Update all context files
node .repo/automation/scripts/update-context-verified.js --all
```

### Pattern Verification

**Check pattern files:**
```bash
node .repo/automation/scripts/pattern-verification.js [--warn-only]
```

Verifies that pattern files exist, are referenced in `.AGENT.md` files, and have corresponding entries in `.agent-context.json`.

### Boundary Checking

**Check module boundaries:**
```bash
node .repo/automation/scripts/check-boundaries.js [--fail-on-violations]
```

Wraps `lint-imports` for easier use. Can be integrated into CI or run manually.

## Troubleshooting

For help with script failures and recovery procedures, see `.repo/docs/TROUBLESHOOTING.md`.

## Notes

- Bash scripts are the canonical implementation (used in CI)
- Node.js scripts are provided as alternatives
- Both implementations should produce equivalent results
- If you add new scripts, prefer bash for consistency with existing scripts
- Logging SDK is Node.js only (no bash equivalent needed)
- All scripts include error handling and graceful degradation
