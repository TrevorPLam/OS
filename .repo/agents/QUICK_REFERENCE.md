# Agent Quick Reference Card

**File**: `.repo/agents/QUICK_REFERENCE.md`

> **One-page cheat sheet for AI agents.** See `.repo/agents/AGENTS.md` for full details.

## 🚦 Decision Tree: Do I Need HITL?

```
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

## 📋 Three-Pass Workflow

1. **Plan**: List actions, risks, files, UNKNOWNs → Get approval if needed
2. **Change**: Apply edits → Follow patterns → Include filepaths
3. **Verify**: Run tests → Show evidence → Update logs → Document in PR

## 🔍 Before Starting Work

- [ ] Read `agents/tasks/TODO.md` (current task)
- [ ] Read `.repo/repo.manifest.yaml` (commands)
- [ ] Check `.repo/policy/HITL.md` (blocking items?)
- [ ] Review `.repo/policy/BOUNDARIES.md` (architectural rules)

## ⚠️ Never Do These

- ❌ Guess commands (use manifest or HITL)
- ❌ Skip filepaths (required everywhere)
- ❌ Modify policy files without approval
- ❌ Commit secrets or `.env` files
- ❌ Cross boundaries without ADR
- ❌ Proceed with UNKNOWN items

## ✅ Always Do These

- ✅ Include filepaths in all changes
- ✅ Mark UNKNOWN → Create HITL
- ✅ Follow three-pass workflow
- ✅ Run `make lint` before PR
- ✅ Link changes to tasks
- ✅ Archive completed tasks

## 📁 Key Files

| File | Purpose |
|------|---------|
| `agents/tasks/TODO.md` | Current active task (ONE only) |
| `agents/tasks/BACKLOG.md` | Prioritized queue (P0→P3) |
| `.repo/repo.manifest.yaml` | Commands (single source of truth) |
| `.repo/policy/HITL.md` | Human-in-the-loop items |
| `.repo/policy/CONSTITUTION.md` | 8 fundamental articles |
| `.repo/policy/PRINCIPLES.md` | Operating principles (P3-P25) |

## 🛠️ Common Commands

```bash
make setup          # Install dependencies
make lint           # Run linters
make test           # Run tests
make verify         # Full CI suite
make ci             # Alias for verify
```

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

# Agent Logs
./scripts/generate-agent-log.sh [task-id] [action]

# Waiver Management
./scripts/create-waiver.sh [waiver-id] [what-waives] [why]
./scripts/check-expired-waivers.sh
./scripts/suggest-waiver.sh [verify-output-file]

# ADR Detection & Creation
./scripts/detect-adr-triggers.sh [base-branch]
./scripts/create-adr-from-trigger.sh

# Metrics & Reporting
./scripts/generate-metrics.sh [json|markdown|text]
./scripts/generate-dashboard.sh [output-file]

# Validation
./scripts/validate-manifest-commands.sh

# Governance Verification
./scripts/governance-verify.sh
```

## 🔗 Security Triggers (Require HITL)

1. Auth/login behavior change
2. Money/payment flow change
4. External service integration
5. Sensitive data handling
8. Production config/keys
9. Cryptography/security controls
10. Dependency vulnerabilities

## 📝 Artifact Requirements

| Change Type | Required Artifacts |
|-------------|-------------------|
| Feature | Task Packet, Trace Log, Tests |
| API Change | Task Packet, ADR, Trace Log, OpenAPI update |
| Security | HITL, Trace Log, Security tests |
| Cross-module | ADR, Task Packet, Trace Log |

## 🎯 Task Workflow

1. Read `TODO.md` → Work on task
2. Complete → Mark criteria `[x]`
3. Move to `ARCHIVE.md` (prepend)
4. Promote top task from `BACKLOG.md` to `TODO.md`

## 📚 Examples

- Trace log: `.repo/templates/examples/example_trace_log.json`
- HITL item: `.repo/templates/examples/example_hitl_item.md`
- Waiver: `.repo/templates/examples/example_waiver.md`
- Task packet: `.repo/templates/examples/example_task_packet.json`

---

**Remember**: When in doubt → HITL. No guessing. Filepaths everywhere.
