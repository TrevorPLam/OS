# Scripts Directory

This directory contains utility scripts for the ConsultantPro project. Scripts are optional; run them when they help with a specific task rather than by default.

## Activation Guidance

- **Local hooks (opt-in):** Install pre-commit hooks with `pre-commit install` if you want local enforcement. Uninstall with `pre-commit uninstall` to return to a clean state.
- **CI workflows:** GitHub Actions workflows live in `.github/workflows/`.
- **Generated artifacts:** If any script outputs `TODO.generated.md`, keep it gitignored and never overwrite TODO.md automatically.

## TIER 0 Enforcement Scripts

### `pre_launch_gate.sh`

**Purpose**: Enforce the pre-launch checklist gate before production deployment.

**What it checks**:
- `docs/PRE_LAUNCH_CHECKLIST.md` exists and has no unchecked items
- `TODO.md` Status values are valid (READY, BLOCKED, IN-PROGRESS, IN-REVIEW)

**Usage**:

```bash
docs/scripts/pre_launch_gate.sh
```

### `lint_firm_scoping.py`

**Purpose**: Enforce TIER 0 firm scoping requirements by detecting unsafe database queries.

**What it checks**:
- ❌ `Model.objects.all()` on firm-scoped models
- ❌ `Model.objects.filter()` without `firm` parameter
- ❌ `Model.objects.get()` without `firm` parameter

**Models checked** (all have `firm` FK):
- CRM: Lead, Prospect, Campaign, Proposal, Contract
- Clients: Client
- Projects: Project
- Finance: Invoice, Bill, LedgerEntry
- Documents: Folder, Document, Version
- Assets: Asset, MaintenanceLog

**Usage**:

```bash
# Check for violations
python docs/scripts/lint_firm_scoping.py

# Run as part of pre-commit
pre-commit run lint-firm-scoping --all-files
```

**Example violations**:

```python
# ❌ WRONG - queries all firms' clients
clients = Client.objects.all()

# ✅ CORRECT - firm-scoped query
firm = get_request_firm(request)
clients = Client.firm_scoped.for_firm(firm)

# ✅ ALSO CORRECT - explicit firm filter
clients = Client.objects.filter(firm=firm)
```

**Integration**:

This script is automatically run by:
- Pre-commit hooks (`.pre-commit-config.yaml`)
- CI/CD pipeline (GitHub Actions)
- Manual developer checks

**Exit codes**:
- `0`: No violations found ✅
- `1`: Violations detected ❌

## Documentation Inventory Scripts

### `inventory_api_coverage.py`

**Purpose**: Inventory API endpoint coverage across `src/modules/` and `src/api/`.

**What it checks**:
- `src/modules/<module>/urls.py` and `src/modules/<module>/views.py`
- `src/api/<module>/urls.py` and `src/api/<module>/views.py`

**Usage**:

```bash
python docs/scripts/inventory_api_coverage.py
```

## Setup

### Install development tools:

```bash
# Install linting and formatting tools
pip install ruff black pre-commit

# Install pre-commit hooks
pre-commit install

# Run all checks manually
pre-commit run --all-files
```

### Run firm scoping linter:

```bash
# Check for violations
python docs/scripts/lint_firm_scoping.py

# Expected output if violations found:
# ================================================================================
# TIER 0 Firm Scoping Linter
# ================================================================================
#
# Checking 24 files...
#
# ❌ src/modules/crm/views.py
# --------------------------------------------------------------------------------
#   Line 42: Model.objects.all() forbidden on firm-scoped models. Use Model.firm_scoped.for_firm(firm) instead.
#     queryset = Lead.objects.all()
#
# ================================================================================
# ❌ Found 1 firm scoping violation(s).
#
# TIER 0 REQUIREMENT: All queries on firm-scoped models MUST include firm context.
# ================================================================================
```

## Continuous Integration

These scripts are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run TIER 0 Linting
  run: |
    python docs/scripts/lint_firm_scoping.py
```

## Future Enhancements

- [ ] Auto-fix mode (--fix flag)
- [ ] Detect raw SQL queries without firm filtering
- [ ] Check serializers for firm context in create/update
- [ ] Validate that all API endpoints enforce firm context
- [ ] Report metrics (coverage of firm scoping)
