# Agent Quick Reference Card

**File**: `.repo/agents/QUICK_REFERENCE.md`

> **Essential Rules:** This document contains ALL critical rules agents need to operate. Full policy documents (CONSTITUTION.md, PRINCIPLES.md) provide deeper context when needed.

**Agent Instructions:** This is your quick reference. Read in this order:

1. `.repo/tasks/TODO.md` - Current task (MUST READ FIRST)
2. `.repo/repo.manifest.yaml` - Commands (BEFORE ANY COMMAND)
3. This file (`.repo/agents/QUICK_REFERENCE.md`) - Rules (START HERE)

**When entering a folder:**
- Read `.agent-context.json` (if exists) - Machine-readable folder context
- Read `.AGENT.md` (if exists) - Human-readable folder quick reference

**Use this as reference while working.** Follow three-pass workflow from `AGENTS.json`. Use decision trees below for UNKNOWN or risky situations.

---

## 🚦 Decision Tree: Do I Need HITL?

```text
Is it risky? (security, money, production, external systems)
├─ YES → Create HITL item → Stop work → Wait for completion
└─ NO → Continue

Is it UNKNOWN? (not in docs, manifest, or code)
├─ YES → Mark <UNKNOWN> → Create HITL → Stop work
└─ NO → Continue

Does it cross module boundaries?
├─ YES → Requires ADR (Principle 23)
└─ NO → Continue

Did a waiverable gate fail? (coverage, performance, warnings)
├─ YES → Create waiver using template → Link in PR
└─ NO → Continue
```

---

## 📜 Constitution (8 Articles) - Essential Rules

**Article 1: Final Authority** - Solo founder has final say on ambiguity/conflicts

**Article 2: Verifiable over Persuasive** - Work needs verification evidence. Proof beats persuasion.

**Article 3: No Guessing** - If unknown: Mark `<UNKNOWN>` → Create HITL → Stop work

**Article 4: Incremental Delivery** - Ship small, reviewable, testable increments. No mega-PRs.

**Article 5: Strict Traceability** - Every change must link to task in `.repo/tasks/TODO.md`. Archive completed tasks.

**Article 6: Safety Before Speed** - Risky changes: **STOP → ASK (HITL) → VERIFY → THEN PROCEED**

**Article 7: Per-Repo Variation** - Workflow may vary per repo (via manifest)

**Article 8: HITL for External Systems** - Credentials, billing, production, external services = always HITL

---

## 🎯 Key Principles (Most Critical)

**Global Rule:** Filepaths required everywhere (PRs, logs, ADRs, waivers, comments)

**P3: One Change Type Per PR** - Split work if multiple types needed

**P4: Make It Shippable** - Each PR should be safe to merge and ship (or clearly blocked by HITL/waivers)

**P5: Don't Break Surprises** - If users, security, money, or production behavior could change: call it out, add tests, add rollback plan, use HITL

**P6: Evidence Over Vibes** - Show proof: commands, outputs, test results, filepaths

**P7: UNKNOWN Is First-Class** - Mark explicitly, route to HITL

**P8: Read Repo First** - Use `.repo/` docs + `repo.manifest.yaml` before deciding anything

**P9: Assumptions Must Be Declared** - Any assumption must be written down and labeled as an assumption

**P10: Risk Triggers a Stop** - Non-trivial risk → STOP → HITL → VERIFY

**P11: Prefer Guardrails Over Heroics** - Prefer checks, tooling, and automation over "trust me"

**P12: Rollback Thinking** - Every risky change must have rollback thinking (how to undo safely)

**P13: Respect Boundaries** - Don't cross module boundaries unless rules allow

**P14: Localize Complexity** - Put complexity where it belongs. Keep it contained.

**P15: Consistency Beats Novelty** - Prefer existing patterns and names. Novelty requires justification.

**P16: Decisions Written Down** - Record decisions in the smallest durable place (ADR only when triggered)

**P17: PR Narration** - PR must explain: what, why, filepaths, verification, risks, rollback

**P18: No Silent Scope Creep** - Do not expand scope without updating Task Packet and calling it out

**P19: Docs Age With Code** - When code changes, docs must change too if they describe behavior

