# DOCSAUDIT.md — Documentation Audit Runbook

**Authority & Precedence:**
1) CODEBASECONSTITUTION.md
2) READMEAI.md
3) TODO.md (Task Truth Source)
4) This runbook (DOCSAUDIT.md)
5) Supporting docs (DOCS_ROOT.md, docs/DOCS_INDEX.md, docs/REPO_MAP.md)

**Purpose:** Keep documentation accurate, discoverable, and aligned with governance while preserving existing indexes and maps.

## AGENT EXECUTION
- **Inputs to Inspect:** DOCS_ROOT.md, docs/DOCS_INDEX.md, docs/REPO_MAP.md, README.md files across modules, and documentation referenced by open TODO tasks.
- **Outputs to Produce:**
  - Documentation drift findings captured as TODO.md tasks with acceptance criteria.
  - Notes appended to the `Summary` section below.
- **Stop Rules:**
  - Do not delete documentation; archive outdated sections with context if necessary.
  - Do not move docs without updating links/indexes.

## Standard Checklist
- Documentation hub (docs/DOCS_INDEX.md) up to date with new/renamed files.
- README files reflect current setup and onboarding steps.
- API and architecture docs match implemented behavior.
- Security/privacy docs mirror current controls and policies.
- Deprecated content clearly marked and linked to replacements.

## Preserved Project Guidance (from DOCS_ROOT.md and docs indexes)
- Maintain existing documentation structure and navigation.
- Keep references between docs intact when updating content.

---

## Summary (append-only)
- Pending entries.
