# Setup Instructions

**File**: `.repo/automation/scripts/SETUP_INSTRUCTIONS.md`

## Quick Start

Since Node.js is not available in all environments, follow these steps when Node.js is available:

### Step 1: Install Node.js (if not installed)

1. Download from: https://nodejs.org/
2. Install (recommended: LTS version)
3. Verify: `node --version` (should show v14+)
4. Verify: `npm --version`

### Step 2: Install Dependencies

```bash
cd .repo/automation/scripts
npm install
```

This installs:
- `ajv` (^8.12.0) - JSON schema validator

**Expected output:**
```
added 1 package, and audited 2 packages in 2s
```

### Step 3: Update Context Files

```bash
# Update all context files with last_verified date
node update-context-verified.js --all
```

**Expected output:**
```
Updating last_verified date for 11 file(s)...

✅ Updated backend/.agent-context.json
✅ Updated frontend/.agent-context.json
✅ Updated backend/modules/clients/.agent-context.json
... (and so on)

✅ Updated 11/11 file(s)
```

### Step 4: Verify Scripts Work

```bash
# Test logging SDK
node agent-logger.js metrics

# Test stale context detection
node check-stale-context.js --warn-only

# Test pattern verification
node pattern-verification.js --warn-only

# Test validation
node validate-agent-context.js ../../backend/.agent-context.json
```

## Manual Alternative

If Node.js is not available, you can manually update context files:

1. Open each `.agent-context.json` file
2. Find the `metrics` section
3. Add `"last_verified": "2026-01-23"` (use today's date)
4. Save the file

Example:
```json
"metrics": {
  "files_count": 500,
  "last_modified": "2026-01-23",
  "last_verified": "2026-01-23",  // Add this line
  "test_coverage": 0.82
}
```

## Files That Need Updating

All `.agent-context.json` files should have `last_verified` in their `metrics` section:

- `backend/.agent-context.json` ✅ (already updated)
- `frontend/.agent-context.json`
- `backend/modules/clients/.agent-context.json`
- `backend/modules/finance/.agent-context.json`
- `backend/modules/core/.agent-context.json`
- `backend/modules/firm/.agent-context.json`
- `backend/modules/crm/.agent-context.json`
- `backend/modules/projects/.agent-context.json`
- `backend/api/clients/.agent-context.json`
- `frontend/src/api/.agent-context.json`
- `frontend/src/components/.agent-context.json`

## Verification

After setup, verify:

1. ✅ `node_modules/` directory exists in `.repo/automation/scripts/`
2. ✅ `package-lock.json` exists
3. ✅ All context files have `last_verified` field
4. ✅ Scripts can be executed without errors

## Troubleshooting

See `.repo/automation/scripts/VERIFICATION.md` for detailed troubleshooting.

---

**Created:** 2026-01-23
