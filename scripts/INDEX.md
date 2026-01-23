# Scripts Directory Index

**File**: `scripts/INDEX.md`

This file catalogs the scripts in the `scripts/` directory. See [root `INDEX.md`](../INDEX.md) for repository overview.

## Scripts

### `governance-verify.sh`
Enforces quality gates per `.repo/policy/QUALITY_GATES.md`. Checks required policy files, manifest, HITL items, and repository structure.

**Usage**: `./scripts/governance-verify.sh`

**Exit codes**:
- `0` - Pass (all checks pass)
- `1` - Hard failure (blocks merge)
- `2` - Waiverable failure (requires waiver)

### `migrate.sh`
Database migration script for UBOS. Creates and applies Django migrations, with prompts for user confirmation.

**Usage**: `./scripts/migrate.sh`

**Features**:
- Creates migrations for all modules
- Shows migration plan
- Prompts for confirmation before applying
- Option to create superuser

### `setup-migrations.sh`
Sets up migration environment and dependencies.

**Usage**: `./scripts/setup-migrations.sh`

## Navigation

- [Root `INDEX.md`](../INDEX.md) - Repository master index
- [`backend/INDEX.md`](../backend/INDEX.md) - Backend directory index

## See Also

- `scripts/SCRIPTS.md` - What agents may do in this directory
- [`.repo/policy/QUALITY_GATES.md`](../.repo/policy/QUALITY_GATES.md) - Quality gate definitions
