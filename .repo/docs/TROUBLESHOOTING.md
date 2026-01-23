# Troubleshooting Guide

**File**: `.repo/docs/TROUBLESHOOTING.md`

This guide helps resolve common issues with agent workflows and automation scripts.

## Script Failures

### HITL Creation Script Fails

**Symptom:** `scripts/create-hitl-item.sh` fails with error

**Possible Causes:**
1. File permissions issue
2. `.repo/hitl/` directory doesn't exist
3. `.repo/policy/HITL.md` is locked or missing

**Solutions:**
1. Check permissions: `ls -la scripts/create-hitl-item.sh`
2. Create directory: `mkdir -p .repo/hitl`
3. Check HITL index: `cat .repo/policy/HITL.md`
4. Manual creation: Create `HITL-XXXX.md` in `.repo/hitl/` and update `.repo/policy/HITL.md` manually

### Logging SDK Fails

**Symptom:** `agent-logger.js` throws errors or doesn't write logs

**Possible Causes:**
1. `.agent-logs/` directory doesn't exist
2. File permissions issue
3. Disk space full

**Solutions:**
1. Create directories: `mkdir -p .agent-logs/{interactions,errors,metrics}`
2. Check permissions: `ls -la .agent-logs/`
3. Check disk space: `df -h`
4. Graceful fallback: Logging failures are non-blocking - workflow continues

### Validation Script Fails

**Symptom:** `validate-agent-context.js` fails validation

**Possible Causes:**
1. JSON syntax error in context file
2. Missing required fields
3. Schema validation failure (ajv not installed)

**Solutions:**
1. Check JSON syntax: `cat .agent-context.json | python -m json.tool`
2. Review schema: `.repo/templates/AGENT_CONTEXT_SCHEMA.json`
3. Install dependencies: `cd .repo/automation/scripts && npm install`
4. Basic validation: Script falls back to basic checks if ajv not installed

### Boundary Check Fails

**Symptom:** `check-boundaries.js` or `lint-imports` fails

**Possible Causes:**
1. `import-linter` not installed
2. `.importlinter` config file missing
3. Actual boundary violations in code

**Solutions:**
1. Install: `pip install import-linter==2.0`
2. Check config: `cat .importlinter`
3. Fix violations: Review error output and refactor imports
4. Create waiver: If exception needed (see `.repo/policy/QUALITY_GATES.md`)

### Governance-Verify Fails

**Symptom:** `governance-verify.sh` or `governance-verify.js` reports failures

**Possible Causes:**
1. Missing required artifacts
2. HITL items not completed
3. Boundary violations
4. Stale context files

**Solutions:**
1. Review error output for specific failures
2. Complete required HITL items
3. Fix boundary violations
4. Update context files: `node .repo/automation/scripts/update-context-verified.js --all`

## Workflow Issues

### Context Files Not Found

**Symptom:** Agent can't find `.agent-context.json` files

**Solutions:**
1. Verify files exist: `find . -name ".agent-context.json"`
2. Check file paths in context files are correct
3. Regenerate if needed: `node .repo/automation/scripts/generate-agent-context.js`

### Pattern Files Out of Date

**Symptom:** Patterns in `PATTERNS.md` don't match actual code

**Solutions:**
1. Review actual code in folder
2. Update `PATTERNS.md` to match
3. Update `.agent-context.json` patterns field
4. Run verification: `node .repo/automation/scripts/pattern-verification.js`

### Task Packet Missing

**Symptom:** `governance-verify` reports missing task packet

**Solutions:**
1. Create task packet: See `.repo/agents/QUICK_REFERENCE.md` Task Packet Workflow
2. Store in `.repo/tasks/packets/TASK-XXX-packet.json` or include in `TODO.md`
3. Link in PR description

## Recovery Procedures

### When Scripts Fail Completely

1. **Check logs:** Review error messages carefully
2. **Manual steps:** Follow manual procedures documented in this guide
3. **Create HITL:** If issue is blocking, create HITL item for help
4. **Bypass (temporary):** Only if absolutely necessary, create waiver (see `.repo/policy/QUALITY_GATES.md`)

### When Workflow Is Blocked

1. **Identify blocker:** Review HITL items, waivers, or quality gate failures
2. **Resolve blocker:** Complete HITL items, fix violations, or create waivers
3. **Re-run verification:** `./scripts/governance-verify.sh`

### When Context Files Are Stale

1. **Check staleness:** `node .repo/automation/scripts/check-stale-context.js`
2. **Update files:** `node .repo/automation/scripts/update-context-verified.js --all`
3. **Verify patterns:** Review actual code and update patterns if needed

## Getting Help

- **Policy questions:** See `.repo/policy/` directory
- **Workflow questions:** See `.repo/agents/QUICK_REFERENCE.md`
- **Blocking issues:** Create HITL item in `.repo/policy/HITL.md`
- **Script issues:** Check this troubleshooting guide first

---

**Last updated:** 2026-01-23
