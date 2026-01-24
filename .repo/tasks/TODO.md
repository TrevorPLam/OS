# 🎯 Current Task

> **Single Active Task** — Only ONE task should be in this file at any time.

**Agent Instructions:** This is your current task. Read this file FIRST.

**Reading order (canonical per AGENTS.json):**
1. This file (`.repo/tasks/TODO.md`) - Current task - **MUST READ FIRST**
2. `.repo/repo.manifest.yaml` - Commands - **BEFORE ANY COMMAND**
3. `.repo/agents/QUICK_REFERENCE.md` - Rules - **START HERE**
4. Conditional: Policy docs as needed (security, boundaries, etc.)

---

## Your Current Task

**Do this:**
1. Read task below
2. Follow three-pass workflow from `AGENTS.json`:
   - Plan: List actions, risks, files, UNKNOWNs
   - Change: Apply edits, include filepaths
   - Verify: Run tests, show evidence, update logs
3. Mark criteria `[x]` when done
4. Archive when all criteria met

---

## Workflow Instructions

### When Task is Completed:
1. Mark the task checkbox as complete: `- [x]`
2. Add completion date: `Completed: YYYY-MM-DD`
3. Move the entire task block to `ARCHIVE.md` (prepend to top)
4. Move the highest priority task from `BACKLOG.md` to this file
5. Update the task status to `In Progress`

### Task Format Reference:
```markdown
### [TASK-XXX] Task Title
- **Priority:** P0 | P1 | P2 | P3
- **Status:** In Progress
- **Created:** YYYY-MM-DD
- **Context:** Brief description of why this task matters

#### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

#### Notes
- Any relevant context or links
```

---

## Active Task

> **Welcome!** 👋 If this section is empty, you need to promote a task from the backlog:
>
> 1. Read `.repo/tasks/BACKLOG.md` to see available tasks
> 2. Find the highest priority task (P0 → P1 → P2 → P3)
> 3. Copy the task block from `BACKLOG.md` to this file
> 4. Update status from `Pending` to `In Progress`
> 5. Remove the task from `BACKLOG.md`
>
> **Then:** Follow the three-pass workflow from `AGENTS.json` to complete the task.

---

### [TASK-018] Re-enable ESLint Rules and Fix Violations
- **Priority:** P1
- **Status:** In Progress
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 0.8, 4 critical ESLint rules are disabled, compromising type safety and code quality. Per Section 11.4, 57 instances of `any` type exist.

#### Acceptance Criteria
- [ ] Re-enable `@typescript-eslint/no-explicit-any` (start with "warn")
- [ ] Re-enable `@typescript-eslint/no-unused-vars` (start with "warn")
- [ ] Re-enable `react-hooks/exhaustive-deps` (start with "warn")
- [ ] Fix all violations across codebase (57 `any` types, unused vars, etc.)
- [ ] Gradually increase rules to "error" level
- [ ] Verify `make -C frontend lint` passes

#### Notes
- Per ANALYSIS.md Section 0.8: Lines 35-38 need rule re-enabling
- Per Section 11.4: 57 `any` types need replacement
- Estimated: 8-10 hours to fix all violations
- File: `frontend/.eslintrc.cjs` + all source files
