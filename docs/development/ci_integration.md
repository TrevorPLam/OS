# CI Integration Guide

**File**: `docs/development/ci_integration.md`

## Overview

This guide explains how to integrate governance verification into your CI pipeline.

## Current Status

✅ **Boundary checker** is integrated (`.github/workflows/ci.yml` line 101-104)
✅ **Governance verify** is integrated (`.github/workflows/ci.yml` Job 7)
✅ **HITL sync** runs automatically on PRs (via `sync-hitl-to-pr.py`)

## Adding Governance Verify to CI

### Option 1: Add as Separate Job (Recommended)

Add to `.github/workflows/ci.yml`:

```yaml
jobs:
  # ... existing jobs ...

  governance:
    name: Governance Verification
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run governance verification
        run: |
          chmod +x scripts/governance-verify.sh
          ./scripts/governance-verify.sh
```

### Option 2: Add to Existing CI Job

Add to the existing `ci` job in `.github/workflows/ci.yml`:

```yaml
      - name: Run governance verification
        run: |
          chmod +x scripts/governance-verify.sh
          ./scripts/governance-verify.sh || true  # Don't fail CI yet (soft integration)
```

### Option 3: Use Manifest Command

If `check:governance` is in your Makefile:

```yaml
      - name: Run governance verification
        run: make check:governance
```

## Exit Codes

The `governance-verify.sh` script uses these exit codes:
- `0` = All checks pass
- `1` = Hard gate failure (blocks merge)
- `2` = Waiverable failure (requires waiver)

## Hard Gates (Block Merge)

These failures block PR merge:
- Missing required policy files
- Manifest contains `<UNKNOWN>` placeholders
- Required HITL items not Completed
- Missing required artifacts for change type

## Waiverable Gates

These failures require waiver:
- Coverage targets (gradual ratchet)
- Performance/bundle budgets
- Warning budgets

## PR Comments (Future Enhancement)

To auto-comment on PRs with governance status, you could add:

```yaml
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const output = require('fs').readFileSync('governance-output.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Governance Verification\n\n' + output
            });
```

## Testing Locally

Before adding to CI, test locally:

```bash
# Make script executable
chmod +x scripts/governance-verify.sh

# Run verification
./scripts/governance-verify.sh

# Check exit code
echo $?  # Should be 0 for pass, 1 for hard fail, 2 for waiverable
```

## Related Files

- `scripts/governance-verify.sh` - Verification script
- `.repo/policy/QUALITY_GATES.md` - Quality gate definitions
- `.repo/repo.manifest.yaml` - Command definitions
