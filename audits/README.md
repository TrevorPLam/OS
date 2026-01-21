# audits/README.md
> How to run audits in this repo (agent-executable, evidence-driven).
> This repo is AI-generated; audits are built to reduce AI failure modes and keep the codebase shippable.

## What this folder is
This folder contains the audit system referenced by `AUDITINDEX.md`.

Audits are:
- **Checklist-driven** (objective, low-subjectivity)
- **Scored** (0/1/2 per item)
- **Gated** (no “task complete” without passing audits + verification evidence)

If anything is unknown or missing, the correct action is:
- **STOP**, report **UNKNOWN**, and create a **TODO task** to resolve the missing prerequisite.

---

## Required entry point
Always start at the root index:

1. `AUDITINDEX.md` (select the smallest adequate audit set)
2. Follow **Required Read Order** in `AUDITINDEX.md`
3. Execute the selected audits from this folder

If `AUDITINDEX.md` is missing, create a TODO task to restore it.

---

## Audit execution rules (non-negotiable)

### 1) No hallucinations
- Do not invent files, APIs, modules, commands, or behaviors.
- If an audit references something that does not exist, mark it **UNKNOWN** and create a TODO task.

### 2) Minimal diffs
- Do not reformat/restructure unrelated code.
- Only change what is required by the task’s Acceptance Criteria and the audit findings.

### 3) Evidence required
Every audit run must record:
- files inspected (paths)
- findings (bulleted)
- score per checklist item (0/1/2)
- pass/fail with thresholds
- any TODO tasks created

### 4) No premature closure
Do not mark tasks COMPLETE in `P0TODO.md`, `P1TODO.md`, `P2TODO.md`, `P3TODO.md` until:
- required audits pass (no critical item scored 0)
- verification per `repo.manifest.yaml` passes (or is blocked + TODO created)

---

## Scoring system
Each checklist item is scored:

- **0 = Fail** (missing, incorrect, unsafe, or violates repo rules)
- **1 = Acceptable** (works but has a clear improvement opportunity)
- **2 = Excellent** (fully compliant, consistent, and robust)

### Pass thresholds
- **Critical items:** must be **>= 1** (no 0 allowed)
- **Overall pass:** average score **>= 1.6** (unless the audit file defines a stricter threshold)

If an item cannot be evaluated, score **0** and label **UNKNOWN**, then create a TODO task to make it auditable.

---

## Output format (standard)
All audit reporting must use:

- `audits/templates/AUDIT_REPORT_TEMPLATE.md`

Minimum in final response:
- Audit set run (which audit files)
- Pass/fail + any 0 scores (and why)
- Verification commands run + results
- Files changed
- TODO updates made

---

## Folder map

### Code micro-audits
`audits/code/`
- `CORRECTNESSAUDIT.md` — behavior correctness and edge cases
- `CHANGEAUDIT.md` — minimal diff, no scope creep, safe edits
- `DESIGNAUDIT.md` — architecture coherence within existing patterns
- `TESTQUALITYAUDIT.md` — tests prove behavior, are deterministic, and meaningful

### System audits
`audits/system/`
- `DOCSAUDIT.md` — docs match reality
- `DEPENDENCYAUDIT.md` — supply-chain hygiene + licenses + necessity
- `SECURITYAUDIT.md` — secrets, unsafe defaults, attack surface
- `RELEASEAUDIT.md` — shippability, metadata, reproducibility
- `AGENTAUDIT.md` — resilience to agent drift + prompt injection

### Templates
`audits/templates/`
- `AUDIT_REPORT_TEMPLATE.md` — standardized report output

---

## When in doubt
- Prefer smaller audit sets (per `AUDITINDEX.md`)
- Prefer creating a TODO task over guessing
- Prefer stopping after one task/audit cycle with a clean report
