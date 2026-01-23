# Agent Optimization Proposal - Repository-Wide

**Date:** 2026-01-23
**Purpose:** Propose optimizations to speed up agent interactions with the entire repository
**Scope:** Folder-level context files, quick references, logging, and other agent-friendly enhancements

---

## Executive Summary

To speed up agent interactions beyond `.repo/`, we propose:

1. **Folder-level JSON context files** (`.agent-context.json`) - Machine-readable folder metadata
2. **Agent-optimized quick reference files** (`.AGENT.md`) - Token-optimized folder guides
3. **Pattern libraries** - Code patterns documented at folder level
4. **Agent interaction logging** - Track what agents do and where they struggle
5. **Smart indexing** - JSON indexes of folder contents for fast lookup
6. **Boundary markers** - Clear boundary documentation at folder level
7. **Common tasks documentation** - Frequent operations at folder level

---

## 1. Folder-Level JSON Context Files

### Concept

Each major folder gets a `.agent-context.json` file that provides machine-readable metadata about the folder. This allows agents to quickly understand:
- What the folder contains
- What agents can/cannot do
- Common patterns
- Dependencies
- Boundaries
- Quick links

### Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "version": "1.0.0",
  "type": "folder_context",
  "folder": {
    "path": "backend/modules/clients",
    "purpose": "Client management module with firm-scoped multi-tenancy",
    "layer": "domain",
    "depends_on": ["backend/modules/core", "backend/modules/firm"],
    "used_by": ["backend/api/clients", "frontend/src/api/clients.ts"]
  },
  "agent_rules": {
    "can_do": [
      "Create new models with FirmScopedMixin",
      "Add serializers for API",
      "Create viewsets with FirmScopedMixin",
      "Add migrations for schema changes"
    ],
    "cannot_do": [
      "Import from other modules without ADR",
      "Break firm-scoping",
      "Depend on business modules (only core/firm allowed)"
    ],
    "requires_hitl": [
      "Schema changes affecting other modules",
      "Breaking API changes",
      "Security-related changes"
    ]
  },
  "patterns": {
    "model": "class Client(FirmScopedMixin, models.Model):",
    "viewset": "class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):",
    "serializer": "class ClientSerializer(serializers.ModelSerializer):"
  },
  "boundaries": {
    "can_import_from": ["backend/modules/core", "backend/modules/firm"],
    "cannot_import_from": ["backend/modules/crm", "backend/modules/finance"],
    "cross_module_requires_adr": true
  },
  "quick_links": {
    "guide": "backend/modules/clients/.AGENT.md",
    "index": "backend/modules/clients/INDEX.md",
    "policy": ".repo/policy/BOUNDARIES.md",
    "best_practices": ".repo/policy/BESTPR.md"
  },
  "common_tasks": [
    {
      "task": "Add new client field",
      "steps": [
        "1. Add field to models.py",
        "2. Create migration: python manage.py makemigrations clients",
        "3. Update serializer",
        "4. Update tests"
      ],
      "files": ["models.py", "serializers.py", "migrations/"]
    }
  ],
  "metrics": {
    "files_count": 47,
    "last_modified": "2026-01-15",
    "test_coverage": 0.85
  }
}
```

### Benefits

- **Fast lookup** - Agents can read JSON instead of parsing markdown
- **Machine-readable** - Easy to validate and process
- **Structured** - Consistent format across all folders
- **Comprehensive** - All context in one place

### Implementation

- Create `.agent-context.json` in:
  - `backend/`
  - `frontend/`
  - `backend/modules/*/` (each module)
  - `backend/api/*/` (each API domain)
  - `frontend/src/api/` (API clients)
  - `frontend/src/components/` (components)
  - `tests/` (test organization)
  - `docs/` (documentation structure)

---

## 2. Agent-Optimized Quick Reference Files

### Concept

Each folder gets a `.AGENT.md` file (token-optimized, < 200 lines) that provides:
- Quick "what can I do here" guide
- Common patterns (code examples)
- Boundary rules
- Common tasks
- Links to full docs

### Structure

```markdown
# Clients Module - Agent Quick Reference

