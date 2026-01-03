# DOCS ROOT

Precedence: CODEBASECONSTITUTION.md → READMEAI.md → specs/* → this document.

Purpose: keep repository documentation accurate, deduped, navigable, and "single-source-of-truth" over time. This document defines what belongs in root vs /docs, how to sanitize and update docs, and how to prevent doc drift.

Primary outputs (must exist / be maintained):

* docs/DOCS_INDEX.md (the navigation hub)
* docs/REPO_MAP.md (structure overview)
* DECISIONS.md (or docs/05-decisions/) for durable decisions
* Clean, current root docs (see "Root Allowed Set")

**Note:** This repository uses `docs/05-decisions/` for Architecture Decision Records rather than a standalone DECISIONS.md file.

Secondary outputs (optional):

* docs/ARCHIVE/ for deprecated docs
* docs/CHANGELOG.md or root CHANGELOG.md (choose one location)

Hard rules:

1. One truth for each topic. No duplicated "authoritative" docs.
2. Root is for operator control docs only. Everything else lives in /docs.
3. Docs must not hold executable tasks. Tasks belong in TODO.md (see CODE_AUDIT.md).
4. Every doc must have an owner path: it is referenced by docs/DOCS_INDEX.md or it is archived/deleted.

---

## Root Allowed Set (Keep Root Small)

Root docs should be "control plane" only. Recommended root set:

Required (core operators)

* READMEAI.md (entrypoint)
* CODEBASECONSTITUTION.md (rules/standards)
* CODE_AUDIT.md (code audit pipeline)
* DOCS_ROOT.md (this doc)
* TODO.md
* TODO_COMPLETED.md
* CHANGELOG.md (optional but recommended; choose root or docs, not both)
* DECISIONS.md (optional but recommended; choose root, docs/, or docs/05-decisions/, not multiple)

**Note:** This repository uses `docs/05-decisions/` (ADR format) rather than a standalone DECISIONS.md file.

Optional root docs (only if actively used)

* RELEASE_CHECKLIST.md
* SECURITY_REVIEW.md
* DEPENDENCY_HEALTH.md
* LICENSE / SECURITY.md (if public/open source posture)
* README.md (standard GitHub landing page)
* CONTRIBUTING.md (contribution guidelines)

Everything else should live in /docs/**.

Rule:

* If a doc is not in the root allowed set, move it to /docs or archive it.

---

## Doc Header Standard (RECOMMENDED)

Every non-trivial doc should start with:

* Title
* Purpose (1–2 sentences)
* Last Updated: YYYY-MM-DD
* Owner: (role/team or "Repo Owner")
* Canonical Status: (Canonical | Supporting | Deprecated)
* Links: (DOCS_INDEX, related docs, specs, code dirs)

If adding headers is too heavy, at minimum add "Last Updated" + "Canonical Status" to canonical docs.

---

## Canonicalization Rules (Prevent Duplication)

A topic may have:

* 1 canonical doc (source-of-truth)
* any number of supporting docs (narrow scope, reference canonical)
* deprecated docs must move to docs/ARCHIVE/ and be labeled Deprecated

How to choose canonical when duplicates exist:

1. Prefer the doc that is referenced by READMEAI.md or DOCS_INDEX.md.
2. Prefer the doc with clearer scope and fewer contradictions.
3. If both contain unique value:
   * merge into the stronger doc
   * keep the other as a supporting doc or archive it

Hard rule:

* Do not leave two docs both claiming to be authoritative on the same subject.

---

## Documentation Hygiene Pipeline (Phases)

### Phase 0 — Inventory

Goal: identify what exists and what's redundant.

Steps:

1. List root docs and check against Root Allowed Set.
2. List /docs top-level categories (e.g., standards, workflows, architecture, product, ops).
3. Identify duplicates by title/subject keywords:
   * governance, workflows, standards, security, onboarding, stack, templates, prompts, repo map

Output:

* A short inventory note (can be in docs/DOCS_INDEX.md as "Structure Overview")

Gate:

* You can explain where a new reader should start and where "everything else" lives.

---

### Phase 1 — Root Sanitation

Goal: root becomes the operator control plane.

Steps:

1. For each non-allowed root doc:
   * Move to /docs/<category>/... OR docs/ARCHIVE/...
2. Update references in READMEAI.md and docs/DOCS_INDEX.md to new paths.
3. Ensure TODO.md / TODO_COMPLETED.md remain at root.

Gate:

* Root only contains allowed docs + necessary config files.

---

### Phase 2 — Build / Refresh docs/DOCS_INDEX.md

Goal: find anything quickly.

docs/DOCS_INDEX.md must include:

* "Start Here" (3–7 links max)
* "By Task" index (common intents: bootstrapping, adding a feature, running audits, releases)
* "By Topic" index (architecture, security, workflows, standards, templates/prompts)
* "By Role" (founder/operator vs dev agent)
* "Canonical Docs" section (explicit list)

Rules:

* Every doc that matters is linked from DOCS_INDEX.
* If a doc isn't linked, it should be archived or deleted.

Gate:

* A new reader can locate key docs in under 60 seconds.

---

### Phase 3 — Deduplicate + Declare Canonical Sources

Goal: remove contradictions and drift.

Steps:

1. For each duplicated topic:
   * pick canonical doc
   * merge unique content into canonical (if valuable)
   * convert the other doc into:
     * a short pointer doc (supporting), or
     * move to archive
2. Add "Canonical Status" header to canonical docs.

Gate:

* No topic has competing "authoritative" docs.

---

### Phase 4 — Remove Task Leakage from Docs

Goal: docs stop acting like TODO lists.

Steps:

1. Search docs for TODO/FIXME/TBD/TKTK/open questions.
2. For executable items:
   * create tasks in TODO.md using repo task format
   * replace in doc with: "Tracked in TODO: T-###"
3. Keep context in docs; remove only the "action directive."

Gate:

* Docs contain no executable tasks, only pointers.

---

### Phase 5 — Archive and Deprecate Safely

Goal: keep history without clutter.

Archive structure:

* docs/ARCHIVE/<YYYY>/<topic>/...

Rules:

* Archived docs must start with:
  * "DEPRECATED"
  * "Replaced by: "
  * "Reason:"
* Do not keep more than one "active" version of the same doc outside archive.

Gate:

* /docs contains only active docs; old versions are in ARCHIVE.

---

### Phase 6 — Final Consistency Checks

Goal: links, names, and structure are consistent.

Checks:

* All referenced docs exist at the linked paths.
* docs/DOCS_INDEX.md links resolve.
* docs/REPO_MAP.md matches actual folder structure.
* Root docs reference /docs locations correctly.
* No duplicate changelogs/decision logs exist in both root and docs.

Final acceptance:

* Root is clean.
* Docs are navigable.
* Canonical sources are explicit.
* Tasks are in TODO, not hidden in docs.

---

## Recommended /docs Top-Level Categories (Stable)

Use only what you need, but keep categories predictable:

* docs/start-here/ (onboarding, repo map, docs index)
* docs/workflows/ (how work happens)
* docs/standards/ (coding standards, conventions)
* docs/architecture/ (system design)
* docs/security/ (security notes/checklists)
* docs/product/ (requirements, UX notes)
* docs/templates/ (doc templates)
* docs/prompts/ (prompt libraries)
* docs/ops/ (release, incidents)
* docs/ARCHIVE/ (deprecated docs)

Rule:

* Do not create deep nesting unless there's clear volume.

---

## Minimal docs/DOCS_INDEX.md Template (must exist)

Create/ensure docs/DOCS_INDEX.md looks like:

* Start Here
* By Task
* By Topic
* Canonical Docs
* Templates / Prompts
* Archive
