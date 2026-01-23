# Token Optimization Strategy

**Purpose:** Minimize token usage by implementing smart, conditional document references.

---

## Problem Statement

**Before Optimization:**
- Agents were loading all policy documents upfront (~3000+ tokens)
- Multiple redundant references in every document
- No clear guidance on when to read what
- Assessment documents being read unnecessarily

**After Optimization:**
- Start with 3 required documents (~650-750 tokens)
  - QUICK_REFERENCE.md contains ALL essential rules (~400-500 tokens)
  - This replaces need to read CONSTITUTION.md + PRINCIPLES.md upfront
- Add conditional documents only when deeper context needed
- Clear decision tree for document selection
- Assessment documents excluded from agent reading

---

## Optimization Principles

### 1. **QUICK_REFERENCE.md Contains All Essential Rules**
**CRITICAL:** QUICK_REFERENCE.md must include ALL essential rules from CONSTITUTION.md and PRINCIPLES.md so agents can operate correctly without reading full policy documents.

**What QUICK_REFERENCE.md must include:**
- All 8 Constitutional Articles (summarized)
- All critical Principles (P3, P6, P7, P10, P13, P17, P23, P25, plus global rule)
- Security triggers
- Decision trees
- Workflow rules
- Never/Always lists

**Full policy documents are for:**
- Deeper context when encountering edge cases
- Understanding full policy structure
- Reference when QUICK_REFERENCE is insufficient

### 2. **Start Minimal, Add Conditionally**
- Begin with 3 required documents (TODO.md, manifest.yaml, QUICK_REFERENCE.md)
- QUICK_REFERENCE.md has all essential rules (~400-500 tokens)
- Add full policy documents only when context requires deeper understanding
- Use decision trees to determine what to read

### 3. **Context-Based Reading**
- Security work → Read SECURITY_BASELINE.md (for detailed triggers/patterns)
- Cross-module work → Read BOUNDARIES.md (for detailed boundary rules)
- Creating PR → Read QUALITY_GATES.md (for detailed merge requirements)
- UNKNOWN situation → QUICK_REFERENCE has Article 3, but read HITL.md for process

### 4. **Never Read Assessment Documents**
- Assessment/summary documents are for humans only
- Agents should never load: `*ASSESSMENT*.md`, `*SUMMARY*.md`
- These documents are historical/analytical, not operational

### 5. **Use Examples, Not Full Templates**
- When format is unclear, read example files
- Don't read full template unless creating artifact
- Examples are smaller and more focused

### 6. **Read Specific Sections, Not Entire Documents**
- PRINCIPLES.md has 25 principles (~800 tokens)
- QUICK_REFERENCE.md extracts the critical ones
- Read full PRINCIPLES.md only for specific principle details when needed

---

## Token Budget by Workflow

| Workflow | Before | After | Savings |
|----------|--------|-------|---------|
| Starting task | ~1500 | ~700 | 53% |
| Code changes | ~2000 | ~500 | 75% |
| Security work | ~2500 | ~500 | 80% |
| Cross-module | ~2000 | ~400 | 80% |
| Creating PR | ~2500 | ~550 | 78% |
| UNKNOWN | ~2000 | ~400 | 80% |

**Average Savings:** ~75% token reduction

---

## Smart Reference Implementation

### Root AGENTS.md Pattern

**Before:**
```markdown
> **Governance**: All agents must follow `.repo/policy/CONSTITUTION.md`
> **Principles**: See `.repo/policy/PRINCIPLES.md`
> **Quality Gates**: See `.repo/policy/QUALITY_GATES.md`
> **Security**: See `.repo/policy/SECURITY_BASELINE.md`
> **HITL**: See `.repo/policy/HITL.md`
> **Boundaries**: See `.repo/policy/BOUNDARIES.md`
> **Best Practices**: See `.repo/policy/BESTPR.md`
```

**After:**
```markdown
## 🚀 Start Here: Required Reading (Always)
1. `agents/tasks/TODO.md` - Current active task
2. `.repo/repo.manifest.yaml` - Commands
3. `.repo/agents/QUICK_REFERENCE.md` - Decision tree

## 📋 Conditional Reading (Read Only When Needed)
- If security work → `.repo/policy/SECURITY_BASELINE.md`
- If crossing boundaries → `.repo/policy/BOUNDARIES.md`
- If creating PR → `.repo/policy/QUALITY_GATES.md`
```

**Token Savings:** ~70% reduction in upfront references

---

## Document Reading Patterns

### Pattern 1: Starting a Task
```
1. TODO.md (100 tokens)
2. manifest.yaml (150 tokens)
3. QUICK_REFERENCE.md (400-500 tokens) ← Contains ALL essential rules
Total: 650-750 tokens
```

**Note:** QUICK_REFERENCE.md is larger (~400-500 tokens) because it contains all essential rules from CONSTITUTION and PRINCIPLES, but this is still much smaller than reading all policy documents (~3000+ tokens).

### Pattern 2: Security Work
```
1. TODO.md (100 tokens)
2. manifest.yaml (150 tokens)
3. QUICK_REFERENCE.md (400-500 tokens) ← Has security triggers
4. SECURITY_BASELINE.md (400 tokens) ← For detailed patterns/forbidden patterns
5. HITL.md (200 tokens) ← For HITL process details
Total: 1250-1350 tokens (vs 3000+ before)
```

