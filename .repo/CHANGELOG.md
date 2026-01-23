# Framework Changelog

**File**: `.repo/CHANGELOG.md`

This file tracks improvements and changes to the governance framework.

## 2026-01-23 - Framework Enhancements (Part 2)

### Added

- **CI Integration**
  - Governance verification job added to `.github/workflows/ci.yml` (Job 7)
  - HITL sync runs automatically on PRs via GitHub API
  - Fixed duplicate CI workflow definitions

- **Makefile Integration**
  - Added `check-governance` target: `make check-governance`
  - Runs governance verification locally

- **Pre-commit Hooks**
  - Added governance verification hook (runs on `.repo/`, `agents/`, `scripts/` changes)
  - Non-blocking (uses `|| true` to avoid blocking commits)

- **GitHub API Integration**
  - `sync-hitl-to-pr.py` now updates PRs directly via GitHub API
  - Automatic token detection from environment
  - Fallback to manual method if API unavailable

- **Dependencies**
  - `scripts/requirements.txt` - Python dependencies for automation scripts

### Updated

- `.github/workflows/ci.yml` - Added governance job, fixed duplicates
- `Makefile` - Added `check-governance` target
- `.pre-commit-config.yaml` - Added governance verification hook
- `scripts/sync-hitl-to-pr.py` - Added GitHub API integration
- Documentation updated to reflect new integrations

---

## 2026-01-23 - Framework Enhancements (Part 1)

### Added

- **Example Files** (`.repo/templates/examples/`)
  - `example_trace_log.json` - Example trace log format
  - `example_hitl_item.md` - Example HITL item
  - `example_waiver.md` - Example waiver
  - `example_task_packet.json` - Example task packet
  - `README.md` - Examples documentation

- **Quick Reference** (`.repo/agents/QUICK_REFERENCE.md`)
  - One-page cheat sheet for agents
  - Decision tree for HITL requirements
  - Common commands and workflows
  - Artifact requirements table

- **Documentation**
  - `.repo/docs/boundary_checker.md` - Boundary checker documentation
  - `.repo/docs/ci_integration.md` - CI integration guide
  - `.repo/docs/automation_scripts.md` - Automation scripts documentation

- **Automation Scripts**
  - `scripts/sync-hitl-to-pr.py` - Sync HITL status to PRs
  - `scripts/archive-task.py` - Archive completed tasks

### Enhanced

- **Governance Verify Script** (`scripts/governance-verify.sh`)
  - Added trace log validation (JSON schema check)
  - Enhanced HITL item parsing (detailed status checking)
  - Added artifact checking (ADR detection)
  - Added boundary checker verification
  - Better error reporting and categorization

### Updated

- `.repo/agents/AGENTS.md` - Added references to quick reference and examples
- `.repo/GOVERNANCE.md` - Updated directory structure to reflect new files

### Notes

- Boundary checker confirmed working (import-linter, configured in `.importlinter`)
- CI integration documented but not yet implemented (see `.repo/docs/ci_integration.md`)
- Automation scripts are functional but may need GitHub API integration for full automation
