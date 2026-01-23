# Command System: One-Three Word Prompts

**Design:** Minimal commands → Self-guiding entry point → Everything else

---

## Commands (1-3 Words)

| Command | Entry Point | What Happens |
|---------|-------------|--------------|
| `Start` | `AGENTS.md` | Begin work on current task |
| `Work` | `AGENTS.md` | Same as Start |
| `Task` | `AGENTS.md` | Work on current task |
| `Review` | `AGENTS.md` → PR section | Review/create PR |
| `Security` | `AGENTS.md` → Security section | Security-related work |
| `Help` | `AGENTS.md` | Get guidance |

---

## How It Works

### 1. User Types Command

```
Start
```

### 2. Model Reads Entry Point

**`AGENTS.md` contains:**
- Role definition (what the agent is)
- Step-by-step workflow
- What to read next
- Context determination
- Decision trees
- Everything needed to proceed

### 3. Entry Point Guides Model

**`AGENTS.md` tells model:**
1. Read `agents/tasks/TODO.md` (task)
2. Read `.repo/repo.manifest.yaml` (commands)
3. Read `.repo/agents/QUICK_REFERENCE.md` (rules)
4. Follow three-pass workflow
5. What to do at each step

### 4. Documents Are Self-Guiding

**Each document:**
- Tells model what it is
- Tells model when to read it
- Tells model what to do next
- Contains role/context information
- Guides workflow progression

---

## Document Flow

```
User: "Start"
  ↓
Model reads: AGENTS.md (entry point)
  ↓
AGENTS.md says: "Read TODO.md, manifest.yaml, QUICK_REFERENCE.md"
  ↓
Model reads: TODO.md (task)
  ↓
TODO.md says: "Follow three-pass workflow from AGENTS.md"
  ↓
Model reads: manifest.yaml (commands)
  ↓
Model reads: QUICK_REFERENCE.md (rules)
  ↓
Model follows: Three-pass workflow from AGENTS.md
  ↓
Model completes: Task
```

---

## Key Design Principles

### 1. Entry Point Contains Everything

**`AGENTS.md` includes:**
- Role definition
- Workflow steps
- What to read
- Decision trees
- Rules summary
- Next steps

### 2. Documents Guide, Don't Require Prompts

**Each document:**
- Self-explanatory
- Tells model what to do
- References other documents
- Guides progression

### 3. Minimal User Input

**User only needs:**
- One-three word command
- Documents handle the rest

### 4. Context in Documents

**Role, context, task all in documents:**
- Role: Defined in `AGENTS.md`
- Context: Determined from task + decision trees
- Task: In `TODO.md`
- Workflow: In `AGENTS.md`

---

## Example Usage

### User Types:
```
Start
```

### Model Reads:
1. `AGENTS.md` - Entry point with role, workflow, guidance
2. `agents/tasks/TODO.md` - Current task
3. `.repo/repo.manifest.yaml` - Commands
4. `.repo/agents/QUICK_REFERENCE.md` - Rules

### Model Follows:
- Three-pass workflow from `AGENTS.md`
- Decision trees from `QUICK_REFERENCE.md`
- Task requirements from `TODO.md`

### Model Completes:
- Task according to acceptance criteria
- Archives task
- Moves to next task

---

## Benefits

1. **Minimal User Input** - Just 1-3 words
2. **Self-Guiding** - Documents guide the model
3. **No Long Prompts** - Everything in documents
4. **Clear Workflow** - Step-by-step guidance
5. **Context-Aware** - Documents contain role/context

---

## Implementation

**Enhanced Documents:**
- ✅ `AGENTS.md` - Now self-guiding entry point
- ✅ `PROMPT.md` - Simple command reference
- ✅ `agents/tasks/TODO.md` - References workflow
- ✅ `.repo/agents/QUICK_REFERENCE.md` - References entry point

**All documents now:**
- Tell model what they are
- Tell model when to read them
- Tell model what to do next
- Guide workflow progression

---

**End of Command System Guide**
