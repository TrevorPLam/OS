# Quality Assurance Review: Command System & Entry Point

**Date:** 2026-01-23
**Reviewer:** AI Agent (Auto)
**Scope:** Command system, entry point, self-guiding documents

---

## 🔴 Critical Issues

### 1. **Command Routing Not Implemented**

**Issue:** `PROMPT.md` lists commands (`Start`, `Work`, `Review`, etc.) but there's no mechanism for the model to know which file to read.

**Current State:**
- User types "Start"
- Model doesn't know to read `AGENTS.md`
- No routing mechanism

**Impact:** Commands won't work as intended. Model needs explicit instruction or file naming convention.

**Fix Options:**
- Option A: Add instruction in PROMPT.md: "Type 'Start' then read AGENTS.md"
- Option B: Rename AGENTS.md to START.md and make it obvious
- Option C: Add routing logic in a central file

**Recommendation:** Option A - Update PROMPT.md to explicitly route commands.

---

### 2. **Duplicate AGENTS.md Files**

**Issue:** Two `AGENTS.md` files exist:
- Root `AGENTS.md` (new entry point, ~187 lines)
- `.repo/agents/AGENTS.md` (old framework doc, ~87 lines)

**Impact:** Confusion about which file to read. Potential conflicts.

**Current References:**
- `PROMPT.md` says "entry point (AGENTS.md)" - ambiguous
- `TODO.md` says "read AGENTS.md" - ambiguous
- `QUICK_REFERENCE.md` says "read AGENTS.md" - ambiguous

**Fix Options:**
- Option A: Rename root `AGENTS.md` to `START.md` or `ENTRY.md`
- Option B: Remove/archive `.repo/agents/AGENTS.md`
- Option C: Consolidate into one file

**Recommendation:** Option A - Rename root to `START.md` for clarity.

---

### 3. **Circular Dependency in Reading Order**

**Issue:** Documents reference each other in conflicting order:

- `AGENTS.md` says: "Read TODO.md FIRST"
- `TODO.md` says: "You should have already read AGENTS.md"
- `QUICK_REFERENCE.md` says: "You should have read AGENTS.md and TODO.md"

**Impact:** Model doesn't know correct reading order.

**Fix:** Make reading order explicit and consistent:
1. `AGENTS.md` (entry point) - Read first
2. `TODO.md` - Read second (as instructed by AGENTS.md)
3. `manifest.yaml` - Read third
4. `QUICK_REFERENCE.md` - Read fourth

**Recommendation:** Update TODO.md and QUICK_REFERENCE.md to not assume prior reading.

---

### 4. **Missing Command Handlers**

**Issue:** Commands listed in `PROMPT.md` but not handled:

- `Review` - No specific workflow in AGENTS.md
- `Security` - No specific workflow in AGENTS.md
- `Help` - No guidance provided

**Impact:** Commands exist but don't do anything specific.

**Fix:** Add command-specific sections to AGENTS.md or create separate entry points.

**Recommendation:** Add command routing section to AGENTS.md.

---

## 🟡 Medium Issues

### 5. **AGENTS.md Too Verbose**

**Issue:** `AGENTS.md` is ~187 lines. Could be more concise while maintaining guidance.

**Current Problems:**
- "What to Read Next" section repeats Step 1 (redundant)
- Some repetition between sections
- Could use more structure/formatting

**Impact:** Higher token cost, harder to scan.

**Fix:**
- Remove redundant "What to Read Next" section
- Consolidate repeated information
- Use better formatting (tables, lists)

**Recommendation:** Streamline to ~120-150 lines.

---

### 6. **Role Definition Incomplete**

