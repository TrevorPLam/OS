# Entry Point System Design

**Goal:** One-three word prompts → Self-guiding entry point → Everything else

---

## Command Prompts (1-3 Words)

| Command | Entry Point | Purpose |
|---------|-------------|---------|
| `Start` | `AGENTS.md` | Begin work on current task |
| `Work` | `AGENTS.md` | Same as Start |
| `Task` | `AGENTS.md` | Work on current task |
| `Review` | `AGENTS.md` → PR workflow | Review/create PR |
| `Security` | `AGENTS.md` → Security workflow | Security-related work |
| `Help` | `AGENTS.md` | Get guidance |

---

## Entry Point Document Structure

**File:** `AGENTS.md` (or create `START.md`)

**Must contain:**
1. **Role Definition** - What is the agent's role?
2. **Initial Reading** - What to read first (TODO, manifest, QUICK_REFERENCE)
3. **Workflow** - Three-pass workflow explained
4. **Context** - How to determine context (security, boundaries, etc.)
5. **Next Steps** - Clear guidance on what to do next
6. **Self-Guiding** - Documents should guide the model, not require prompts

---

## Current State Analysis

**Current `AGENTS.md`:**
- ✅ Has initial reading list
- ✅ Has workflow rules
- ✅ Has conditional reading
- ❌ Doesn't define role explicitly
- ❌ Doesn't guide model through workflow step-by-step
- ❌ Requires user to know what to do

**Needs:**
- Role definition at top
- Step-by-step workflow guidance
- Self-guiding instructions
- Clear "what to do next" at each stage

---

## Proposed Solution

### 1. Create Self-Guiding Entry Point

**`AGENTS.md` should:**
- Start with role definition
- Provide step-by-step workflow
- Guide model through each stage
- Include "what to read next" at each step
- Be self-contained for initial work

### 2. Command Mapping

**Simple commands route to entry point:**
- `Start` → Read `AGENTS.md`
- `Work` → Read `AGENTS.md`
- `Task` → Read `AGENTS.md`

**Entry point then guides to:**
- TODO.md (task)
- manifest.yaml (commands)
- QUICK_REFERENCE.md (rules)
- Workflow steps

### 3. Self-Guiding Documents

**Each document should:**
- Tell model what it is
- Tell model when to read it
- Tell model what to do next
- Include role/context information
- Guide workflow progression

---

## Implementation Plan

1. **Enhance `AGENTS.md`** - Add role, step-by-step guidance
2. **Enhance `TODO.md`** - Add workflow guidance
3. **Enhance `QUICK_REFERENCE.md`** - Add "what to do next"
4. **Create command reference** - Simple 1-3 word commands

---

**Next:** Implement the enhanced entry point system.