**Folder:** `backend/modules/clients/`
**Purpose:** Client management with firm-scoped multi-tenancy
**Layer:** Domain

## Quick Rules

✅ **Can Do:**
- Create models with `FirmScopedMixin`
- Add serializers, viewsets, URLs
- Add migrations

❌ **Cannot Do:**
- Import from other modules (requires ADR)
- Break firm-scoping

## Patterns

**Model:**
```python
class Client(FirmScopedMixin, models.Model):
    firm = models.ForeignKey('firm.Firm', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
```

**Viewset:**
```python
class ClientViewSet(FirmScopedMixin, viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
```

## Common Tasks

**Add Field:**
1. Add to `models.py`
2. `python manage.py makemigrations clients`
3. Update serializer
4. Update tests

## Links

- Full guide: `backend/BACKEND.md`
- Policy: `.repo/policy/BOUNDARIES.md`
- JSON context: `.agent-context.json`
```

### Benefits

- **Token-efficient** - Quick read, no parsing needed
- **Example-driven** - Code patterns visible immediately
- **Actionable** - Clear "can do" / "cannot do" lists
- **Self-contained** - All context in one file

---

## 3. Pattern Libraries

### Concept

Document common code patterns at folder level so agents don't have to search the codebase.

### Structure

Create `PATTERNS.md` in each folder with:

```markdown
# Code Patterns - Clients Module

## Model Pattern
[Code example]

## Viewset Pattern
[Code example]

## Serializer Pattern
[Code example]

## Test Pattern
[Code example]

## Anti-Patterns (Don't Do This)
[Examples of what NOT to do]
```

### Benefits

- **No searching** - Patterns documented where needed
- **Consistency** - Agents follow same patterns
- **Learning** - Agents learn from examples

---

## 4. Agent Interaction Logging

### Concept

Track what agents do to identify:
- Where agents struggle
- What files are accessed most
- What patterns are used
- Where agents make mistakes

### Structure

Create `.agent-logs/` directory with:

```
.agent-logs/
├── interactions/
│   ├── 2026-01-23.jsonl
│   └── 2026-01-24.jsonl
├── metrics/
│   ├── file-access.json
│   ├── error-patterns.json
│   └── success-rates.json
└── README.md
```

### Log Format

```json
{
  "timestamp": "2026-01-23T10:30:00Z",
  "agent": "Auto",
  "action": "read_file",
  "file": "backend/modules/clients/models.py",
  "duration_ms": 45,
  "success": true,
  "context": {
    "task": "TASK-001",
    "folder": "backend/modules/clients"
  }
}
```

### Metrics to Track

- **File access frequency** - Which files are read most?
- **Error patterns** - Where do agents fail?
- **Time spent** - Which folders take longest?
- **Pattern usage** - Which patterns are used most?
- **Boundary violations** - Where do agents cross boundaries?

### Benefits

- **Identify pain points** - See where agents struggle
- **Optimize documentation** - Improve docs for frequently accessed areas
- **Measure effectiveness** - Track if optimizations help
- **Debug issues** - Understand what went wrong

---

## 5. Smart Indexing

### Concept

Create JSON indexes of folder contents for fast lookup without reading files.

### Structure

Create `INDEX.json` in each folder:

```json
{
  "folder": "backend/modules/clients",
  "files": [
    {
      "path": "models.py",
      "type": "models",
      "purpose": "Database models",
      "key_classes": ["Client", "ClientContact"],
      "line_count": 234
    },
    {
      "path": "views.py",
      "type": "views",
      "purpose": "API viewsets",
      "key_classes": ["ClientViewSet"],
      "line_count": 156
    }
  ],
  "subfolders": [
    {
      "path": "migrations/",
      "purpose": "Database migrations",
      "file_count": 12
    }
  ],
  "dependencies": {
    "imports": ["backend/modules/core", "backend/modules/firm"],
    "imported_by": ["backend/api/clients"]
  }
}
```

### Benefits

- **Fast lookup** - Find files without reading them
- **Search optimization** - Know what's in folders
- **Dependency tracking** - Understand relationships

---

## 6. Boundary Markers

### Concept

Clear boundary documentation at folder level with visual markers.

### Structure

Add to `.AGENT.md`:

```markdown
## Boundaries

