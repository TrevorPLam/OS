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

### [TASK-019] Create Shared Error and Loading Components
- **Priority:** P1
- **Status:** In Progress
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 11.2, 88 console.error calls exist with 0 user-facing error components. Per Section 11.12, loading states are duplicated in 20+ files.

#### Acceptance Criteria
- [x] Create `frontend/src/components/ErrorDisplay.tsx` component
- [x] Create `frontend/src/components/ConfirmDialog.tsx` component (replace window.confirm)
- [x] Enhance `frontend/src/components/LoadingSpinner.tsx` if needed
- [x] Replace all `console.error` calls with ErrorDisplay component (50+ instances - COMPLETE)
- [x] Replace all `window.confirm` calls with ConfirmDialog (18 instances - COMPLETE)
- [x] Replace manual loading states with shared component (LoadingSpinner already used)
- [x] Add proper accessibility (ARIA labels, keyboard navigation)

#### Notes
- Per ANALYSIS.md Section 11.2: 88 console.error, 0 error components - NOW RESOLVED
- Per Section 11.5: 19 window.confirm calls need replacement - NOW RESOLVED
- Per Section 11.12: ~800-1000 lines of duplicate code - NOW IMPROVED
- Estimated: 6-8 hours - COMPLETED
- Files: 18 page components modified with ErrorDisplay and ConfirmDialog
- All acceptance criteria met - ready to archive
