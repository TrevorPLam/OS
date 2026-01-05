# EMERGENCY_PROTOCOL.md — Stop-the-line

Last Updated: 2026-01-02

This protocol takes priority during suspected compromise, data loss, or runaway changes.
Also review: docs/SECURITY_BASELINE.md

---

# Emergency Protocol (Stop-the-line)

Use this when:
- You suspect data loss, security exposure, or a runaway implementation
- Tests are failing in ways you can’t quickly reason about
- The system behavior diverges from Spec/Plan

## 1) Freeze
- Stop current work immediately.
- Do not continue implementing “to fix it” until the state is understood.

## 2) Snapshot
- Save current context in PROJECT_STATUS.md:
  - What changed
  - What broke
  - What you were trying to do
  - UNKNOWNs discovered

## 3) Revert path (choose one)
A) Fast revert (recommended)
- `git status`
- `git diff`
- Revert last commit(s) or reset to last known good point.

B) Surgical revert
- Identify minimal files causing breakage
- Revert only those changes

## 4) Verify baseline
Run the repo’s standard verification:
- lint
- unit tests
- integration tests (if applicable)
- ai-audit

Record results in PROJECT_STATUS.md.

## 5) Root-cause brief
In PROJECT_STATUS.md add:
- suspected root cause
- proof (logs, diffs, failing test names)
- prevention action (doc + automation update)

## 6) Resume
Resume only after:
- Baseline passes
- The next task is re-planned if required
