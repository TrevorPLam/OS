# Critical Fixes Needed

**Based on Quality Assurance Review**

---

## 🔴 P0: Critical Fixes (Do First)

### 1. Command Routing Not Implemented

**Problem:** User types "Start" but model doesn't know to read AGENTS.md

**Fix:**
```markdown
# In PROMPT.md, add explicit routing:

## Commands

Type the command, then read the specified file:

- `Start` → Read `AGENTS.md`
- `Work` → Read `AGENTS.md`
- `Task` → Read `AGENTS.md`
- `Review` → Read `AGENTS.md` (see PR section)
- `Security` → Read `AGENTS.md` (see Security section)
```

---

### 2. Duplicate AGENTS.md Files

**Problem:** Two files with same name:
- Root `AGENTS.md` (new entry point)
- `.repo/agents/AGENTS.md` (old framework)

**Fix:** Rename root `AGENTS.md` to `START.md`

**Then update all references:**
- PROMPT.md: "Read START.md"
- TODO.md: "Read START.md"
- QUICK_REFERENCE.md: "Read START.md"
- INDEX.md: Update reference

---

### 3. Circular Reading Order

**Problem:** Documents reference each other:
- AGENTS.md: "Read TODO.md FIRST"
- TODO.md: "You should have already read AGENTS.md"

**Fix:** Make order explicit and linear:

**In START.md (renamed AGENTS.md):**
```
Step 1: Read this file (START.md) - You are here
Step 2: Read agents/tasks/TODO.md
Step 3: Read .repo/repo.manifest.yaml
Step 4: Read .repo/agents/QUICK_REFERENCE.md
```

**In TODO.md:**
```
Agent Instructions: Read this AFTER reading START.md.
START.md contains your role and workflow.
```

**In QUICK_REFERENCE.md:**
```
Agent Instructions: Read this AFTER START.md and TODO.md.
This contains all essential rules.
```

---

### 4. Missing Command Handlers

**Problem:** Commands exist but no specific workflows:
- `Review` - No PR workflow
- `Security` - No security workflow
- `Help` - No help section

**Fix:** Add command routing section to START.md:

```markdown
## Command Routing

**If command was "Start", "Work", or "Task":**
→ Follow workflow below (default)

**If command was "Review":**
→ Skip to "Creating a PR" section below

**If command was "Security":**
→ Read .repo/policy/SECURITY_BASELINE.md first
→ Then follow workflow

**If command was "Help":**
→ See "What to Read Next" section below
```

---

## 🟡 P1: Important Fixes

### 5. Streamline START.md

**Problem:** ~187 lines, some redundancy

**Fix:**
- Remove "What to Read Next" section (repeats Step 1)
- Consolidate repeated information
- Use tables for better structure
- Target: 120-150 lines

---

### 6. Add Role Definition

**Problem:** Role is vague ("AI coding agent")

**Fix:** Add role section:
```markdown
## Your Role

**You are:** A primary AI coding agent

**You can:**
- Create features
- Modify existing code
- Add dependencies (with security review)
- Change API contracts (with ADR)
- Create ADRs

**You cannot:**
- Apply waivers (reviewer only)
- Update release process (release role only)

**Full role details:** See `.repo/agents/roles/primary.md`
```

---

### 7. Add Error Handling

**Problem:** No guidance for edge cases

**Fix:** Add troubleshooting section:
```markdown
## Troubleshooting

**If TODO.md is empty:**
→ Check agents/tasks/BACKLOG.md for tasks
→ Promote highest priority task to TODO.md

**If manifest.yaml is missing:**
→ Mark as <UNKNOWN>
→ Create HITL item
→ Stop work

**If QUICK_REFERENCE.md is missing:**
→ Use .repo/agents/rules-compact.md
→ Or read .repo/policy/CONSTITUTION.md and PRINCIPLES.md
```

---

## 📋 Implementation Checklist

- [ ] Rename `AGENTS.md` to `START.md`
- [ ] Update PROMPT.md with explicit routing
- [ ] Fix reading order in all documents
- [ ] Add command routing section to START.md
- [ ] Remove redundant sections from START.md
- [ ] Add role definition to START.md
- [ ] Add error handling to START.md
- [ ] Update all file references (AGENTS.md → START.md)
- [ ] Test command flow: "Start" → reads START.md → follows workflow

---

**Priority:** Fix P0 issues first, then P1 improvements.