**P20: Examples Are Contracts** - Examples define expected behavior. If code changes, examples must be updated

**P21: Naming Matters** - Names must be clear. Avoid confusing abbreviations.

**P22: Waivers Rare + Temporary** - Waivers are not permanent. They expire. They require a plan.

**P23: ADR Required When Triggered** - Cross-feature imports require ADR. No exceptions.

**P24: Logs Required for Non-Docs** - Non-doc-only changes require agent logs + trace logs + reasoning summary

**P25: Token-Optimized TODO** - Use TODO/BACKLOG/ARCHIVE, archive completed work

---

## 📋 Three-Pass Workflow

**Pass 0: Context** (When entering folder)
- Read `.agent-context.json` if exists (machine-readable folder context)
- Read `.AGENT.md` if exists (human-readable folder quick reference)

1. **Plan**: Determine change type → Check boundaries → Create task packet (if required) → List actions, risks, files, UNKNOWNs → Get approval if needed
   - **First:** Determine change type (feature/api_change/security/cross_module/non_doc_change)
   - **Check boundaries:** Run `lint-imports --config .importlinter` or `node .repo/automation/scripts/check-boundaries.js` (see Boundary Checking below)
   - **If feature/api_change/cross_module:** Create task packet in Pass 1 (see Task Packet Workflow below)
   - If crossing boundaries → Create ADR (see ADR Workflow below)
   - If risky/unknown → Create HITL → Stop work
2. **Change**: Apply edits → Follow patterns → Include filepaths
3. **Verify**: Run tests → Show evidence → Update logs → Document in PR
   - Create trace log using `scripts/generate-trace-log.sh` (for non-doc changes)
   - Create agent log using `scripts/generate-agent-log.sh` (for reasoning summary, P24)

---

## 🔍 Before Starting Work

- [ ] Read `.repo/tasks/TODO.md` (current task) - **MUST READ FIRST**
- [ ] Read `.repo/repo.manifest.yaml` (commands) - **BEFORE ANY COMMAND**
- [ ] Check `.repo/policy/HITL.md` (blocking items?)
- [ ] If crossing boundaries → Read `.repo/policy/BOUNDARIES.md`
- [ ] If security-related → Read `.repo/policy/SECURITY_BASELINE.md`

---

## ⚠️ Never Do These

- ❌ Guess commands (use manifest or HITL) - Article 3
- ❌ Skip filepaths (required everywhere - global rule)
- ❌ Modify policy files without approval
- ❌ Commit secrets or `.env` files (absolute prohibition)
- ❌ Cross boundaries without ADR (Principle 23)
- ❌ Proceed with UNKNOWN items (Article 3)
- ❌ Make risky changes without HITL (Article 6 & 8)
- ❌ Create mega-PRs (Article 4: incremental delivery)
- ❌ Skip verification evidence (Article 2)
- ❌ Expand scope silently (Principle 18)
- ❌ Make assumptions without declaring them (Principle 9)

---

## ✅ Always Do These

- ✅ Include filepaths in all changes (global rule)
- ✅ Link changes to task in `.repo/tasks/TODO.md` (Article 5)
- ✅ Mark UNKNOWN → Create HITL (Article 3)
- ✅ Follow three-pass workflow
- ✅ Run `make lint` before PR
- ✅ Archive completed tasks to `.repo/tasks/ARCHIVE.md` (Article 5)
- ✅ Show verification evidence (Article 2, P6)
- ✅ Explain what/why/filepaths/verification/risks/rollback in PR (P17)
- ✅ Update docs when code behavior changes (P19)
- ✅ Update examples when code changes (P20)
- ✅ Declare assumptions explicitly (P9)
- ✅ Think about rollback for risky changes (P12)

---

## 🛠️ Commands

