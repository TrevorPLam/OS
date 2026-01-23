# Document Map: Token-Optimized Reference System

**Purpose:** Map all documents and when agents need to read them (context-based, not always).

---

## Document Inventory

### Core Policy (Always Available, Read When Needed)

| Document | When to Read | Token Cost | Priority |
|----------|--------------|-----------|----------|
| `.repo/policy/CONSTITUTION.md` | When uncertain about authority/process | Medium | High |
| `.repo/policy/PRINCIPLES.md` | When making decisions about workflow | High | Medium |
| `.repo/policy/QUALITY_GATES.md` | Before PR, when checking merge requirements | Medium | High |
| `.repo/policy/SECURITY_BASELINE.md` | When touching security/auth/money/external systems | Medium | High |
| `.repo/policy/HITL.md` | When creating HITL items or checking blockers | Low | High |
| `.repo/policy/BOUNDARIES.md` | When importing across modules/features | Low | Medium |
| `.repo/policy/BESTPR.md` | When working in repo-specific areas (backend/frontend) | High | Medium |

### Agent Framework (Context-Dependent)

| Document | When to Read | Token Cost | Priority |
|----------|--------------|-----------|----------|
| `.repo/agents/AGENTS.md` | Deep dive on agent rules (if QUICK_REFERENCE insufficient) | Medium | Low |
| `.repo/agents/QUICK_REFERENCE.md` | **START HERE** - Quick decision tree | Low | High |
| `.repo/agents/capabilities.md` | When checking what agent role can do | Low | Low |
| `.repo/agents/roles/primary.md` | When acting as primary agent | Low | Low |
| `.repo/agents/roles/secondary.md` | When acting as secondary agent | Low | Low |
| `.repo/agents/checklists/change-plan.md` | When planning a change | Low | Medium |
| `.repo/agents/checklists/pr-review.md` | When reviewing/creating PR | Low | Medium |
| `.repo/agents/prompts/pr_template.md` | When creating PR | Low | Medium |
| `.repo/agents/prompts/task_packet.md` | When creating task packets | Low | Low |

### Task Management (Workflow-Specific)

| Document | When to Read | Token Cost | Priority |
|----------|--------------|-----------|----------|
| `.repo/tasks/TODO.md` | **ALWAYS FIRST** - Current task | Low | Critical |
| `.repo/tasks/BACKLOG.md` | When promoting tasks or checking priorities | Low | Medium |
| `.repo/tasks/ARCHIVE.md` | When archiving tasks (reference only) | Low | Low |
| `.repo/tasks/README.md` | When managing tasks (first time) | Medium | Low |

### Commands & Configuration (Context-Dependent)

| Document | When to Read | Token Cost | Priority |
|----------|--------------|-----------|----------|
| `.repo/repo.manifest.yaml` | **ALWAYS** - Before running any command | Low | Critical |
| `Makefile` | When manifest unclear, checking actual commands | Medium | Low |

### Templates (Only When Creating Artifacts)

| Document | When to Read | Token Cost | Priority |
|----------|--------------|-----------|----------|
| `.repo/templates/AGENT_TRACE_SCHEMA.json` | When creating trace logs | Low | Medium |
| `.repo/templates/AGENT_LOG_TEMPLATE.md` | When creating agent logs | Low | Medium |
| `.repo/templates/PR_TEMPLATE.md` | When creating PR | Low | Medium |
| `.repo/templates/ADR_TEMPLATE.md` | When creating ADR | Low | Low |
| `.repo/templates/WAIVER_TEMPLATE.md` | When creating waiver | Low | Low |
| `.repo/templates/examples/*` | When unsure of format | Medium | Low |

### Documentation (Reference Only)

| Document | When to Read | Token Cost | Priority |
|----------|--------------|-----------|----------|
| `.repo/GOVERNANCE.md` | First-time onboarding, framework overview | High | Low |
| `.repo/INDEX.md` | Navigation reference | Low | Low |
| `docs/architecture/README.md` | When understanding system design | High | Medium |
| `README.md` | Project overview (first time) | Medium | Low |

### Archived Documents (Historical Reference Only)

**Note:** Assessment and analysis documents from the framework design phase have been archived to `docs/archive/` for historical reference. They are not part of the operational documentation and should not be read by agents.

---

## Smart Reference Trails by Workflow

### 🚀 Starting a New Task

**Required Documents (in order):**
1. `.repo/tasks/TODO.md` - **MUST READ FIRST**
2. `.repo/repo.manifest.yaml` - Check commands
3. `.repo/agents/QUICK_REFERENCE.md` - Quick decision tree
4. `.repo/policy/HITL.md` - Check for blockers

**Conditional Documents:**
- If task involves security/auth/money → `.repo/policy/SECURITY_BASELINE.md`
- If task crosses modules → `.repo/policy/BOUNDARIES.md`
- If task is backend/frontend specific → `.repo/policy/BESTPR.md`

**Token Cost:** ~500-1000 tokens (minimal)

---

### 💻 Making Code Changes

**Required Documents:**
1. `agents/tasks/TODO.md` - Current task
2. `.repo/repo.manifest.yaml` - Commands
3. `.repo/agents/checklists/change-plan.md` - Planning checklist

