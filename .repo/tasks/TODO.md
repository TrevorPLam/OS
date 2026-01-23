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

### [TASK-013] Convert API Layer to React Query Hooks (Phase 1: Core APIs)
- **Priority:** P0
- **Status:** In Progress
- **Created:** 2026-01-23
- **Context:** CRITICAL pattern violation per ANALYSIS.md. All API files export plain async functions instead of React Query hooks, contradicting documented patterns in PATTERNS.md. This blocks caching, background refetching, and proper error handling.

#### Acceptance Criteria
- [ ] Convert `frontend/src/api/clients.ts` - all 13 functions to React Query hooks
- [ ] Convert `frontend/src/api/auth.ts` - all 6 functions to React Query hooks
- [ ] Export hooks: `useClients()`, `useClient(id)`, `useCreateClient()`, `useUpdateClient()`, `useDeleteClient()`, `useLogin()`, `useRegister()`, etc.
- [ ] Implement proper query invalidation on mutations
- [ ] Add TypeScript return types to all hooks
- [ ] Update PATTERNS.md if patterns need adjustment
- [ ] Verify hooks follow pattern in `frontend/src/api/PATTERNS.md`

#### Notes
- Per ANALYSIS.md Section 0.2, 1.1.1: Pattern violation affects all API files
- Reference implementation: `frontend/src/pages/WorkflowBuilder.tsx` (correct pattern)
- Estimated: 4-6 hours for core APIs
- Files: `frontend/src/api/clients.ts`, `frontend/src/api/auth.ts`
