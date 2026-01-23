# Boundary Checker Documentation

**File**: `.repo/docs/boundary_checker.md`

## Overview

This repository uses **import-linter** (via `lint-imports` command) to enforce architectural boundaries defined in `.importlinter`.

## Configuration

- **Config file**: `.importlinter`
- **Command**: `lint-imports --config .importlinter`
- **Manifest command**: `check:boundaries` (see `.repo/repo.manifest.yaml`)

## How It Works

1. **Static Analysis**: import-linter analyzes Python import statements
2. **Contract Enforcement**: Validates imports against contracts defined in `.importlinter`
3. **CI Integration**: Runs automatically in GitHub Actions (see `.github/workflows/ci.yml`)

## Current Contracts

The `.importlinter` file defines several contracts:

1. **Core module isolation**: Core cannot depend on business modules
2. **Firm module foundation**: Business modules cannot import firm module
3. **Portal API isolation**: Portal API cannot import staff admin modules
4. **API layer isolation**: API modules should not import from each other
5. **Independence contracts**: No circular dependencies between core modules

## UBOS-Specific Rules

- Django modules in `backend/modules/` should be self-contained
- Cross-module imports require justification (see `.repo/policy/BOUNDARIES.md`)
- API layer (`backend/api/`) should not import infrastructure directly

## Running Locally

```bash
# Install import-linter
pip install import-linter==2.0

# Run boundary check
lint-imports --config .importlinter

# Or use manifest command
make check:boundaries  # (if added to Makefile)
```

## CI Integration

The boundary checker runs in GitHub Actions:

```yaml
- name: Check boundary rules with import-linter
  run: lint-imports
```

See `.github/workflows/ci.yml` line 101-104.

## Violations

If boundaries are violated:
- CI will fail
- PR merge is blocked (hard gate)
- Fix violations or create waiver (see `.repo/policy/QUALITY_GATES.md`)

## Adding New Contracts

1. Edit `.importlinter` file
2. Add new contract section
3. Test locally: `lint-imports --config .importlinter`
4. Commit changes

## Related Documentation

- `.repo/policy/BOUNDARIES.md` - Boundary policy and rules
- `.repo/policy/PRINCIPLES.md` - Principle 13 (Respect Boundaries)
- `.repo/repo.manifest.yaml` - Command definitions
