# DEPENDENCY HEALTH

Precedence: CODEBASECONSTITUTION.md → READMEAI.md → specs/* → this document.

Purpose: keep dependencies safe, minimal, and maintainable without requiring scripts, scanners, or CI. This doc defines how to evaluate, add, update, and remove dependencies, and how to prevent “dependency creep” in AI-built repos.

Primary outputs:

* A predictable dependency posture (few surprises, fewer abandoned libs)
* Dependency changes recorded in CHANGELOG.md when they affect behavior
* Any dependency findings converted into TODO.md tasks (with acceptance criteria)

Hard rules:

1. Add dependencies only with an explicit reason and ownership.
2. Prefer fewer, well-maintained dependencies over many one-off packages.
3. Keep only one library per “job” unless there is a documented reason.
4. No dependency changes are “silent.” They must be recorded either in TODO (planned) or CHANGELOG (done).

⠀
---

## AGENT EXECUTION PROMPT (RUN THIS EXACTLY)

You are a dependency health agent operating inside this repository.

Constraints:

* Assume the repo owner does not run scripts and does not use GitHub Actions.
* You may inspect package.json, lockfiles, requirements.txt, pyproject.toml, etc.
* You must not recommend large dependency upgrades unless you also list the risks and a safe upgrade plan.
* Convert findings into concrete TODO.md tasks with:

  * Priority (P0/P1/P2)
  * Type (QUALITY or ENHANCE)
  * Acceptance criteria
  * References (files)

Deliverables:

1. Append a “Dependency Health Summary” section to the bottom of this file (dated).
2. Add/modify TODO.md tasks for any recommended changes (add/update/remove/dedupe).
3. If a dependency change is already completed, ensure it is reflected in CHANGELOG.md and TODO_COMPLETED.md.

⠀
Stop conditions:

* If removing or upgrading a dependency could break production behavior and you cannot validate safely, create a task and stop short of executing the change.
---

## What “healthy” looks like

* Minimal: no duplicates (one date library, one HTTP client, etc.)
* Maintained: dependencies show ongoing maintenance and documentation
* Scoped: dependencies are chosen for clear roles
* Predictable: upgrades happen intentionally, not randomly
* Replaceable: key abstractions avoid lock-in where possible
---

## Phase 1 — Inventory (By Inspection)

Identify dependency manifest(s):

* JS/TS: package.json (+ lockfile)
* Python: pyproject.toml or requirements.txt
* Other ecosystems if present

Record:

* total dependency count (rough)
* top “heavy” dependencies (frameworks, SDKs)
* any obvious duplicates (two libs solving same thing)
* any “one-off” micro deps that could be replaced with native code

Output:

* A short list of “Critical Dependencies” (the ones that can’t break)

* Examples:
* framework (Next.js, React)
* auth provider SDK
* payments SDK (Stripe)
* database client/ORM
---

## Phase 2 — Add Dependency Policy (Before Adding Anything New)

A dependency is allowed only if:

1. It solves a real problem not reasonably solved by existing deps or standard library.
2. It is actively maintained OR is a well-established, stable standard.
3. It doesn’t introduce redundant overlap.
4. It has acceptable licensing for your use (if relevant).
5. You record:

   * why you added it
   * what it replaces (if anything)
   * where it’s used

⠀
When proposing a new dependency, always produce:

* “Why this dependency?”
* “Alternatives considered”
* “Risk if it becomes unmaintained”
* “How to remove later”
---

## Phase 3 — Update Policy (Cadence + Safety)

Recommended cadence (doc-only, no tooling required):

* Patch updates: safe, can bundle periodically
* Minor updates: do selectively; group by area
* Major updates: treat like a mini-project

Upgrade safety checklist:

* Identify what changes (breaking notes, new behavior)
* Identify blast radius (files/flows)
* Define validation plan (manual smoke tests from RELEASE_CHECKLIST.md)
* Update CHANGELOG.md if user-facing behavior changes

Hard rule:

* Never do major upgrades “because it’s old.” Only upgrade with a reason + validation plan.
---

## Phase 4 — Duplicate & Overlap Control

Common overlap categories (choose one):

* Date/time: pick one library
* HTTP: pick one client abstraction
* Validation: pick one schema validator
* State management: pick one approach
* UI components: avoid multiple component kits unless justified

If overlap exists:

* Create a TODO.md task to consolidate:

  * pick the canonical lib
  * list where the other is used
  * migration steps
  * acceptance criteria: “only canonical lib remains”
---

## Phase 5 — Risk Heuristics (No Web, No Tools)

Even without browsing or scanners, you can spot risk patterns:

High risk (P0/P1 candidates):

* dependencies that touch auth, crypto, payments, file uploads
* deps copied from random repos or unverified sources
* deps that require native binaries without clear reason
* deps with broad permissions or runtime code execution

Moderate risk:

* deps that are “glue” libraries but unmaintained
* overly large deps used for tiny tasks

Low risk:

* stable, widely used libraries in mature ecosystems

Rule:

* If a dependency is high-risk and poorly justified, create a task to replace or isolate it.
---

## Phase 6 — Removal Policy (How to Reduce Dependency Creep)

When removing dependencies:

1. Identify all usages (imports/require references).
2. Replace with:

   * existing dependencies, or
   * standard library code, or
   * a small internal utility module.
3. Remove the dependency from manifest.
4. Ensure docs/code references are updated.
5. Record removal in:

   * CHANGELOG.md if behavior changed
   * TODO_COMPLETED.md with date

⠀
Acceptance criteria template:

* “No remaining imports of X”
* “X removed from manifest and lockfile”
* “Equivalent behavior confirmed via smoke tests”
---

## Phase 7 — Dependency Change Recording

Every dependency change must be recorded:

* Planned: TODO.md with task ID
* Completed: TODO_COMPLETED.md + CHANGELOG.md (if behavior impact)

Recommended task labeling:

* Type: ENHANCE (general) or QUALITY (cleanup/consolidation)
* Tag: include “DEP” in title or context
---

## Optional: Lightweight Dependency Notes (Recommended)

Create a short section in DECISIONS.md whenever you choose:

* a core framework
* an auth strategy
* a payments SDK
* an ORM/database layer

This prevents future churn and re-arguing.

---

## Dependency Health Summary (Append Below Each Review)

## Dependency Health Summary — YYYY-MM-DD

Inventory:

* Ecosystem(s):
* Critical dependencies:
* Duplicates/overlap suspected:

Findings:

* (P1) …
* (P2) …

Tasks created:

* T-### …

## Notes / assumptions:

---