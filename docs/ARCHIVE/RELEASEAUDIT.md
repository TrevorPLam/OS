# RELEASEAUDIT.md — Release Audit Runbook

**Authority & Precedence:**
1) CODEBASECONSTITUTION.md
2) READMEAI.md
3) P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md (Task Truth Source)
4) This runbook (RELEASEAUDIT.md)
5) Supporting docs (RELEASE_CHECKLIST.md, CODE_AUDIT_REPORT.md)

**Purpose:** Standardize pre-release verification while retaining existing release checklists and evidence requirements.

## AGENT EXECUTION
- **Inputs to Inspect:** RELEASE_CHECKLIST.md, CODE_AUDIT_REPORT.md, CHANGELOG.md, deployment manifests, P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md release tasks.
- **Outputs to Produce:**
  - Release readiness notes appended to the `Summary` below.
  - Follow-up tasks added to P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md for gaps.
- **Stop Rules:**
  - Do not skip mandatory release gates from RELEASE_CHECKLIST.md.
  - Do not change release processes without TODO-backed approval.

## Standard Checklist
- All tests and linters passing for release commit.
- Security review complete or waivers documented.
- Migration plans validated with rollback steps.
- Documentation (user guides, API specs) updated for the release scope.
- Release notes prepared and reviewed.

## Preserved Project Guidance (from RELEASE_CHECKLIST.md)
- Follow documented pre-release steps including verification of migrations, secrets, monitoring, and smoke tests.
- Capture evidence of completed checks and archive in CODE_AUDIT_REPORT.md when relevant.

---

## Summary (append-only)
- Pending entries.
