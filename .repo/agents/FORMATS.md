# Agent Rules Formats

**Purpose:** Multiple formats for different use cases - machine-readable, compact, and comprehensive.

---

## Available Formats

### 1. `rules.json` - Machine-Readable Format

**Purpose:** Structured JSON for programmatic access, tooling, and automation

**Use Cases:**
- Agent tooling that needs to parse rules programmatically
- Validation scripts
- Rule checking automation
- Generating documentation from structured data

**Structure:**
- JSON Schema compliant
- Hierarchical organization
- All rules with source references
- Workflows as structured data
- Commands, tech stack, code patterns

**Token Cost:** ~300-400 tokens

**Example Usage:**
```python
import json
with open('.repo/agents/rules.json') as f:
    rules = json.load(f)
    if change_type == 'security':
        triggers = rules['security']['triggers']
```

---

### 2. `rules-compact.md` - Ultra-Compact Format

**Purpose:** Minimal token usage while preserving all essential rules

**Use Cases:**
- Quick rule lookup when context is already loaded
- Token-constrained environments
- Quick reference during work
- Mobile/limited context scenarios

**Features:**
- ~70% smaller than QUICK_REFERENCE.md
- All essential rules preserved
- Abbreviated but clear
- References full QUICK_REFERENCE.md for context

**Token Cost:** ~150-200 tokens

**Trade-offs:**
- Less explanatory text
- Assumes some context already loaded
- Best for agents familiar with framework

---

### 3. `QUICK_REFERENCE.md` - Comprehensive Format

**Purpose:** Complete reference with all essential rules and context

**Use Cases:**
- First-time agent onboarding
- When full context is needed
- Reference for edge cases
- Human review

**Features:**
- All 8 Constitutional Articles (detailed)
- All 25 Principles (listed)
- Complete decision trees
- Full explanations
- Examples and references

**Token Cost:** ~400-500 tokens

**Best For:** Primary reference document

---

## Format Comparison

| Format | Tokens | Authority | Clarity | Machine-Readable | Use Case |
|--------|--------|-----------|---------|------------------|----------|
| `rules.json` | 300-400 | ✅ Full | ✅ Structured | ✅ Yes | Tooling, automation |
| `rules-compact.md` | 150-200 | ✅ Full | ✅ Clear | ❌ No | Quick lookup, token-constrained |
| `QUICK_REFERENCE.md` | 400-500 | ✅ Full | ✅ Excellent | ❌ No | Primary reference, onboarding |

---

## When to Use Which Format

### Use `rules.json` when:
- Building tooling/automation
- Need programmatic rule access
- Validating against rules
- Generating documentation
- Integrating with other systems

### Use `rules-compact.md` when:
- Token budget is tight
- Quick rule lookup needed
- Context already loaded
- Mobile/limited context
- Familiar with framework

### Use `QUICK_REFERENCE.md` when:
- First-time onboarding
- Need full explanations
- Encountering edge cases
- Human review needed
- Primary reference

---

## Token Optimization Strategy

**Recommended Approach:**

1. **Start with:** `rules-compact.md` (~200 tokens)
2. **If insufficient:** Load `QUICK_REFERENCE.md` (~400-500 tokens)
3. **For tooling:** Use `rules.json` (~300-400 tokens)

**Total Savings:**
- Using compact: ~200 tokens vs ~500 tokens = 60% savings
- Using JSON: ~300 tokens vs ~500 tokens = 40% savings
- Both maintain full authority and clarity

---

## Format Maintenance

**Source of Truth:** `QUICK_REFERENCE.md`

**Sync Strategy:**
- `rules-compact.md` - Manually maintained, extract from QUICK_REFERENCE
- `rules.json` - Manually maintained, structured version of QUICK_REFERENCE

**Future:** Auto-generate compact and JSON from QUICK_REFERENCE.md

---

## Authority & Clarity

**All formats maintain:**
- ✅ Full authority (all rules included)
- ✅ Clear structure (easy to understand)
- ✅ Source references (traceable to origin)
- ✅ Complete coverage (nothing missing)

**Differences:**
- **Compact:** Less explanation, same rules
- **JSON:** Structured format, same rules
- **QUICK_REFERENCE:** Full explanation, same rules

**No information loss** - only format and verbosity differ.

---

**End of Formats Guide**
