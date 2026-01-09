# audits/code/TESTQUALITYAUDIT.md
> Proof audit: verifies tests are meaningful, deterministic, and tied to behavior.
> This audit answers: “Do the tests actually prove the change works?”

## Goal
Ensure that tests:
- Validate **behavior**, not implementation details
- Cover new/changed logic adequately
- Are deterministic and reliable
- Fail with clear diagnostics
- Don’t create false confidence

If the repo has no test harness, the correct action is:
- record **UNKNOWN**
- create a TODO task to establish minimal testing/verification for the relevant area

---

## Scope
Apply to:
- new tests
- modified tests
- existing tests that should have changed but didn’t
- verification scripts in `repo.manifest.yaml` (as the “test harness” for non-test repos)

---

## Checklist & Scoring

### 1) Tests Exist for Changed Behavior (CRITICAL)
**Question:** For any behavior change, is there a test (or equivalent verification) that would fail before and pass after?

- 0 = No test/verification covers the change
- 1 = Some coverage exists but incomplete
- 2 = Clear coverage exists and would catch regressions

**Evidence:**  
- test file paths + test names  
- or manifest verification commands that validate the behavior

---

### 2) Tests Assert Behavior, Not Implementation (CRITICAL)
**Question:** Do tests validate outputs/side-effects rather than internals?

- 0 = Tests are tightly coupled to internals and will break during refactors
- 1 = Mixed: some behavioral, some overly internal
- 2 = Primarily behavioral assertions

**Red flags:**
- testing private functions unnecessarily
- snapshots that encode incidental formatting
- brittle mocks

---

### 3) Determinism & Flake Resistance (CRITICAL)
**Question:** Are tests stable across runs?

- 0 = Flaky or nondeterministic tests
- 1 = Mostly stable but some risk (time, randomness, external state)
- 2 = Fully deterministic or properly controlled

**Common causes:**
- timezones / current time
- ordering dependence
- network calls
- filesystem state leakage

---

### 4) Minimal Mocks, Realistic Scenarios
**Question:** Are mocks used appropriately without over-mocking?

- 0 = Over-mocked; doesn’t resemble real usage
- 1 = Acceptable but could be more realistic
- 2 = Realistic scenarios with minimal necessary mocking

---

### 5) Failure Diagnostics
**Question:** If a test fails, will the failure message be actionable?

- 0 = Failures are vague; hard to debug
- 1 = Some clarity but inconsistent
- 2 = Clear failure messages and assertions

---

### 6) Coverage of Edge Cases
**Question:** Do tests cover likely edge cases introduced by the change?

- 0 = No edge case coverage where expected
- 1 = Partial edge case coverage
- 2 = Good edge case coverage or explicit justification for omissions

---

## Pass / Fail Criteria
- **All CRITICAL items must score ≥ 1**
- **Overall average score ≥ 1.6**

If FAIL:
- Do not mark task COMPLETE
- Add or improve tests, or
- Create TODO tasks to establish the missing harness

---

## Required Output
Include in audit report:
- which tests/commands validate the change
- what would have failed before
- determinism risks
- final score + pass/fail

Use:
- `audits/templates/AUDIT_REPORT_TEMPLATE.md`

---

## AI-Specific Failure Modes This Catches
- tests that “pass” but don’t test anything important
- snapshot sprawl
- brittle, over-mocked tests
- missing verification because “it seems fine”

---

> If it isn’t tested or verifiably checked, it isn’t proven.