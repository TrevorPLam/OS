# AUDITINDEX.md
> Single entry point for all audits.
> This repo is AI-generated; audits are designed to be agent-executable and evidence-driven.

## Required Read Order (Hard Requirement)
1. READMEAI.md
2. CODEBASECONSTITUTION.md (or equivalent constitution file)
3. AGENTS.md
4. TODO.md
5. repo.manifest.yaml (verification commands)

If any file above is missing, STOP and create a TODO task to add/repair it.

---

## Core Rules (Non-Negotiable)
- **No hallucinations:** do not invent files, APIs, or behaviors. If unknown, say UNKNOWN and create a TODO.
- **Minimal diffs:** do not reformat or refactor unrelated code. Changes must be tied to the task’s Acceptance Criteria.
- **Evidence required:** every completion must report:
  - files changed (paths)
  - commands run
  - results (pass/fail + relevant output summary)
- **No premature closure:** do not mark a task COMPLETE until required audits + verification gates pass.

---

## Audit Selection (Choose the smallest adequate set)

### A) Micro-change / tiny doc fix
Run:
- audits/system/DOCSAUDIT.md
- audits/code/CHANGEAUDIT.md

Gate:
- verification per repo.manifest.yaml (if applicable)

### B) Bug fix
Run:
- audits/code/CORRECTNESSAUDIT.md
- audits/code/CHANGEAUDIT.md
- audits/code/TESTQUALITYAUDIT.md (if tests exist; otherwise create a TODO)

Also run:
- audits/system/DOCSAUDIT.md (if behavior/docs changed)

Gate:
- verification per repo.manifest.yaml

### C) New feature
Run:
- audits/code/DESIGNAUDIT.md
- audits/code/CORRECTNESSAUDIT.md
- audits/code/CHANGEAUDIT.md
- audits/code/TESTQUALITYAUDIT.md
- audits/system/DOCSAUDIT.md

Optional (if feature touches secrets, auth, file IO, networking):
- audits/system/SECURITYAUDIT.md

Gate:
- verification per repo.manifest.yaml

### D) Dependency change (add/remove/bump)
Run:
- audits/system/DEPENDENCYAUDIT.md
- audits/system/SECURITYAUDIT.md
- audits/code/CHANGEAUDIT.md
- audits/system/RELEASEAUDIT.md (if versioning/release artifacts exist)

Gate:
- verification per repo.manifest.yaml

### E) Release prep / publish readiness
Run:
- audits/system/RELEASEAUDIT.md
- audits/system/DOCSAUDIT.md
- audits/system/DEPENDENCYAUDIT.md
- audits/system/SECURITYAUDIT.md

Gate:
- verification per repo.manifest.yaml

### F) Agent health / workflow drift
Run:
- audits/system/AGENTAUDIT.md
- audits/system/DOCSAUDIT.md

Gate:
- repo remains consistent with READMEAI.md + constitution + AGENTS.md

---

## “Perfect Codebase Standard” (Operational Definition)
A change meets Perfect Codebase Standard when:
1. All **critical audit items** score != 0
2. Required audits for the task type pass the threshold
3. repo.manifest.yaml verification passes (or is explicitly blocked with a newly created TODO task)
4. TODO.md + directly related docs are updated to match reality

---

## Output Format (Always)
Use: audits/templates/AUDIT_REPORT_TEMPLATE.md

Minimum required in your final response:
- Task executed
- Audit set run (which files)
- Audit results (pass/fail + any 0 scores)
- Verification commands run + results
- Files changed
- TODO updates made