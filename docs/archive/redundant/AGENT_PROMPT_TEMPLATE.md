# Agent Prompt Template

**Use this prompt when starting work with AI models (Cursor, Claude, ChatGPT, GitHub Copilot)**

---

## Quick Start Prompt

```
I'm working in a repository with an agentic coding framework.

Before you start, read these 3 files in order:
1. agents/tasks/TODO.md - Current active task
2. .repo/repo.manifest.yaml - Commands (don't guess commands)
3. .repo/agents/QUICK_REFERENCE.md - All essential rules

Token-optimized: Only read additional documents when needed based on context (see .repo/DOCUMENT_MAP.md).

Follow the three-pass workflow: Plan → Change → Verify.
```

---

## Full Prompt (For Complex Tasks)

```
I'm working in a repository with an agentic coding framework. Follow these instructions:

**Required Reading (Start Here):**
1. Read `agents/tasks/TODO.md` - Current active task (MUST READ FIRST)
2. Read `.repo/repo.manifest.yaml` - Commands (source of truth, don't guess)
3. Read `.repo/agents/QUICK_REFERENCE.md` - All essential rules

**Token Optimization:**
- Use the smart trail pattern (see .repo/DOCUMENT_MAP.md)
- Only read additional documents when context requires it
- For quick lookups, use `.repo/agents/rules-compact.md` (~200 tokens)
- For programmatic access, use `.repo/agents/rules.json`

**Workflow:**
- Follow three-pass: Plan (actions/risks/files/UNKNOWNs) → Change (edits/patterns/filepaths) → Verify (tests/evidence/logs)
- If UNKNOWN: Mark <UNKNOWN> → Create HITL → Stop work
- If risky (security/money/prod/external): Create HITL → Stop work
- Always include filepaths in all changes (global rule)

**Key Rules:**
- Never guess commands (use manifest or HITL)
- Never skip filepaths (required everywhere)
- Never commit secrets/.env files
- Link all changes to task in agents/tasks/TODO.md
- Archive completed tasks to agents/tasks/ARCHIVE.md

Now work on the current task in agents/tasks/TODO.md.
```

---

## Minimal Prompt (For Simple Tasks)

```
Read agents/tasks/TODO.md, .repo/repo.manifest.yaml, and .repo/agents/QUICK_REFERENCE.md.

Follow three-pass workflow. Include filepaths. Link to task. No guessing commands.
```

---

## Context-Specific Prompts

### For Security Work
```
Read agents/tasks/TODO.md, .repo/repo.manifest.yaml, .repo/agents/QUICK_REFERENCE.md, and .repo/policy/SECURITY_BASELINE.md.

This touches security - create HITL item before proceeding.
```

### For Cross-Module Work
```
Read agents/tasks/TODO.md, .repo/repo.manifest.yaml, .repo/agents/QUICK_REFERENCE.md, and .repo/policy/BOUNDARIES.md.

This crosses module boundaries - ADR required per Principle 23.
```

### For Creating PR
```
Read agents/tasks/TODO.md, .repo/repo.manifest.yaml, .repo/agents/QUICK_REFERENCE.md, .repo/policy/QUALITY_GATES.md, and .repo/templates/PR_TEMPLATE.md.

Check .repo/policy/HITL.md for blocking items before creating PR.
```

---

## Mobile/Token-Constrained Prompt

```
Read agents/tasks/TODO.md, .repo/repo.manifest.yaml, and .repo/agents/rules-compact.md (~200 tokens).

Follow three-pass workflow. Include filepaths. Link to task.
```

---

## What Each Prompt Does

### Quick Start
- Gets AI started with minimal context
- Points to essential files
- Mentions token optimization

### Full Prompt
- Complete instructions
- All key rules mentioned
- Workflow guidance
- Good for complex tasks

### Minimal Prompt
- Ultra-concise
- Assumes AI knows framework
- Good for simple tasks

### Context-Specific
- Adds relevant documents for specific scenarios
- Reduces token waste
- Targeted guidance

### Mobile/Token-Constrained
- Uses compact format
- Minimal token usage
- Still has all essential rules

---

## Usage Tips

1. **Start Simple** - Use Quick Start or Minimal for most tasks
2. **Add Context** - Use context-specific prompts when needed
3. **Mobile** - Use token-constrained prompt on mobile
4. **Complex Tasks** - Use Full Prompt for complex work

---

## Example Usage

**Before starting work:**
```
[Paste Quick Start Prompt]

Work on the current task.
```

**For security work:**
```
[Paste Security Work Prompt]

Review the security implications and create HITL item.
```

**On mobile:**
```
[Paste Mobile Prompt]

What's the current task?
```

---

**Remember:** The prompt should be concise but complete. The AI will read the actual files, so you don't need to repeat everything in the prompt.
