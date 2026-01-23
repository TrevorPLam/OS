# Token Optimization Analysis: JSON vs Markdown

**Date:** 2026-01-23
**Purpose:** Determine if additional JSON files would optimize token usage and context efficiency

---

## Current State Analysis

### Current Agent Reading Pattern

**Startup (Required):**
1. `AGENTS.json` or `AGENT.md` - Entry point (~169 lines, ~300 tokens)
2. `.repo/tasks/TODO.md` - Current task (~78 lines, ~100 tokens)
3. `.repo/repo.manifest.yaml` - Commands (~54 lines, ~150 tokens)
4. `.repo/agents/QUICK_REFERENCE.md` - Rules (~270 lines, ~400-500 tokens)

**Total Startup:** ~650-750 tokens

### Existing JSON Files

1. **`AGENTS.json`** - Entry point, workflow routing (~169 lines, ~300 tokens)
2. **`.repo/agents/rules.json`** - Full rules (~240 lines, ~400 tokens)
3. **`.repo/templates/AGENT_TRACE_SCHEMA.json`** - Trace log schema (~14 lines)

### Existing Compact Formats

1. **`.repo/agents/rules-compact.md`** - Ultra-compact rules (~110 lines, ~150-200 tokens)

---

## Token Usage Breakdown

### TODO.md Analysis

**Current Structure:**
- ~30 lines of instructions/metadata
- ~48 lines of actual task content
- **Essential:** Task ID, priority, status, criteria, notes
- **Non-essential for startup:** Workflow instructions, format reference

**Token Cost:** ~100 tokens (but ~40% is instructional, not task data)

### QUICK_REFERENCE.md Analysis

**Current Structure:**
- ~270 lines total
- Decision trees, constitution, principles, workflows, commands, etc.
- **Essential:** Decision trees, critical rules, workflows
- **Non-essential for startup:** Full command list, full artifact table, full examples

**Token Cost:** ~400-500 tokens

**Key Insight:** Most agents only need decision trees + critical rules at startup. Full reference can be loaded conditionally.

---

## Optimization Opportunities

### 1. **TASK.json** - Minimal Task Data

**Purpose:** Extract just the task data, separate from instructions.

**Current TODO.md:**
```markdown
# 🎯 Current Task
[30 lines of instructions]
### [TASK-001] Title
- Priority: P0
- Status: In Progress
- Created: 2026-01-23
- Context: ...
#### Acceptance Criteria
- [ ] Criterion 1
#### Notes
- Note 1
```

**Proposed TASK.json:**
```json
{
  "id": "TASK-001",
  "title": "Refine AGENTS.md to Be Concise & Effective",
  "priority": "P0",
  "status": "In Progress",
  "created": "2026-01-23",
  "context": "Current AGENTS.md is 22 lines...",
  "acceptance_criteria": [
    "Include all six core areas...",
    "Add specific tech stack..."
  ],
  "notes": ["One real code snippet beats...", "Tools: Cursor, Codex..."]
}
```

**Token Savings:** ~60 tokens (from ~100 to ~40)
- Instructions stay in TODO.md (read only when needed)
- Task data is structured and minimal

**Trade-off:**
- ✅ More machine-readable
- ✅ Easier to parse/validate
- ✅ Smaller token footprint
- ❌ Requires maintaining both formats
- ❌ Less human-readable

**Recommendation:** ⚠️ **MAYBE** - Only if we want programmatic task access. Markdown is fine for human+agent readability.

---

### 2. **AGENT_START.json** - Ultra-Minimal Entry Point

**Purpose:** Absolute minimum to start work (just reading order + decision tree).

**Current AGENTS.json:**
- 169 lines
- Contains: routing, reading order, context determination, full workflow, task completion, PR creation, rules, decision trees, troubleshooting

