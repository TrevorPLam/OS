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

### [TASK-015] Refactor Page Components to Use React Query Hooks (Phase 1: Core Pages)
- **Priority:** P0
- **Status:** In Progress
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 0.3-0.4, all page components use anti-pattern (useState + useEffect + direct API calls). Only 2 pages use React Query correctly. This blocks production readiness.

#### Acceptance Criteria
- [ ] Refactor `frontend/src/pages/Clients.tsx` to use React Query hooks
- [ ] Refactor `frontend/src/pages/Login.tsx` to use React Query hooks
- [ ] Refactor `frontend/src/pages/Register.tsx` to use React Query hooks
- [ ] Remove all `useState` + `useEffect` + direct API call patterns
- [ ] Remove manual loading states (use React Query `isLoading`)
- [ ] Replace `console.error` with proper error handling
- [ ] Verify pages work correctly with new hooks

#### Notes
- Per ANALYSIS.md Section 0.3: Clients.tsx has 4 direct API calls, 5 useState hooks
- Per ANALYSIS.md Section 0.10: Login.tsx needs React Hook Form (separate task)
- Reference: `frontend/src/pages/WorkflowBuilder.tsx` for correct pattern
- Estimated: 8-10 hours for core pages
- Files: `frontend/src/pages/Clients.tsx`, `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx`
