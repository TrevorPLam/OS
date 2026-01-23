# Framework Changelog

**File**: `.repo/CHANGELOG.md`

This file tracks improvements and changes to the governance framework.

## 2026-01-23 - World-Class Documentation Structure

### Added

- **Comprehensive documentation structure** in root `docs/` directory:
  - `getting-started/` - Quick start guides and onboarding
  - `guides/` - User, admin, and API guides
  - `architecture/` - System architecture, modules, ADRs, data models
  - `development/` - Development workflow, contributing, testing, standards
  - `operations/` - Operations, monitoring, troubleshooting, runbooks, disaster recovery
  - `reference/` - API reference, module reference, configuration, CLI
  - `security/` - Security, compliance, data privacy
  - `integrations/` - Integration documentation, webhooks, API integrations
  - `archive/` - Historical documentation (analysis and redundant docs)

### Reorganized

- **Moved `.repo/docs/` to root `docs/`** - Documentation now in standard location
- **Organized existing docs** - Moved to appropriate sections:
  - `ONBOARDING.md` → `getting-started/onboarding.md`
  - `ARCHITECTURE.md` → `architecture/README.md`
  - `DEVELOPMENT.md` → `development/README.md`
  - `RUNBOOK.md` → `operations/README.md`
  - `DOCS.md` → `guides/README.md`
- **Created structure** - Anticipated future needs based on application (multi-tenant, many modules, integrations, etc.)

### Updated

- **All documentation references** - Updated throughout codebase
- **INDEX.md** - Updated to reference new docs structure
- **README.md** - Updated documentation links
- **`.repo/INDEX.md`** - Removed docs section (now in root)
- **`.repo/DOCUMENT_MAP.md`** - Updated architecture reference

---

## 2026-01-23 - Directory Reorganization & Entry Point Optimization

### Reorganized

- **Moved `agents/tasks/` to `.repo/tasks/`** - Task management now centralized in `.repo/`
- **Updated all references** - All file paths updated throughout codebase:
  - Entry points (`AGENTS.json`, `AGENTS.md`)
  - Agent framework files (`.repo/agents/rules.json`, `QUICK_REFERENCE.md`)
  - Scripts (`archive-task.py`, `promote-task.sh`, `generate-metrics.sh`, etc.)
  - Documentation (`INDEX.md`, `DOCUMENT_MAP.md`, `README.md`)

### Archived

- **Moved 14 documents to `docs/archive/`** for historical reference:
  - 12 analysis/assessment documents from design phase (all issues resolved)
  - 2 redundant documentation files (superseded by new entry point system)
  - See `docs/archive/README.md` for details

### Added

- **`AGENTS.json`** - Structured JSON entry point for better model parsing
- **Optimized `AGENTS.md`** - Streamlined to imperative, action-oriented style
- **`docs/archive/`** - Archive directory for historical documentation

### Updated

- **`AGENTS.md`** - Optimized text style for model interaction (imperative, direct commands)
- **`PROMPT.md`** - Updated to reference JSON as primary format
- **`DOCUMENT_MAP.md`** - Removed references to archived assessment documents
- **`.repo/tasks/TODO.md`** - Updated to reference `AGENTS.json` first
- **`.repo/agents/QUICK_REFERENCE.md`** - Updated to reference JSON entry point

### Improved

- **Entry Point System** - Now uses JSON for structured parsing, markdown for human readability
- **Text Style** - All entry point documents optimized for model interaction
- **Documentation Structure** - Cleaner, more focused operational docs

---

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
  - `docs/development/boundary_checker.md` - Boundary checker documentation
  - `docs/development/ci_integration.md` - CI integration guide
  - `docs/development/automation_scripts.md` - Automation scripts documentation

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
- CI integration documented (see `docs/development/ci_integration.md`)
- Automation scripts are functional but may need GitHub API integration for full automation
