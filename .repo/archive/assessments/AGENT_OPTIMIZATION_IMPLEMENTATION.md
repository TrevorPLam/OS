# Agent Optimization Implementation Guide

**Date:** 2026-01-23
**Purpose:** Guide for implementing agent-friendly optimizations across the repository

---

## Overview

This guide explains how to implement the agent optimization system proposed in `AGENT_OPTIMIZATION_PROPOSAL.md`.

---

## Files Created

### 1. Schema & Templates

- `.repo/templates/AGENT_CONTEXT_SCHEMA.json` - JSON schema for `.agent-context.json` files
- `.repo/templates/AGENT_QUICK_REFERENCE_TEMPLATE.md` - Template for `.AGENT.md` files
- `.repo/templates/AGENT_PATTERNS_TEMPLATE.md` - Template for `PATTERNS.md` files

### 2. Example Context Files

- `backend/.agent-context.json` - Example for backend folder
- `frontend/.agent-context.json` - Example for frontend folder

### 3. Automation Scripts

- `.repo/automation/scripts/generate-agent-context.js` - Generate context file template
- `.repo/automation/scripts/validate-agent-context.js` - Validate context files

---

## Implementation Steps

### Step 1: Create Context Files for Core Folders

```bash
# Generate template
node .repo/automation/scripts/generate-agent-context.js backend/modules/clients

# Edit the generated file to fill in details
# Then validate
node .repo/automation/scripts/validate-agent-context.js backend/modules/clients/.agent-context.json
```

### Step 2: Create Quick Reference Files

Use the template in `.repo/templates/AGENT_QUICK_REFERENCE_TEMPLATE.md` to create `.AGENT.md` files for each folder.

### Step 3: Create Pattern Files

Use the template in `.repo/templates/AGENT_PATTERNS_TEMPLATE.md` to create `PATTERNS.md` files for folders with common patterns.

### Step 4: Set Up Logging (Future)

Create `.agent-logs/` directory structure and logging infrastructure.

---

## Priority Order

1. **Core folders** (backend/, frontend/)
2. **Foundation modules** (backend/modules/core/, backend/modules/firm/)
3. **High-traffic modules** (backend/modules/clients/, backend/modules/crm/, etc.)
4. **API folders** (backend/api/*/)
5. **Frontend folders** (frontend/src/api/, frontend/src/components/)

---

## Validation

Run validation on all context files:

```bash
find . -name ".agent-context.json" -exec node .repo/automation/scripts/validate-agent-context.js {} \;
```

---

## Maintenance

- Update context files when folder structure changes
- Regenerate metrics periodically
- Update patterns when code patterns evolve
- Keep quick references in sync with full documentation

---

**End of Implementation Guide**
