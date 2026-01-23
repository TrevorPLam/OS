# Script Verification Guide

**File**: `.repo/automation/scripts/VERIFICATION.md`

This guide helps verify that all scripts are working correctly.

## Prerequisites

1. **Node.js installed** (v14 or higher)
   - Check: `node --version`
   - Install: https://nodejs.org/

2. **Dependencies installed**
   ```bash
   cd .repo/automation/scripts
   npm install
   ```

## Verification Steps

### 1. Install Dependencies

```bash
cd .repo/automation/scripts
npm install
```

**Expected output:**
- `ajv` package installed in `node_modules/`
- `package-lock.json` created/updated

### 2. Update Context Files

```bash
node update-context-verified.js --all
```

**Expected output:**
- All `.agent-context.json` files updated with `last_verified` date
- Success message for each file

**Manual verification:**
- Check that `metrics.last_verified` field exists in context files
- Date should be today's date (YYYY-MM-DD format)

### 3. Test Logging SDK

```bash
# Generate metrics for today
node agent-logger.js metrics

# Generate metrics for specific date
node agent-logger.js metrics 2026-01-23

# Cleanup old logs (keep last 30 days)
node agent-logger.js cleanup 30
```

**Expected output:**
- Metrics JSON printed to console
- Metrics file created in `.agent-logs/metrics/`

### 4. Test Stale Context Detection

```bash
# Check for stale files (warn only)
node check-stale-context.js --warn-only

# Check for stale files (fail on stale)
node check-stale-context.js --threshold-days=30
```

**Expected output:**
- List of stale files (if any)
- Warning messages for files missing `last_verified`
- Success message if all files are up to date

### 5. Test Pattern Verification

```bash
# Check pattern files (warn only)
node pattern-verification.js --warn-only

# Check pattern files (fail on issues)
node pattern-verification.js
```

**Expected output:**
- List of pattern file issues (if any)
- Success message if all patterns are properly configured

### 6. Test Context Validation

```bash
# Basic validation
node validate-agent-context.js ../../backend/.agent-context.json

# With file path checking
node validate-agent-context.js ../../backend/.agent-context.json --check-files

# With all checks
node validate-agent-context.js ../../backend/.agent-context.json --check-files --check-boundaries --check-links
```

**Expected output:**
- Validation success message
- Warnings for non-critical issues (if any)
- Errors for critical issues (if any)

### 7. Test Boundary Checking

```bash
# Check boundaries (requires import-linter)
node check-boundaries.js --fail-on-violations
```

**Expected output:**
- Boundary check results
- List of violations (if any)
- Success message if no violations

**Note:** Requires `import-linter` to be installed:
```bash
pip install import-linter==2.0
```

## Troubleshooting

### Node.js Not Found

**Error:** `node: command not found`

**Solution:**
1. Install Node.js from https://nodejs.org/
2. Restart terminal/IDE
3. Verify: `node --version`

### npm Install Fails

**Error:** `npm ERR!` messages

**Solutions:**
1. Check internet connection
2. Clear npm cache: `npm cache clean --force`
3. Try: `npm install --legacy-peer-deps`

### Scripts Fail with Module Errors

**Error:** `Cannot find module 'ajv'`

**Solution:**
```bash
cd .repo/automation/scripts
npm install
```

### Permission Errors

**Error:** `EACCES: permission denied`

**Solution:**
- On Linux/Mac: Use `sudo` (if needed) or fix permissions
- On Windows: Run as Administrator or fix folder permissions

## Manual Verification Checklist

If scripts can't run, verify manually:

- [ ] `package.json` exists in `.repo/automation/scripts/`
- [ ] All `.js` script files exist and are executable
- [ ] Context files have `metrics.last_verified` field (can add manually)
- [ ] Pattern files exist and are referenced in `.AGENT.md` files
- [ ] Scripts have proper shebang (`#!/usr/bin/env node`)

## Success Criteria

All scripts are working correctly if:
- ✅ Dependencies install without errors
- ✅ Context files can be updated
- ✅ Logging SDK generates metrics
- ✅ Validation scripts run and report correctly
- ✅ No critical errors in script execution

---

**Last updated:** 2026-01-23
