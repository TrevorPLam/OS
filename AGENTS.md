# Agent Entry Point

**Role:** AI coding agent. Complete tasks safely following all rules.

**Command received:** Start/Work/Task/Review/Security/Help

---

## Command Routing

- `Start`/`Work`/`Task` → Follow workflow below
- `Review` → Skip to "Creating a PR" section
- `Security` → Read `.repo/policy/SECURITY_BASELINE.md` first, then workflow
- `Help` → See "Next Steps" section

---

## Step 1: Read These Files (In Order)

1. `.repo/tasks/TODO.md` - Current task
2. `.repo/repo.manifest.yaml` - Commands (source of truth)
3. `.repo/agents/rules.json` - All rules (or `QUICK_REFERENCE.md` for human-readable)

---

## Step 2: Determine Context

**When entering a folder:**
→ Read `.agent-context.json` (if exists) → Read `.AGENT.md` (if exists) → Use folder-specific context

**If security/auth/money/external:**
→ Read `.repo/policy/SECURITY_BASELINE.md` → Create HITL → Stop work

**If cross-module boundaries:**
→ Read `.repo/policy/BOUNDARIES.md` → Create ADR

**If backend/frontend:**
→ Read `.repo/policy/BESTPR.md` + folder guide (`backend/BACKEND.md` or `frontend/FRONTEND.md`) + `.agent-context.json`

**If UNKNOWN:**
→ Mark `<UNKNOWN>` → Read `.repo/policy/HITL.md` → Create HITL → Stop work

---

## Step 3: Three-Pass Workflow

### Pass 0: Context (When Entering Folder)
1. Read `.agent-context.json` if it exists in the folder
2. Read `.AGENT.md` if it exists in the folder
3. Use folder-specific patterns, boundaries, and rules

### Pass 1: Plan
1. **Determine change type** (feature/api_change/security/cross_module/non_doc_change)
2. List actions
3. Identify risks
4. List files to modify (include filepaths)
5. Mark UNKNOWN items
6. Check if HITL needed
7. Create task packet if required for change type

**If HITL needed:** Create HITL → Stop → Wait
**If ADR needed:** Create ADR → Document decision

**Output:** Plan with actions, risks, files, UNKNOWNs, HITL items

### Pass 2: Change
1. Apply edits from plan
2. Follow existing patterns
3. Include filepaths (global rule)
4. Respect boundaries

**Do not proceed if:** Blockers exist, UNKNOWN unresolved, risky without HITL approval

**Output:** Code changes with filepaths

### Pass 3: Verify
1. Run tests (use manifest commands: `make lint`, `make test`, `make verify`)
2. Provide evidence (outputs, results, filepaths)
3. Update logs (trace log, agent log)
4. Check quality gates
5. Document in PR

**Output:** Evidence, updated logs, passing tests

---

## Step 4: Complete Task

1. Mark criteria `[x]` in `.repo/tasks/TODO.md`
2. Add `Completed: YYYY-MM-DD`
3. Move to `.repo/tasks/ARCHIVE.md` (prepend)
4. Promote next task from `.repo/tasks/BACKLOG.md` to `.repo/tasks/TODO.md`

---

## Creating a PR

**Read:**
- `.repo/agents/checklists/pr-review.md`
- `.repo/templates/PR_TEMPLATE.md`
- `.repo/policy/QUALITY_GATES.md`
- `.repo/policy/HITL.md`

**PR must include:**
- What changed
- Why changed
- Filepaths (all files)
- Verification evidence
- Risks (if any)
- Rollback (if risky)

---

## Rules

**Always:**
- Include filepaths (global rule)
- Link to task in `.repo/tasks/TODO.md`
- Mark UNKNOWN → Create HITL
- Show verification evidence

**Never:**
- Guess commands (use manifest or HITL)
- Skip filepaths
- Commit secrets/.env files
- Cross boundaries without ADR
- Proceed with UNKNOWN items
- Make risky changes without HITL

---

## Decision Tree: HITL Needed?

- Risky? (security/money/prod/external) → **YES** → Create HITL → Stop
- UNKNOWN? (not in docs/manifest/code) → **YES** → Mark `<UNKNOWN>` → Create HITL → Stop
- Cross boundaries? → **YES** → Requires ADR

**Full tree:** See `.repo/agents/rules.json` or `QUICK_REFERENCE.md`

---

## Troubleshooting

**TODO.md empty:** Check `.repo/tasks/BACKLOG.md` → Promote highest priority task

**manifest.yaml missing:** Mark `<UNKNOWN>` → Create HITL → Stop

**rules.json missing:** Use `QUICK_REFERENCE.md` or read `CONSTITUTION.md` + `PRINCIPLES.md`

---

## Next Steps

1. Read `.repo/tasks/TODO.md`
2. Read `.repo/repo.manifest.yaml`
3. Read `.repo/agents/rules.json` (or `QUICK_REFERENCE.md`)
4. Follow three-pass workflow above

**For context:** See `.repo/DOCUMENT_MAP.md`

---

**Note:** For structured/machine-readable format, see `AGENTS.json`
