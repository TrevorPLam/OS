# Documentation Style Guide

**Purpose:** Standards for writing documentation in ConsultantPro repository, including the critical "No Hallucination" guardrails.

**Authority:** This guide implements Constitution Section 3.2 (No Undocumented Behavior) and Section 14 (PR Checklist).

---

## Core Principles

### 1. No Hallucination (Constitution 3.1, 3.2)

**CRITICAL RULE:** Every factual claim must cite evidence from the repo.

**Evidence Format:**
- File paths + line numbers: `src/config/settings.py:17-24`
- Config key/value: `Makefile:98` defines `openapi` target
- Command output: If you ran a command, show the output

**Forbidden:**
- Guessing features exist without verification
- Describing APIs/commands that don't exist
- Inventing file paths

**Required Labels:**
- **VERIFIED:** You executed a command and captured output
- **STATIC-ONLY:** You read code but didn't execute
- **UNKNOWN:** You cannot confirm it exists

**Example (Good):**
> The health check endpoint is at `/health` (evidence: P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md:41 - CONST-2, implemented in `src/config/health.py`).
>
> **Verification:** STATIC-ONLY (code confirmed but endpoint path not verified via HTTP request).

**Example (Bad):**
> The health check endpoint is at `/health` and returns JSON with database status.
>
> ❌ No evidence provided, second claim not verified.

---

### 2. Single Source of Truth

**Rule:** Link to the canonical source instead of duplicating information.

**Evidence:** Constitution Section 3.2 line 51 - "Docs must point to the authoritative source"

**Good:**
> For environment variables, see `docs/OPERATIONS.md` Section 3.1.

**Bad:**
> Set these environment variables: DJANGO_SECRET_KEY=..., POSTGRES_DB=..., [50 lines of duplication]

---

### 3. Evidence-First Writing

**When documenting a feature:**

1. **Read the code** - Find the implementation
2. **Cite the evidence** - File path + line number
3. **Mark verification level** - VERIFIED vs STATIC-ONLY vs UNKNOWN
4. **Document what you found** - Not what you think should be there

---

## Documentation Organization

### Diátaxis Framework

