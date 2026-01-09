# audits/code/CORRECTNESSAUDIT.md
> Behavioral audit: verifies that the code does the right thing in all expected conditions.
> This audit answers: “Does this actually work, and fail safely?”

## Goal
Ensure that all implemented behavior:
- Matches the task’s Acceptance Criteria exactly
- Handles expected edge cases
- Fails safely and predictably
- Does not introduce hidden bugs or undefined behavior

This audit is about **truth**, not style.

---

## Scope
Apply to:
- new or modified logic
- affected call paths
- configuration or data flows changed by the task

If a behavior cannot be evaluated due to missing tests, unclear requirements, or missing docs:
- Score **0**
- Mark **UNKNOWN**
- Create a TODO task to make it auditable

---

## Checklist & Scoring

### 1) Acceptance Criteria Fulfillment (CRITICAL)
**Question:** Does the implementation fully satisfy every Acceptance Criterion?

- 0 = One or more criteria are unmet or partially met
- 1 = All criteria met, but edge cases or ambiguity remain
- 2 = All criteria met clearly and unambiguously

**Evidence required:**
- Quote each Acceptance Criterion
- Point to code paths that satisfy them

---

### 2) Happy Path Correctness (CRITICAL)
**Question:** Does the primary intended use work end-to-end?

- 0 = Happy path fails or is incomplete
- 1 = Happy path works but is brittle
- 2 = Happy path works reliably

**Evidence:**
- Test results
- Manual reasoning trace
- Logs/output (if applicable)

---

### 3) Edge Case Handling
**Question:** Are reasonable edge cases handled?

Examples:
- empty inputs
- malformed data
- missing files
- boundary values
- null/undefined states

- 0 = Edge cases cause crashes or undefined behavior
- 1 = Some edge cases handled, others undocumented
- 2 = Edge cases handled or explicitly documented as unsupported

---

### 4) Error Handling & Failure Modes (CRITICAL)
**Question:** When things go wrong, does the system fail safely and clearly?

- 0 = Silent failures, crashes, or misleading behavior
- 1 = Errors surfaced but unclear or inconsistent
- 2 = Clear, consistent, and safe failure behavior

**Includes:**
- error messages
- exit codes
- fallback behavior
- logging

---

### 5) Determinism
**Question:** Is behavior deterministic given the same inputs?

- 0 = Non-deterministic behavior without justification
- 1 = Minor non-determinism but acceptable
- 2 = Fully deterministic or justified randomness

**Watch for:**
- time-based logic
- network calls
- unordered data structures

---

### 6) Interaction Safety
**Question:** Do interactions with other components behave correctly?

- 0 = Breaks or destabilizes dependent code
- 1 = Interaction risks exist but mitigated
- 2 = Interactions are safe and well-bounded

---

## Pass / Fail Criteria
- **All CRITICAL items must score ≥ 1**
- **Overall average score ≥ 1.6**

If FAIL:
- Do not mark the task COMPLETE
- Fix the behavior or
- Create TODO tasks to address gaps

---

## Required Output
Include in the audit report:
- Acceptance Criteria → implementation mapping
- Identified edge cases and handling
- Error/failure behavior summary
- Final score + pass/fail

Use:
- `audits/templates/AUDIT_REPORT_TEMPLATE.md`

---

## Common AI Failure Modes This Catches
- “Looks right” implementations
- Partial acceptance criteria fulfillment
- Missing edge case coverage
- Silent failure paths

---

> CORRECTNESSAUDIT ensures the system behaves as intended — no more, no less.