**Note:** QUICK_REFERENCE.md has security triggers, but SECURITY_BASELINE.md has detailed forbidden patterns and full security review process.

### Pattern 3: Cross-Module Work
```
1. TODO.md (100 tokens)
2. manifest.yaml (150 tokens)
3. QUICK_REFERENCE.md (400-500 tokens) ← Has P13, P23 (boundaries, ADR)
4. BOUNDARIES.md (300 tokens) ← For detailed boundary rules/edges
Total: 950-1050 tokens (vs 2000+ before)
```

**Note:** QUICK_REFERENCE.md has the essential boundary rules (P13, P23), but BOUNDARIES.md has detailed module structure and edge definitions.

---

## Implementation Checklist

### ✅ Completed

- [x] Created `.repo/DOCUMENT_MAP.md` - Full document inventory with conditional reading
- [x] Optimized `AGENTS.md` - Smart conditional references
- [x] Documented token budgets by workflow
- [x] Excluded assessment documents from agent reading
- [x] Created decision tree for document selection
- [x] Enhanced QUICK_REFERENCE.md to include all essential rules from CONSTITUTION and PRINCIPLES

### 🔄 To Do

- [ ] Verify QUICK_REFERENCE.md contains all essential rules (audit against CONSTITUTION + PRINCIPLES)
- [ ] Update `.repo/agents/AGENTS.md` to reference DOCUMENT_MAP
- [ ] Add token optimization notes to other key documents
- [ ] Create agent instruction to check DOCUMENT_MAP when unsure

---

## Usage Guidelines

### For Agents

1. **Always start with:** TODO.md + manifest.yaml + QUICK_REFERENCE.md
2. **Check DOCUMENT_MAP.md** when unsure what to read
3. **Add documents conditionally** based on your workflow
4. **Never read** assessment/summary documents
5. **Read specific principles** from PRINCIPLES.md, not the whole file

### For Humans

- Assessment documents are for review/analysis
- Document map helps understand what agents read when
- Token budgets help estimate context window usage

---

## Metrics

**Target Token Budgets:**
- Starting task: < 1000 tokens
- Code changes: < 800 tokens
- Security work: < 1200 tokens
- Cross-module: < 1000 tokens
- Creating PR: < 1200 tokens

**Current Performance:**
- Average workflow: ~800-900 tokens (well under targets)
- Maximum workflow: ~1350 tokens (security work)
- Savings vs. before: ~70% reduction (still significant)

**Key Insight:** QUICK_REFERENCE.md is larger (~400-500 tokens) but contains all essential rules, eliminating need to read CONSTITUTION.md (~300 tokens) + PRINCIPLES.md (~800 tokens) = ~1100 tokens saved upfront.

---

## Critical Design Decision

**QUICK_REFERENCE.md must be comprehensive enough that agents can operate correctly without reading full policy documents.**

**Trade-off:**
- QUICK_REFERENCE.md is larger (~400-500 tokens vs ~200 tokens)
- But eliminates need to read CONSTITUTION.md (~300 tokens) + PRINCIPLES.md (~800 tokens) = ~1100 tokens saved
- Net savings: ~600-700 tokens per workflow
- Agents have all essential rules in one place

**If QUICK_REFERENCE.md is missing essential rules:**
- Agents will make mistakes
- Agents will need to read full policy documents anyway
- Token optimization fails

**Solution:** QUICK_REFERENCE.md must be audited to ensure it contains all essential rules from CONSTITUTION.md and PRINCIPLES.md.

---

## Machine-Readable Format

**Created:** `.repo/agents/rules.json` - Structured JSON format for programmatic access

**Benefits:**
- Easy to parse and query
- Can be loaded into agent context programmatically
- Structured data for tooling/automation
- Version-controlled schema

**Usage:**
- Agents can load JSON for structured rule lookup
- Tooling can validate against schema
- Can generate documentation from JSON

## Compact Format

**Created:** `.repo/agents/rules-compact.md` - Ultra-compact markdown (~200 tokens)

**Benefits:**
- ~70% smaller than QUICK_REFERENCE.md
- All essential rules preserved
- Quick reference for agents
- Maintains authority and clarity

**Trade-off:**
- Less explanatory text
- References full QUICK_REFERENCE.md for context
- Best for agents with context already loaded

## Format Comparison

| Format | Tokens | Use Case |
|--------|--------|----------|
| QUICK_REFERENCE.md | ~400-500 | Comprehensive reference |
| rules-compact.md | ~150-200 | Ultra-quick lookup |
| rules.json | ~300-400 | Programmatic access |

**Recommendation:** Use compact.md for quick lookups, QUICK_REFERENCE.md for full context, rules.json for tooling.

---

## Future Optimizations

1. **Template Fragmentation** - Split large templates into smaller, focused sections
2. **Principle Index** - Create index of principles by topic (read specific ones)
3. **Example Library** - Expand examples, reduce need for full templates
4. **Context Caching** - Document what context persists across workflows
5. **Workflow Templates** - Pre-defined document sets for common workflows
6. **QUICK_REFERENCE Audit** - Periodic review to ensure all essential rules are included
7. **JSON Schema Validation** - Validate rules.json against schema
8. **Auto-generation** - Generate compact.md and rules.json from QUICK_REFERENCE.md

---

**End of Token Optimization Strategy**
