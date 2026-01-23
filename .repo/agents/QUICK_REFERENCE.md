# Agent Quick Reference Card

**File**: `.repo/agents/QUICK_REFERENCE.md`

> **Essential Rules:** This document contains ALL critical rules agents need to operate. Full policy documents (CONSTITUTION.md, PRINCIPLES.md) provide deeper context when needed.

**Agent Instructions:** Read `AGENTS.json` (or `AGENTS.md`) and `.repo/tasks/TODO.md` first, then this file.

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

1. **Plan**: List actions, risks, files, UNKNOWNs → Get approval if needed
2. **Change**: Apply edits → Follow patterns → Include filepaths
3. **Verify**: Run tests → Show evidence → Update logs → Document in PR

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
2. Complete → Mark criteria `[x]`
3. Move to `ARCHIVE.md` (prepend)
4. Promote top task from `BACKLOG.md` to `TODO.md`

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

# Trace Logs
./scripts/generate-trace-log.sh [task-id] [intent]
./scripts/validate-trace-log.sh [trace-log-file]

# Task Management
./scripts/validate-task-format.sh [task-file]
./scripts/get-next-task-number.sh
./scripts/promote-task.sh [task-id]
python3 scripts/archive-task.py [--force]

# PR Validation
./scripts/validate-pr-body.sh [pr-body-file]

# Governance Verification
./scripts/governance-verify.sh
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
