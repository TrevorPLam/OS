# audits/code/CHANGEAUDIT.md
> Guardrail audit: prevents scope creep, refactor drift, and accidental breakage.
> This is the **highest-priority micro-audit** for AI-generated repos.

## Goal
Ensure every change is:
- **Necessary**
- **Minimal**
- **Directly justified by the task’s Acceptance Criteria**
- **Safe to merge without collateral damage**

This audit exists to stop agents from:
- refactoring “because it looks better”
- reformatting unrelated files
- expanding scope beyond the task
- silently changing public behavior

---

## Scope
Apply to:
- all files changed by the task
- any files indirectly impacted (imports, configs, manifests)

Do **not** assume intent. Evaluate only what actually changed.

---

## Critical Rules (Hard Fail if Violated)
- ❌ No unrelated formatting or stylistic churn
- ❌ No refactors not required by the task
- ❌ No new features beyond Acceptance Criteria
- ❌ No silent behavior or API changes
- ❌ No file moves/renames unless explicitly required

Any violation above = **score 0 on a critical item** → audit FAIL.

---

## Checklist & Scoring

### 1) Change Justification (CRITICAL)
**Question:** Is every changed file directly justified by the task’s Acceptance Criteria?

- 0 = One or more changes are unrelated or weakly justified
- 1 = All changes are justified, but justification is implicit or thin
- 2 = Every change is explicitly tied to Acceptance Criteria

**Evidence required:**  
- Quote Acceptance Criteria  
- Map each changed file to a criterion

---

### 2) Diff Minimality (CRITICAL)
**Question:** Is the diff as small as reasonably possible?

- 0 = Large or sweeping changes not strictly required
- 1 = Mostly minimal, but some avoidable churn exists
- 2 = Surgical changes only; no unnecessary lines touched

**Red flags:**
- whitespace-only changes
- reordering imports without reason
- renaming variables for “clarity” without necessity

---

### 3) Scope Control (CRITICAL)
**Question:** Did the agent stay within task scope?

- 0 = Scope expanded (extra fixes, refactors, or “while I’m here” edits)
- 1 = Minor scope stretch, but documented
- 2 = Scope strictly limited to task intent

**Note:**  
If extra issues were discovered, the correct action is:
→ **Create a TODO task**, not fix them now.

---

### 4) Behavioral Safety
**Question:** Are existing behaviors preserved unless explicitly changed?

- 0 = Behavior changed without task authorization
- 1 = Behavior change is intentional but risky or under-documented
- 2 = No unintended behavior change (or fully justified and documented)

**Evidence:**  
- Tests
- Before/after explanation
- Doc updates (if behavior changed)

---

### 5) Public Surface Stability
**Question:** Are public APIs, interfaces, or contracts stable?

- 0 = Breaking change without versioning or justification
- 1 = Potential breaking change but mitigated or documented
- 2 = No breaking changes introduced

**Includes:**  
- exported functions
- CLI flags
- config keys
- file formats

---

### 6) Reversibility
**Question:** Could this change be safely reverted if needed?

- 0 = Entangled changes; rollback would be risky
- 1 = Mostly reversible with some care
- 2 = Cleanly reversible; changes are isolated

---

## Pass / Fail Criteria
- **All CRITICAL items must score ≥ 1**
- **Overall average score ≥ 1.6**

If FAIL:
- Do **not** mark task COMPLETE
- Either:
  - reduce the diff, or
  - split work into additional TODO tasks

---

## Required Output
When reporting this audit, include:
- list of files changed
- brief justification per file
- any scope risks identified
- final score + pass/fail

Use:
- `audits/templates/AUDIT_REPORT_TEMPLATE.md`

---

## Common Failure Modes (AI-Specific)
- “I cleaned this up while I was here”
- “I standardized formatting”
- “I renamed this for clarity”
- “I fixed a related bug”

All of the above are **invalid unless explicitly required**.

---

> CHANGEAUDIT exists to keep the repo stable, reviewable, and trustworthy.
> If in doubt: **do less**, not more.