**Proposed AGENT_START.json:**
```json
{
  "read_order": [
    ".repo/tasks/TODO.md",
    ".repo/repo.manifest.yaml",
    ".repo/agents/RULES_MIN.json"
  ],
  "decision_tree": {
    "risky": ["security", "money", "production", "external"] → "read SECURITY_BASELINE.md + create HITL",
    "unknown": ["not_in_docs", "not_in_manifest", "not_in_code"] → "mark UNKNOWN + create HITL + stop",
    "cross_boundaries": true → "read BOUNDARIES.md + create ADR"
  },
  "workflow": "three_pass",
  "workflow_ref": ".repo/agents/rules.json#workflows.three_pass"
}
```

**Token Savings:** ~200 tokens (from ~300 to ~100)

**Trade-off:**
- ✅ Ultra-minimal startup
- ✅ References full details elsewhere
- ❌ Requires loading multiple files
- ❌ Less self-contained

**Recommendation:** ❌ **NO** - AGENTS.json is already compact and self-contained. Splitting adds complexity without significant benefit.

---

### 3. **RULES_MIN.json** - Minimal Rules (Decision Trees Only)

**Purpose:** Just decision trees + critical rules, not full reference.

**Current QUICK_REFERENCE.md:**
- ~270 lines, ~400-500 tokens
- Contains: decision trees, constitution, principles, workflows, commands, tech stack, patterns, etc.

**Proposed RULES_MIN.json:**
```json
{
  "decision_tree": {
    "hitl_needed": {
      "risky": ["security", "money", "production", "external"] → "create_hitl_stop",
      "unknown": ["not_in_docs", "not_in_manifest", "not_in_code"] → "mark_unknown_create_hitl_stop",
      "cross_boundaries": true → "requires_adr"
    }
  },
  "critical_rules": {
    "always": ["filepaths", "link_to_task", "unknown_to_hitl", "three_pass"],
    "never": ["guess_commands", "skip_filepaths", "commit_secrets", "cross_boundaries_without_adr"]
  },
  "workflow": {
    "three_pass": {
      "pass1": ["list_actions", "identify_risks", "list_files", "mark_unknowns"],
      "pass2": ["apply_edits", "follow_patterns", "include_filepaths"],
      "pass3": ["run_tests", "provide_evidence", "update_logs", "document_in_pr"]
    }
  },
  "full_ref": ".repo/agents/QUICK_REFERENCE.md"
}
```

**Token Savings:** ~300 tokens (from ~400-500 to ~100-200)

**Trade-off:**
- ✅ Minimal startup
- ✅ Load full reference only when needed
- ❌ May need to load full reference anyway for context
- ❌ Less self-contained

**Recommendation:** ⚠️ **MAYBE** - Only if agents consistently need just decision trees. Most agents need full context anyway.

---

### 4. **WORKFLOW.json** - Stage-Specific Context

**Purpose:** Load only what's needed for current workflow stage.

**Concept:** Instead of loading everything upfront, load context per stage:
- **Stage 1 (Startup):** Just reading order + decision tree
- **Stage 2 (Planning):** Decision tree + risk triggers + workflow steps
- **Stage 3 (Execution):** Patterns + boundaries + filepath rules
- **Stage 4 (Verification):** Quality gates + artifact requirements

**Token Savings:** ~200-300 tokens (load ~300 tokens per stage vs ~750 upfront)

**Trade-off:**
- ✅ Load only what's needed
- ✅ Better token efficiency
- ❌ Requires multiple file reads
- ❌ More complex workflow
- ❌ May need to re-read context

**Recommendation:** ❌ **NO** - Current approach is simpler. Agents benefit from having full context upfront.

---

## Analysis: What Information is Truly Essential?

### At Startup (Before Any Work)

**Essential:**
1. What task to work on (task ID, title, criteria)
2. What commands to use (manifest)
3. Decision tree (when to HITL, when to ADR)
4. Critical rules (always/never)

**Non-Essential (Can Load Conditionally):**
1. Full workflow details (can reference when needed)
2. Full command list (can reference when needed)
3. Full artifact requirements (can reference when needed)
4. Tech stack details (can reference when needed)
5. Code patterns (can reference when needed)