**Can Import From:**
- ✅ `backend/modules/core`
- ✅ `backend/modules/firm`

**Cannot Import From:**
- ❌ `backend/modules/crm` (requires ADR)
- ❌ `backend/modules/finance` (requires ADR)

**Used By:**
- `backend/api/clients`
- `frontend/src/api/clients.ts`
```

### Benefits

- **Clear rules** - Boundaries visible immediately
- **Prevent mistakes** - Agents know what's allowed
- **ADR triggers** - Know when ADR is needed

---

## 7. Common Tasks Documentation

### Concept

Document frequent operations at folder level so agents don't have to figure them out.

### Structure

Add to `.AGENT.md`:

```markdown
## Common Tasks

### Add New Field to Model

1. Add field to `models.py`:
   ```python
   new_field = models.CharField(max_length=255)
   ```

2. Create migration:
   ```bash
   python manage.py makemigrations clients
   ```

3. Update serializer in `serializers.py`

4. Add test in `tests/test_models.py`

**Files to modify:**
- `models.py`
- `serializers.py`
- `migrations/XXXX_add_new_field.py`
- `tests/test_models.py`
```

### Benefits

- **Faster execution** - Agents know steps
- **Consistency** - Same process every time
- **Fewer mistakes** - Clear steps prevent errors

---

## Implementation Plan

### Phase 1: Core Folders (Priority 1)

1. Create `.agent-context.json` for:
   - `backend/`
   - `frontend/`
   - `backend/modules/core/`
   - `backend/modules/firm/`

2. Create `.AGENT.md` for same folders

3. Set up logging infrastructure (`.agent-logs/`)

### Phase 2: Module Folders (Priority 2)

1. Create `.agent-context.json` for all `backend/modules/*/`
2. Create `.AGENT.md` for all modules
3. Create `PATTERNS.md` for high-traffic modules

### Phase 3: API Folders (Priority 3)

1. Create `.agent-context.json` for `backend/api/*/`
2. Create `.AGENT.md` for API folders
3. Create `PATTERNS.md` for API patterns

### Phase 4: Frontend Folders (Priority 4)

1. Create `.agent-context.json` for `frontend/src/api/`
2. Create `.AGENT.md` for frontend folders
3. Create `PATTERNS.md` for component patterns

### Phase 5: Indexing & Metrics (Priority 5)

1. Generate `INDEX.json` for all folders
2. Set up metrics collection
3. Create dashboard for agent metrics

---

## File Naming Convention

- `.agent-context.json` - Machine-readable context (JSON)
- `.AGENT.md` - Human-readable quick reference (Markdown)
- `PATTERNS.md` - Code patterns (Markdown)
- `INDEX.json` - Folder index (JSON)
- `.agent-logs/` - Logging directory

---

## Benefits Summary

1. **Faster Lookups** - JSON context files are faster to parse than markdown
2. **Token Efficiency** - Quick reference files are token-optimized
3. **Pattern Discovery** - Patterns documented where needed
4. **Metrics** - Track what works and what doesn't
5. **Consistency** - Same structure across all folders
6. **Self-Contained** - Each folder has all context needed
7. **Boundary Clarity** - Clear rules prevent mistakes
8. **Task Guidance** - Common tasks documented

---

## Questions to Consider

1. **Should `.agent-context.json` be versioned?** (Yes, for tracking changes)
2. **Should logs be committed?** (No, but metrics summaries yes)
3. **How often to regenerate indexes?** (On file changes, or daily)
4. **Should patterns be auto-generated?** (Could extract from code)
5. **How to keep context files in sync?** (Validation scripts)

---

## Next Steps

1. **Create schema** for `.agent-context.json`
2. **Create template** for `.AGENT.md`
3. **Implement logging** infrastructure
4. **Generate initial** context files for core folders
5. **Test with agent** - Measure improvement
6. **Iterate** based on metrics

---

**End of Proposal**