**Source of Truth:** `.repo/repo.manifest.yaml` (read this, don't guess - Article 3)

```bash
make setup          # Install dependencies
make lint           # Run linters (backend + frontend)
make test           # Run tests (pytest + vitest)
make verify         # Full CI suite (light checks)
make verify SKIP_HEAVY=0  # Full suite (tests/build/OpenAPI)
make ci             # Alias for verify
```

**Backend:** `make -C backend migrate` | `make -C backend openapi`
**Frontend:** `make -C frontend test` | `make -C frontend e2e`

---

## 🔗 Security Triggers (Require HITL - Article 8)

1. Auth/login behavior change
2. Money/payment flow change
3. External service integration
4. Sensitive data handling
5. Production config/keys
6. Cryptography/security controls
7. Dependency vulnerabilities

**Action:** Read `.repo/policy/SECURITY_BASELINE.md` → Create HITL → Stop work

---

## 🎯 Change Type Determination

**When:** Determine change type in **Pass 1 (Plan)** before creating artifacts.

**Decision Tree:**
```
Does it touch security/auth/money/external systems?
├─ YES → Change Type: "security" (requires HITL)
└─ NO → Continue

Does it cross module/feature boundaries?
├─ YES → Change Type: "cross_module" (requires ADR)
└─ NO → Continue

Does it change API contracts/endpoints?
├─ YES → Change Type: "api_change" (requires ADR + OpenAPI update)
└─ NO → Continue

Does it add new functionality/features?
├─ YES → Change Type: "feature"
└─ NO → Continue

Is it only documentation changes?
├─ YES → No artifacts required (doc-only)
└─ NO → Change Type: "non_doc_change" (requires agent log + trace log)
```

**Examples:**
- **Feature:** Adding new user profile page, new dashboard widget, new report
- **API Change:** Adding new endpoint, changing request/response format, versioning API
- **Security:** Auth changes, payment flows, external service integration, sensitive data handling
- **Cross-module:** Importing from one module into another, shared utilities across modules
- **Non-doc change:** Bug fixes, refactoring, configuration changes, test updates

**Important:** One change type per PR (Principle 3). If multiple types, split into separate PRs.

---

## 📝 Artifact Requirements

| Change Type | Required Artifacts |
|-------------|--------------------|
| Feature | Task Packet, Trace Log, Tests |
| API Change | Task Packet, ADR, Trace Log, OpenAPI update |
| Security | HITL, Trace Log, Security tests |
| Cross-module | ADR, Task Packet, Trace Log |
| Non-doc change | Agent Log, Trace Log, Reasoning Summary (P24) |

---

## 🎯 Task Workflow

1. Read `.repo/tasks/TODO.md` → Work on task
   - **If TODO.md is empty:** Promote top task from `BACKLOG.md` to `TODO.md`
2. Complete → Mark criteria `[x]`
3. Move to `ARCHIVE.md` (prepend)
4. Promote top task from `BACKLOG.md` to `TODO.md`

---

## 📝 Trace Log Workflow

**When:** Create trace log in **Pass 3 (Verify)** after tests pass, for **non-doc changes only**.

**How:**
1. Run `scripts/generate-trace-log.sh [task-id] [intent]`
2. Fill in required fields: `intent`, `files`, `commands`, `evidence`, `hitl`, `unknowns`
3. Validate: `scripts/validate-trace-log.sh [trace-log-file]`
4. Store in `.repo/traces/`

**What it tracks:** What changed (files, commands, evidence)

---

## 📋 Agent Log Workflow

**When:** Create agent log in **Pass 3 (Verify)** for **non-doc changes** (P24 requirement).

**How:**
1. Run `scripts/generate-agent-log.sh [task-id] [action]`
2. Fill in: `intent`, `plan`, `actions`, `evidence`, `decisions`, `risks`, `reasoning_summary`
3. Store in `.repo/logs/`

**What it tracks:** Why/how (reasoning, decisions, assumptions)

**Difference from trace log:**
- **Trace log** = What changed (files, commands, evidence)
- **Agent log** = Why/how (reasoning, decisions, assumptions)

---

## 📊 Agent Interaction Logging

**When:** Log interactions during **Pass 0, 1, 2, 3** of workflow for metrics and debugging.

**How:**
1. Use logging SDK: `const logger = require('.repo/automation/scripts/agent-logger.js')`
2. Log interactions: `logger.logInteraction({ agent, action, file, duration_ms, success, context })`
3. Log errors: `logger.logError({ agent, action, error, context })`
4. Logs are automatically written to `.agent-logs/interactions/` (JSONL format)
5. Errors are written to `.agent-logs/errors/`
6. Metrics are generated daily in `.agent-logs/metrics/`

**Example:**
```javascript
const logger = require('.repo/automation/scripts/agent-logger.js');

// Log a file read operation
const startTime = Date.now();
try {
  const content = fs.readFileSync('file.txt', 'utf8');
  logger.logInteraction({
    agent: 'Auto',
    action: 'read_file',
    file: 'file.txt',
    duration_ms: Date.now() - startTime,
    success: true,
    context: { task: 'TASK-001', folder: 'backend' }
  });
} catch (err) {
  logger.logError({
    agent: 'Auto',
    action: 'read_file',
    error: err.message,
    context: { file: 'file.txt' }
  });
}
```

**When to log:**
- **Pass 0:** Log context file reads
- **Pass 1:** Log planning actions (determining change type, creating task packets)
- **Pass 2:** Log file operations (read, write, search)
- **Pass 3:** Log verification actions (test runs, validation)

**Note:** Logging is optional but recommended for metrics collection. If logger is unavailable, workflow continues without logging.

---

## 🔒 Boundary Checking

**When:** Run in **Pass 1 (Plan)** before making changes, especially for cross-module work.

**How:**
1. Run boundary check: `lint-imports --config .importlinter`
   - Or use script: `node .repo/automation/scripts/check-boundaries.js`
2. Review violations (if any)
3. If violations exist:
   - **Fix:** Refactor to respect boundaries
   - **Or create ADR:** If cross-module import is justified (see ADR Workflow)
   - **Or create waiver:** If exception is needed (see Waiver Workflow)
4. Re-run check until clean or waived

**Boundary Rules:**
- See `.repo/policy/BOUNDARIES.md` for full rules
- Core module cannot depend on business modules
- Business modules should not import each other directly
- Cross-module imports require ADR (Principle 23)
- API modules should not import from each other

**CI Integration:** Boundary checks run automatically in CI. PRs with violations are blocked unless fixed or waived.

---

## 🏗️ ADR Workflow

**When:** Required when crossing module/feature boundaries (Principle 23, BOUNDARIES.md).

**Trigger:** Cross-feature imports detected → Create ADR in **Pass 1 (Plan)**.

**How:**
1. Detect triggers: `scripts/detect-adr-triggers.sh` or run boundary check
2. Read `.repo/policy/BOUNDARIES.md` for boundary rules
3. Create ADR: `scripts/create-adr-from-trigger.sh` or use template `.repo/templates/ADR_TEMPLATE.md`
4. Store in `docs/adr/ADR-XXXX.md` (directory auto-created by script)
5. Link ADR in PR description

**Required for:** Cross-module imports, API contract changes, schema changes

**Note:** `docs/adr/` directory must exist. If missing, create it: `mkdir -p docs/adr`

---

## 📦 Task Packet Workflow

**When:** Required in **Pass 1 (Plan)** for change types: `feature`, `api_change`, `cross_module`.

**How:**
1. Determine change type (feature/api_change/cross_module)
2. Create task packet using template `.repo/agents/prompts/task_packet.md`
3. Store task packet:
   - **Option 1 (Recommended):** Store as JSON file in `.repo/tasks/packets/TASK-XXX-packet.json`
   - **Option 2:** Include in `.repo/tasks/TODO.md` as a code block or section
4. Fill in all required fields:
   - `goal`: What you're building/changing
   - `non_goals`: What you're NOT doing
   - `acceptance_criteria`: How to verify completion
   - `approach`: How you'll implement it
   - `files_touched`: List of files to modify (include filepaths)
   - `verification_plan`: How you'll test/verify
   - `risks`: Potential issues
   - `rollback_plan`: How to undo if needed
   - `hitl_requirements`: Any HITL items needed
5. Link task packet in PR description

**Examples:**
- Feature: `.repo/templates/examples/example_task_packet.json`
- API Change: See `.repo/templates/examples/` (create if missing)
- Cross-module: See `.repo/templates/examples/` (create if missing)

**Validation:** `governance-verify` checks that task packets exist for required change types.

---

## 📦 HITL Creation Workflow

**When:** Required for risky changes (security, money, production, external systems) or UNKNOWN items.

**How:**
1. Run: `scripts/create-hitl-item.sh [category] [summary]`
   - Categories: `External Integration`, `Clarification`, `Risk`, `Feedback`, `Vendor`
   - Example: `scripts/create-hitl-item.sh Risk "Payment flow change" "Modifying payment processing logic"`
2. Script creates `HITL-XXXX.md` in `.repo/hitl/`
3. Script updates `.repo/policy/HITL.md` index automatically
4. Link HITL item in PR description: `HITL-XXXX`
5. Wait for HITL item status to be "Completed" before proceeding

**Required for:**
- Security changes (auth, money, external systems)
- UNKNOWN items (not in docs/manifest/code)
- Risky production changes

**See:** `.repo/policy/HITL.md` for full process

---

## 🎫 Waiver Workflow

**When:** Waiverable gate fails (coverage, performance, warnings) per QUALITY_GATES.md.

**How:**
1. `governance-verify` detects waiverable failure → suggests waiver
2. Create waiver: `scripts/create-waiver.sh` or use template `.repo/templates/WAIVER_TEMPLATE.md`
3. Store in `.repo/waivers/WAIVER-XXX.md`
4. Add to `.repo/policy/WAIVERS.md` index
5. Set expiration date (waivers are temporary per Principle 22)
6. Link waiver in PR description

**Check expired:** `scripts/check-expired-waivers.sh`

---

## 📚 When to Read Full Policy Documents

**Read full documents only when:**
- Need deeper context on a specific article/principle
- Encountering edge case not covered here
- Need to understand full policy structure
- Creating ADR/waiver and need full context

**Full documents:**
- `.repo/policy/CONSTITUTION.md` - All 8 articles (detailed)
- `.repo/policy/PRINCIPLES.md` - All 25 principles (detailed)
- `.repo/policy/QUALITY_GATES.md` - Merge requirements (before PR)
- `.repo/policy/SECURITY_BASELINE.md` - Security rules (security work)
- `.repo/policy/BOUNDARIES.md` - Boundary rules (cross-module work)
- `.repo/policy/HITL.md` - HITL process (creating HITL items)
- `.repo/policy/BESTPR.md` - Repo-specific patterns (backend/frontend work)

**Document map:** See `.repo/DOCUMENT_MAP.md` for when to read what

---

## 🔧 Governance Scripts

```bash
# HITL Management
./scripts/create-hitl-item.sh [category] [summary]
python3 scripts/sync-hitl-to-pr.py [PR_NUMBER]
./scripts/archive-hitl-items.sh [--dry-run]

# Trace Logs
./scripts/generate-trace-log.sh [task-id] [intent]
./scripts/validate-trace-log.sh [trace-log-file]
node .repo/automation/scripts/validate-agent-trace.js [trace-log-file]

# Agent Logs
./scripts/generate-agent-log.sh [task-id] [action]

# Task Management
./scripts/validate-task-format.sh [task-file]
./scripts/get-next-task-number.sh
./scripts/promote-task.sh [task-id]
python3 scripts/archive-task.py [--force]

# ADR Management
./scripts/detect-adr-triggers.sh [base-branch]
./scripts/create-adr-from-trigger.sh

# Waiver Management
./scripts/create-waiver.sh
./scripts/suggest-waiver.sh
./scripts/check-expired-waivers.sh

# PR Validation
./scripts/validate-pr-body.sh [pr-body-file]

# Governance Verification
./scripts/governance-verify.sh  # Bash version (canonical, used in CI)
node .repo/automation/scripts/governance-verify.js  # Node.js version (alternative)
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `.repo/tasks/TODO.md` | Current active task (ONE only) |
| `.repo/tasks/BACKLOG.md` | Prioritized queue (P0→P3) |
| `.repo/repo.manifest.yaml` | Commands (single source of truth) |
| `.repo/policy/HITL.md` | Human-in-the-loop items |
| `.repo/templates/examples/` | Format examples |


---

**Remember**: This document has all essential rules. Read full policy documents only when you need deeper context or encounter edge cases.