**Evidence:** `docs/README.md:3` - We follow the [Diátaxis framework](https://diataxis.fr/)

| Type | Purpose | Location | Tone |
|------|---------|----------|------|
| **Tutorials** | Learning by doing | `docs/01-tutorials/` | Friendly, step-by-step |
| **How-To Guides** | Solve specific problems | `docs/02-how-to/` | Direct, action-first |
| **Reference** | Look up facts | `docs/03-reference/` | Dry, precise, complete |
| **Explanation** | Understand concepts | `docs/04-explanation/` | Discursive, thoughtful |

**Rule:** Every new doc must fit into ONE of these categories.

---

## Markdown Style

### Headings

```markdown
# Top-Level Title (H1) - Only ONE per document

## Section (H2)

### Subsection (H3)

#### Sub-subsection (H4) - Avoid going deeper
```

**Rule:** Use sentence case for headings ("Environment variables" not "Environment Variables").

### Links

**Internal links** (to files in repo):
```markdown
[Link text](../path/to/file.md)
```

**Anchor links** (to heading in same doc):
```markdown
[Link text](#section-heading)
```

**External links**:
```markdown
[Link text](https://example.com)
```

**Rule:** All links must be valid. CI checks them (evidence: `.github/workflows/docs.yml:31-39` - lychee).

### Code Blocks

**Inline code:** Use \`backticks\` for commands, file names, variable names.

**Code blocks:**
````markdown
```bash
make test
```

```python
def example():
    pass
```
````

**Rule:** Always specify language for syntax highlighting.

### Evidence Citations

**Evidence block format:**
```markdown
**Evidence:** `path/to/file.py:10-20`
```

**Evidence chain:**
```markdown
**Evidence:** `README.md:55` requires Python 3.11+, confirmed by `.github/workflows/ci.yml:10` (PYTHON_VERSION: '3.11').
```

---

## File Organization

### Required Headers

Every documentation file must have:

```markdown
# Title

**Purpose:** One-sentence description

**Audience:** Who this is for (e.g., "Developers", "Operators", "Non-coder founder")

**Evidence Status:** VERIFIED / STATIC-ONLY / UNKNOWN

---

[Content here]

---

**Last Updated:** YYYY-MM-DD
**Evidence Sources:** [List of primary sources]
```

### File Naming

- **Use kebab-case:** `getting-started.md` not `Getting_Started.md`
- **Be descriptive:** `RUNBOOK_incident-response.md` not `incident.md`
- **Use prefixes for related docs:** `RUNBOOK_*.md`, `ADR-*.md`

---

## Documentation Truthfulness Checklist

**Use this checklist when writing or reviewing docs** (Constitution Section 14):

### Before Writing
- [ ] Have I read the relevant code?
- [ ] Can I cite file paths for each claim?
- [ ] Do I have evidence or am I guessing?

### While Writing
- [ ] Every command references a file path (Makefile, script, README)
- [ ] Every feature claim cites implementation (file + line)
- [ ] Every config mentions the source (settings.py, env var, etc.)
- [ ] Marked verification level (VERIFIED / STATIC-ONLY / UNKNOWN)

### Before Committing
- [ ] All internal links are valid
- [ ] All evidence citations are accurate
- [ ] No claims without evidence
- [ ] Ran `make docs-validate` or `python scripts/check_markdown_links.py`

### PR Review
- [ ] Reviewer verified at least 3 random evidence citations
- [ ] No "hallucinated" features or commands
- [ ] Documentation matches actual code behavior

---

## Common Patterns

### Documenting a Makefile Target

**Good:**
> Run tests with `make test` (evidence: `Makefile:56-75`). This runs backend tests via `make -C src test` and frontend tests via `make -C src/frontend test`, reporting PASS/FAIL for each.

**What this shows:**
- Cited the file and line range
- Described what the target does (based on reading it)
- Verification level implied (STATIC-ONLY from code reading)

---

### Documenting an Environment Variable

**Good:**
> Set `DJANGO_SECRET_KEY` (required). The application will fail to start if missing (evidence: `src/config/settings.py:19-24` raises `ValueError`).

**What this shows:**
- Named the variable
- Stated its requirement level (required vs optional)
- Cited enforcement location

---

### Documenting UNKNOWN Features

**Good:**
> **Backup Strategy:** UNKNOWN - No automated backup procedures found in repo. To verify, check for cron jobs, backup scripts in `/scripts/`, or cloud provider configs.

**What this shows:**
- Clearly labeled UNKNOWN
- Listed what evidence would be needed
- Told user how to verify

---

## Tone & Voice

### For Operators (OPERATIONS.md, TROUBLESHOOTING.md, RUNBOOKS)
- **Direct and action-first:** "Run this command" not "You might want to consider running"
- **Step-by-step numbered lists**
- **Clear failure modes:** "If X, then Y"

### For Developers (How-To Guides)
- **Assume basic knowledge**
- **Show code examples**
- **Link to references, don't repeat them**

### For Non-Coders (User Guides)
- **No jargon without explanation**
- **Screenshots where helpful**
- **Success criteria for each step**

---

## Code Documentation: Meta-commentary Standard

### What is Meta-commentary?

**Meta-commentary** is a structured docstring section that provides implementation context beyond what the code does. It appears after the main docstring description and explains:

- **Current implementation status** (complete vs partial)
- **Design rationale** and architectural decisions
- **Follow-up work** needed (with task IDs)
- **Assumptions** about external systems or state
- **Missing features** that are intentionally deferred
- **Known limitations** or edge cases

**Evidence:** Existing pattern in `src/modules/firm/audit.py:13`, `src/modules/firm/permissions.py:12`, `src/modules/core/purge.py:13`

### When to Use Meta-commentary

Use Meta-commentary when:

✅ **Incomplete by design** - Feature is partially implemented, awaiting follow-up work  
✅ **Security-sensitive** - Auth, permissions, encryption with enforcement gaps  
✅ **Multi-tenant isolation** - Firm-scoping assumptions or RLS enforcement status  
✅ **Complex state machines** - Workflow orchestration with partial states  
✅ **Integration stubs** - OAuth/webhook handlers with retry logic incomplete  
✅ **Governance models** - Tier 0-4 implementations with enforcement hooks not wired  

Do NOT use Meta-commentary for:

❌ Simple utility functions with complete implementations  
❌ Standard CRUD operations with no special considerations  
❌ Code that is self-explanatory from tests and naming  

### Meta-commentary Template

```python
"""
[Regular docstring: what the function/class does, parameters, returns]

Meta-commentary:
- Current Status: [What's implemented vs what was designed]
- Follow-up (TASK-ID): [What needs to be wired/completed, with task reference]
- Assumption: [What the code assumes about external systems/state]
- Missing: [What's intentionally deferred or not implemented]
- Limitation: [Known constraints or edge cases]
"""
```

**Rules:**
1. Start with `Meta-commentary:` on its own line
2. Use bullet points with **bold labels** (`Current Status:`, `Follow-up:`, etc.)
3. Reference task IDs (T-###, SEC-#, DOC-#) when applicable
4. Be concise - 3-5 bullets maximum
5. Update when follow-up work completes

### Examples

#### Example 1: Incomplete Enforcement

```python
class DenyContentAccessByDefault(permissions.BasePermission):
    """
    Default-deny for customer content access by platform operators.
    
    Meta-commentary:
    - Current Status: Permission class defined but not applied to all content ViewSets.
    - Follow-up (SEC-7): Wire this to Document, Message, Comment ViewSets.
    - Assumption: Break-glass sessions are checked via middleware (not yet implemented).
    - Missing: Audit logging for denied access attempts.
    """
```

#### Example 2: Integration Stub

```python
def sync_invoices_bidirectional(self, connection):
    """
    Sync invoices between internal DB and QuickBooks.
    
    Meta-commentary:
    - Current Status: Sync implemented but conflict resolution is last-write-wins.
    - Follow-up (T-036): Add manual conflict resolution UI for invoice discrepancies.
    - Assumption: Invoice numbers are unique per firm (QuickBooks enforces server-side).
    - Missing: Sync locking to prevent concurrent syncs from same connection.
    - Limitation: Only syncs invoices with status='sent'; drafts are ignored.
    """
```

#### Example 3: Design Rationale

```python
class AuditEvent(models.Model):
    """
    Immutable audit event record for compliance and security tracking.
    
    Meta-commentary:
    - Design Rationale: Records are immutable (no updates, only creates) per Tier 3 governance.
    - Current Status: Model complete; automatic event emission wired for config changes only.
    - Follow-up (T-045): Add Sentry breadcrumbs for critical audit events.
    - Assumption: Content is never logged (metadata only) per privacy-first design.
    """
```

### Maintenance Guidelines

**When to Add:**
- During code review when reviewer asks "why is this incomplete?"
- When implementing partial features that need follow-up
- When documenting security assumptions or governance gaps

**When to Update:**
- When follow-up tasks complete (change "Follow-up" to "Previously incomplete, now wired as of [date]")
- When assumptions change (document old assumption and new one)
- When limitations are resolved

**When to Remove:**
- When Meta-commentary becomes redundant with obvious implementation
- When the context is fully captured in ADRs or architecture docs
- Never remove historical context (archive to comments if needed)

---

## Anti-Patterns (DO NOT DO)

### ❌ Hallucinating Commands
```markdown
Run the backup script:
```bash
./scripts/backup.sh
```
```
**Why wrong:** You didn't verify `backup.sh` exists. Either cite it or mark UNKNOWN.

---

### ❌ Copying Without Verification
```markdown
The API supports versioning at `/api/v1/` and `/api/v2/`.
```
**Why wrong:** Did you check the code? Or are you guessing based on common patterns?

---

### ❌ Vague References
```markdown
The system uses Redis for caching.
```
**Why wrong:** Where's the evidence? Settings file? Docker compose? Or is this assumed?

---

### ❌ Missing Verification Level
```markdown
The deployment process takes 5-10 minutes.
```
**Why wrong:** Did you time it (VERIFIED) or read it somewhere (cite source) or guess (UNKNOWN)?

---

## Quality Gates

**Evidence:** `.github/workflows/docs.yml:13-40`, `docs/Makefile:15-17`

Documentation quality is enforced by CI:

1. **Structure validation:** `scripts/validate_docs_structure.py` (evidence: docs/Makefile:16)
2. **Link checking:** lychee (evidence: .github/workflows/docs.yml:31-39)
3. Markdown linting via `markdownlint` (see `.github/workflows/docs-quality.yml`)
4. Spell checking via `cspell` (see `.github/workflows/docs-quality.yml`)

**Local check:**
```bash
make docs-validate
```

---

## When to Archive Documentation

**Evidence:** `docs/ARCHIVE/README.md`

Archive a doc when:
1. It conflicts with current docs
2. It's superseded by a newer version
3. It's a historical snapshot (analysis, old roadmap)

**Process:**
1. Move to `docs/ARCHIVE/category-YYYY-MM-DD/`
2. Update `docs/ARCHIVE/README.md` with reason and replacement
3. Add archive header to the file itself

---

## Questions?

- **Constitution:** `docs/codingconstitution.md`
- **Contributing:** `CONTRIBUTING.md`
- **Diátaxis Framework:** https://diataxis.fr/

---

**Last Updated:** 2026-01-06
**Authority:** Constitution Section 3.2, 14, 15
