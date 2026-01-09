# audits/code/DESIGNAUDIT.md
> Coherence audit: ensures new work fits the repo’s patterns and preserves clean boundaries.
> This audit answers: “Did we add the right thing in the right way for THIS codebase?”

## Goal
Ensure that changes:
- Preserve or improve **separation of concerns**
- Follow existing patterns and conventions (per READMEAI / constitution / AGENTS)
- Avoid unnecessary coupling
- Keep interfaces clean and stable
- Introduce new abstractions only when justified

This audit is not about personal taste — it’s about **consistency and maintainability**.

---

## Scope
Apply to:
- new modules/files
- changes that introduce new interfaces, configs, or flows
- refactors that change shape/structure

If the repo’s architectural conventions are not explicit:
- score **0 (UNKNOWN)** on relevant items
- create a TODO task to document conventions (or add an ADR)

---

## Checklist & Scoring

### 1) Pattern Consistency (CRITICAL)
**Question:** Does the change follow established repo patterns?

- 0 = Introduces a new pattern without justification
- 1 = Mostly consistent, minor deviations
- 2 = Fully consistent with existing patterns

**Evidence:**  
- point to existing similar code and how this matches it

---

### 2) Separation of Concerns (CRITICAL)
**Question:** Are responsibilities cleanly separated (no “god functions/modules”)?

- 0 = Responsibilities mixed; unclear boundaries
- 1 = Mostly separated, minor mixing
- 2 = Clean separation, clear boundaries

---

### 3) Dependency Direction & Coupling
**Question:** Are dependencies pointing in the right direction, and is coupling minimized?

- 0 = Tight coupling introduced or circular-ish relationships
- 1 = Some coupling but manageable
- 2 = Coupling minimized; dependencies sensible

**Red flags:**
- cross-layer imports
- “utility” dumping grounds
- new globals/singletons without need

---

### 4) Interface Hygiene (CRITICAL)
**Question:** Are public interfaces minimal, stable, and well-defined?

- 0 = Public surface expanded unnecessarily or breaking changes introduced
- 1 = Acceptable but could be slimmer/clearer
- 2 = Minimal, clear, stable interfaces

**Includes:**
- exported functions/classes
- CLI flags/options
- config keys
- file formats

---

### 5) Appropriate Abstractions
**Question:** Are abstractions introduced only when they pay off?

- 0 = Over-engineering or premature abstraction
- 1 = Some abstraction risk
- 2 = Abstractions are justified and helpful

**Red flags:**
- “framework inside the repo”
- generic layers with one implementation
- unnecessary indirection

---

### 6) Extensibility Without Fragility
**Question:** Is future extension possible without brittle hacks?

- 0 = Future changes likely require invasive edits
- 1 = Some fragility, but acceptable
- 2 = Extension points exist (or aren’t needed) and are clean

---

### 7) Configuration & Defaults Design
**Question:** Are defaults safe and configuration clear?

- 0 = Unsafe defaults or confusing config
- 1 = Defaults okay, config could be clearer
- 2 = Safe defaults, clear configuration strategy

---

## Pass / Fail Criteria
- **All CRITICAL items must score ≥ 1**
- **Overall average score ≥ 1.6**

If FAIL:
- Do not mark task COMPLETE
- Refactor toward existing patterns, or
- Create TODO tasks to document missing conventions / add ADRs

---

## Required Output
Include in audit report:
- what patterns were followed
- where boundaries live
- any new public interfaces
- any new abstractions and why
- final score + pass/fail

Use:
- `audits/templates/AUDIT_REPORT_TEMPLATE.md`

---

## AI-Specific Failure Modes This Catches
- introducing a new architecture “because it’s cleaner”
- generic abstractions with no payoff
- accidental API surface bloat
- coupling via convenience imports

---

> Design quality is consistency over cleverness.