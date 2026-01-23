# Automation Scripts Documentation

**File**: `.repo/docs/automation_scripts.md`

## Overview

Helper scripts to automate common governance tasks.

## Available Scripts

### 1. `scripts/sync-hitl-to-pr.py`

Syncs HITL items status to PR description.

**Usage:**
```bash
python scripts/sync-hitl-to-pr.py [PR_NUMBER]
```

**What it does:**
- Reads active HITL items from `.repo/policy/HITL.md`
- Generates HITL section for PR description
- Outputs markdown that can be added to PR

**Example:**
```bash
# Generate HITL section
python scripts/sync-hitl-to-pr.py

# Update PR via GitHub CLI (if installed)
python scripts/sync-hitl-to-pr.py 123 | gh pr edit 123 --body-file -
```

**Future enhancement:** Could integrate with GitHub API to auto-update PRs.

### 2. `scripts/archive-task.py`

Archives completed task and promotes next from backlog.

**Usage:**
```bash
python scripts/archive-task.py [--force]
```

**What it does:**
1. Checks if current task in `TODO.md` is complete (all criteria `[x]`)
2. Moves task to `ARCHIVE.md` (prepends)
3. Promotes highest priority task from `BACKLOG.md` to `TODO.md`
4. Updates task status to "In Progress"

**Options:**
- `--force`: Archive even if not all criteria complete

**Example:**
```bash
# Archive completed task
python scripts/archive-task.py

# Force archive (if criteria not all marked)
python scripts/archive-task.py --force
```

## Integration with CI

These scripts can be integrated into CI workflows:

### GitHub Actions Integration

Already integrated in `.github/workflows/ci.yml`:

```yaml
- name: Install Python dependencies for scripts
  run: |
    pip install requests || echo "requests not available, will use fallback method"

- name: Sync HITL to PR
  if: github.event_name == 'pull_request'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    GITHUB_REPOSITORY: ${{ github.repository }}
  run: |
    python3 scripts/sync-hitl-to-pr.py ${{ github.event.pull_request.number }} || true
  continue-on-error: true
```

The script automatically updates PR descriptions with HITL status via GitHub API.

### Pre-commit Hook Example

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: sync-hitl
      name: Sync HITL to PR
      entry: python scripts/sync-hitl-to-pr.py
      language: system
      pass_filenames: false
```

## Requirements

- Python 3.11+
- For GitHub API integration: `requests` library (`pip install -r scripts/requirements.txt`)
- For GitHub CLI integration: `gh` CLI (optional, for manual updates)
- GitHub API token: Set `GITHUB_TOKEN` environment variable (auto-provided in CI)

## Future Enhancements

1. **Auto-update PRs**: Direct GitHub API integration
2. **Task validation**: Check task format before archiving
3. **Statistics**: Update ARCHIVE.md statistics automatically
4. **Notifications**: Notify on HITL status changes

## Related Files

- `scripts/governance-verify.sh` - Governance verification
- `.repo/policy/HITL.md` - HITL index
- `agents/tasks/TODO.md` - Current task
- `agents/tasks/BACKLOG.md` - Task queue