**Issue:** `AGENTS.md` says "You are an AI coding agent" but doesn't specify:
- Capabilities (what can agent do?)
- Restrictions (what can't agent do?)
- Role type (primary/secondary/reviewer?)

**Impact:** Agent doesn't know its scope of authority.

**Fix:** Add role section or reference `.repo/agents/roles/primary.md`.

**Recommendation:** Add brief role definition with link to full role docs.

---

### 7. **Missing Error Handling**

**Issue:** No guidance for:
- What if TODO.md is empty?
- What if no task exists?
- What if manifest.yaml is missing?
- What if QUICK_REFERENCE.md is missing?

**Impact:** Model may get stuck or make incorrect assumptions.

**Fix:** Add error handling section to AGENTS.md.

**Recommendation:** Add "Troubleshooting" section.

---

### 8. **Token Cost Not Optimized**

**Issue:** `AGENTS.md` is now the entry point but is ~187 lines (~400-500 tokens).

**Current Flow:**
- AGENTS.md: ~500 tokens
- TODO.md: ~100 tokens
- manifest.yaml: ~150 tokens
- QUICK_REFERENCE.md: ~500 tokens
- **Total: ~1250 tokens** (vs target of ~650-750)

**Impact:** Higher token usage than intended.

**Fix Options:**
- Option A: Make AGENTS.md more concise
- Option B: Use compact format for QUICK_REFERENCE
- Option C: Accept higher cost for better guidance

**Recommendation:** Option B - Use `rules-compact.md` instead of QUICK_REFERENCE.md in entry point.

---

## 🟢 Minor Issues

### 9. **Inconsistent File References**

**Issue:** Some files use relative paths, some use absolute:
- `agents/tasks/TODO.md` (relative)
- `.repo/repo.manifest.yaml` (absolute from root)
- `.repo/agents/QUICK_REFERENCE.md` (absolute)

**Impact:** Minor confusion, but works.

**Fix:** Standardize to absolute paths from root.

**Recommendation:** Low priority, but good for consistency.

---

### 10. **Missing Command Examples**

**Issue:** `PROMPT.md` shows commands but no examples of actual usage.

**Impact:** User might not understand how to use commands.

**Fix:** Add usage examples.

**Recommendation:** Add "Example Usage" section.

---

### 11. **Old Prompt Template Still Exists**

**Issue:** `.repo/AGENT_PROMPT_TEMPLATE.md` still has old long prompts.

**Impact:** Confusion - which to use?

**Fix:** Update or archive old template.

**Recommendation:** Update to reference new command system.

---

## ✅ What's Working Well

1. **Self-Guiding Structure** - Documents do guide the model
2. **Clear Workflow** - Three-pass workflow is well-defined
3. **Decision Trees** - HITL decision tree is clear
4. **Token Optimization** - Multiple formats available
5. **Role Definition** - Basic role is defined

---

## 📊 Priority Fixes

### P0 (Critical - Fix Now)

1. **Fix Command Routing** - Add explicit routing in PROMPT.md
2. **Resolve Duplicate AGENTS.md** - Rename or consolidate
3. **Fix Circular Dependency** - Clarify reading order
4. **Add Missing Command Handlers** - Implement Review/Security/Help

### P1 (Important - Fix Soon)

5. **Streamline AGENTS.md** - Reduce verbosity, remove redundancy
6. **Add Role Definition** - Include capabilities/restrictions
7. **Add Error Handling** - Handle edge cases

### P2 (Nice to Have)

8. **Optimize Token Cost** - Use compact format where possible
9. **Standardize File References** - Consistent path format
10. **Update Old Templates** - Archive or update old prompt templates

---

## 🎯 Recommendations

### Immediate Actions

1. **Rename root `AGENTS.md` to `START.md`**
   - Clearer purpose
   - Avoids conflict with `.repo/agents/AGENTS.md`
   - Makes entry point obvious

2. **Update PROMPT.md with explicit routing:**
   ```
   Start → Read START.md
   Work → Read START.md
   Review → Read START.md (PR section)
   ```

3. **Fix reading order in documents:**
   - START.md: "Read this first"
   - TODO.md: "Read after START.md"
   - QUICK_REFERENCE.md: "Read after START.md and TODO.md"

4. **Add command routing section to START.md:**
   - Handle different commands
   - Route to appropriate sections

### Short-Term Improvements

5. **Streamline START.md:**
   - Remove redundant sections
   - Use compact format references
   - Better structure

6. **Add role section:**
   - Brief capabilities
   - Link to full role docs
   - Clear restrictions

7. **Add error handling:**
   - Empty TODO.md
   - Missing files
   - Edge cases

---

## 📈 Quality Metrics

| Aspect | Current | Target | Status |
|--------|---------|--------|--------|
| **Command Routing** | ❌ Not implemented | ✅ Explicit | 🔴 Critical |
| **File Conflicts** | ❌ Duplicate files | ✅ Single source | 🔴 Critical |
| **Reading Order** | ⚠️ Circular | ✅ Linear | 🔴 Critical |
| **Command Handlers** | ⚠️ Partial | ✅ Complete | 🔴 Critical |
| **Document Length** | ⚠️ 187 lines | ✅ 120-150 | 🟡 Medium |
| **Role Definition** | ⚠️ Basic | ✅ Complete | 🟡 Medium |
| **Error Handling** | ❌ Missing | ✅ Present | 🟡 Medium |
| **Token Optimization** | ⚠️ ~1250 tokens | ✅ ~750 tokens | 🟡 Medium |

**Overall Quality:** ⚠️ **Good foundation, needs fixes**

---

## 🔧 Proposed Fixes

See separate implementation plan for detailed fixes.

---

**End of Quality Assurance Review**
