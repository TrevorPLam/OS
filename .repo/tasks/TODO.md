# 🎯 Current Task

> **Single Active Task** — Only ONE task should be in this file at any time.

**Agent Instructions:** Read `AGENTS.json` (or `AGENTS.md`) first, then this file.

**Reading order:** 1) `AGENTS.json` → 2) This file (`TODO.md`) → 3) `.repo/repo.manifest.yaml` → 4) `.repo/agents/rules.json`

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

### [TASK-001] Refine AGENTS.md to Be Concise & Effective
- **Priority:** P0
- **Status:** In Progress
- **Created:** 2026-01-23
- **Context:** Current AGENTS.md is 22 lines. Best practice is 50-100 lines that are highly specific and example-driven, NOT verbose documentation.

#### Acceptance Criteria
- [ ] Include all six core areas: Commands, Testing, Project Structure, Code Style, Git Workflow, Boundaries
- [ ] Add specific tech stack with versions (Django 4.2 + Python 3.11 + React 18 + TypeScript)
- [ ] Include 1-2 code examples (showing patterns, not explaining them)
- [ ] Document clear boundaries (what agents must NEVER do)
- [ ] Keep total length under 100 lines

#### Notes
- "One real code snippet beats three paragraphs" — GitHub research
- Tools: Cursor, Codex mobile, Claude mobile, GitHub Copilot mobile
- Reference: https://agents.md (official spec)