**Conditional Documents:**
- If crossing boundaries → `.repo/policy/BOUNDARIES.md`
- If security-related → `.repo/policy/SECURITY_BASELINE.md`
- If repo-specific → `.repo/policy/BESTPR.md`
- If uncertain → `.repo/policy/CONSTITUTION.md` (Article 3: No Guessing)

**Token Cost:** ~300-800 tokens

---

### 🔒 Security/Risky Changes

**Required Documents:**
1. `.repo/policy/SECURITY_BASELINE.md` - **MUST READ**
2. `.repo/policy/HITL.md` - Create HITL item
3. `.repo/templates/examples/example_hitl_item.md` - Format reference

**Conditional Documents:**
- If external systems → `.repo/policy/CONSTITUTION.md` (Article 8)
- If uncertain → `.repo/policy/CONSTITUTION.md` (Article 3)

**Token Cost:** ~400-600 tokens

---

### 🔀 Cross-Module/Feature Work

**Required Documents:**
1. `.repo/policy/BOUNDARIES.md` - **MUST READ**
2. `.repo/templates/ADR_TEMPLATE.md` - Create ADR

**Conditional Documents:**
- If uncertain about boundaries → `.repo/policy/PRINCIPLES.md` (P13, P23)

**Token Cost:** ~300-500 tokens

---

### 📝 Creating PR

**Required Documents:**
1. `.repo/agents/checklists/pr-review.md` - Review checklist
2. `.repo/templates/PR_TEMPLATE.md` - PR format
3. `.repo/policy/QUALITY_GATES.md` - Merge requirements
4. `.repo/policy/HITL.md` - Check HITL status

**Conditional Documents:**
- If waiverable gates fail → `.repo/templates/WAIVER_TEMPLATE.md`
- If trace log needed → `.repo/templates/AGENT_TRACE_SCHEMA.json`

**Token Cost:** ~400-700 tokens

---

### ❓ UNKNOWN Situation

**Required Documents:**
1. `.repo/policy/CONSTITUTION.md` - Article 3 (No Guessing)
2. `.repo/policy/HITL.md` - Create HITL item
3. `.repo/templates/examples/example_hitl_item.md` - Format

**Token Cost:** ~300-500 tokens

---

### 📋 Task Management

**Required Documents:**
1. `.repo/tasks/README.md` - Task workflow
2. `.repo/tasks/TODO.md` - Current task
3. `.repo/tasks/BACKLOG.md` - Next task

**Token Cost:** ~200-400 tokens

---

## Token Optimization Rules

### ✅ DO

1. **Read documents in order of priority** - Start with critical, add conditional as needed
2. **Use QUICK_REFERENCE first** - It's designed to be sufficient for most cases
3. **Read only when needed** - Don't pre-load everything
4. **Use examples** - When format is unclear, read template examples
5. **Check HITL first** - Before starting work, check for blockers

### ❌ DON'T

1. **Don't read assessment documents** - They're for humans only
2. **Don't read GOVERNANCE.md** - Too verbose, use QUICK_REFERENCE instead
3. **Don't read all policies upfront** - Read conditionally based on context
4. **Don't read PRINCIPLES.md fully** - It's 25 principles, read specific ones as needed
5. **Don't read BESTPR.md unless working in repo-specific areas**

---

## Smart Reference Pattern

**Pattern:** Conditional references based on workflow stage

```
START → TODO.md + manifest.yaml + QUICK_REFERENCE
  ↓
IF security → SECURITY_BASELINE.md
IF boundaries → BOUNDARIES.md
IF uncertain → CONSTITUTION.md (Article 3) + HITL.md
IF PR → PR_TEMPLATE + QUALITY_GATES + HITL.md
```

---

## Token Budget by Workflow

| Workflow | Min Tokens | Max Tokens | Typical |
|----------|-----------|------------|---------|
| Starting task | 500 | 1000 | 700 |
| Code changes | 300 | 800 | 500 |
| Security work | 400 | 600 | 500 |
| Cross-module | 300 | 500 | 400 |
| Creating PR | 400 | 700 | 550 |
| UNKNOWN | 300 | 500 | 400 |
| Task management | 200 | 400 | 300 |

**Target:** Keep typical workflows under 1000 tokens total.

---

## Document Size Estimates

| Document | Approx Tokens | Read Frequency |
|----------|---------------|----------------|
| QUICK_REFERENCE.md | ~200 | High (start here) |
| .repo/tasks/TODO.md | ~100 | Critical (always first) |
| repo.manifest.yaml | ~150 | Critical (before commands) |
| CONSTITUTION.md | ~300 | Medium (when uncertain) |
| PRINCIPLES.md | ~800 | Low (read specific principles) |
| SECURITY_BASELINE.md | ~400 | Medium (security work) |
| BOUNDARIES.md | ~300 | Medium (cross-module) |
| BESTPR.md | ~600 | Low (repo-specific work) |
| QUALITY_GATES.md | ~300 | High (before PR) |
| HITL.md | ~200 | High (check blockers) |

---

**End of Document Map**