### Current vs. Optimal

**Current Startup:**
- TODO.md: 100 tokens (40% instructions, 60% task)
- manifest.yaml: 150 tokens (all essential)
- QUICK_REFERENCE.md: 400-500 tokens (30% essential, 70% reference)

**Optimal Startup (if we optimize):**
- TASK.json: 40 tokens (just task data)
- manifest.yaml: 150 tokens (unchanged)
- RULES_MIN.json: 150 tokens (just decision tree + critical rules)
- **Total: ~340 tokens** (vs ~650-750 currently)

**Savings:** ~310-410 tokens (48-55% reduction)

---

## Recommendations

### ✅ **DO Create:**

1. **`TASK.json`** (Optional Enhancement)
   - **Purpose:** Machine-readable task data
   - **Benefit:** Easier parsing, validation, tooling
   - **Cost:** Maintain both formats (or generate JSON from markdown)
   - **Priority:** Low (nice to have, not critical)

### ❌ **DON'T Create:**

1. **`AGENT_START.json`** - AGENTS.json is already optimal
2. **`WORKFLOW.json`** - Adds complexity without significant benefit
3. **`RULES_MIN.json`** - QUICK_REFERENCE.md is already well-optimized

### ⚠️ **CONSIDER:**

1. **Extract instructions from TODO.md**
   - Move workflow instructions to separate file
   - TODO.md becomes just task data
   - **Savings:** ~40 tokens per startup
   - **Priority:** Low (marginal benefit)

2. **Create task JSON schema**
   - For validation/automation
   - Not for agent reading (keep markdown for readability)
   - **Priority:** Low (tooling enhancement)

---

## Final Verdict

### Current System is Already Well-Optimized

**Evidence:**
- Startup cost: ~650-750 tokens (well under 1000 token target)
- QUICK_REFERENCE.md contains all essential rules
- Conditional reading pattern is clear
- Token optimization strategy already documented

### Additional JSON Files Would:

**Pros:**
- Slightly smaller token footprint (~300-400 token savings possible)
- More machine-readable
- Better for tooling/automation

**Cons:**
- Adds maintenance burden (keep JSON + markdown in sync)
- Less human-readable
- More complex (multiple formats to manage)
- Marginal benefit (current system already efficient)

### Recommendation: **NO ADDITIONAL JSON FILES**

**Reasoning:**
1. **Current token usage is already optimal** (~650-750 tokens is excellent)
2. **Markdown is more readable** for both humans and agents
3. **Maintenance cost** of dual formats outweighs benefits
4. **AGENTS.json and rules.json already exist** for machine-readable needs
5. **QUICK_REFERENCE.md is well-designed** and contains all essential rules

### Exception: **TASK.json** (Optional)

If you want programmatic task access (for tooling, automation, validation), create `TASK.json` but:
- Generate it from TODO.md (don't maintain manually)
- Use for tooling, not agent reading
- Keep TODO.md as source of truth

---

## Alternative Optimization: Extract Instructions

**Better approach than new JSON files:**

Move instructional content from TODO.md to separate file:

**Current TODO.md:** ~78 lines (30 lines instructions, 48 lines task)

**Optimized:**
- `TODO.md` - Just task data (~48 lines, ~60 tokens)
- `.repo/tasks/INSTRUCTIONS.md` - Workflow instructions (read only when needed)

**Savings:** ~40 tokens per startup

**Priority:** Low (marginal benefit, but simpler than JSON)

---

## Conclusion

**Your current system is already token-optimized.** Additional JSON files would provide marginal token savings (~300-400 tokens) but add maintenance complexity and reduce readability.

**Best optimization:** Keep current structure, but consider extracting instructions from TODO.md to separate file for marginal savings.

**Token optimization is already excellent:** ~650-750 tokens startup is well below the 1000 token target and represents ~75% savings vs. loading all policy documents.

---

**End of Analysis**
