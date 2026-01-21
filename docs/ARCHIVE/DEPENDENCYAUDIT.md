# DEPENDENCYAUDIT.md — Dependency Health Runbook

**Authority & Precedence:**
1) CODEBASECONSTITUTION.md
2) READMEAI.md
3) P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md (Task Truth Source)
4) This runbook (DEPENDENCYAUDIT.md)
5) Supporting docs (DEPENDENCY_HEALTH.md)

**Purpose:** Govern dependency updates, licensing, and vulnerability management without discarding existing project-specific guidance.

## AGENT EXECUTION
- **Inputs to Inspect:** requirements*.txt, pyproject.toml, package.json files, lockfiles, DEPENDENCY_HEALTH.md, security advisories, CI dependency scan results.
- **Outputs to Produce:**
  - Findings and upgrade tasks recorded in P0TODO.md, P1TODO.md, P2TODO.md, P3TODO.md with IDs and acceptance criteria.
  - Summary notes appended below.
- **Stop Rules:**
  - Do not remove pinned versions without approval.
  - Do not introduce new package sources or paid services unless authorized.
  - If critical vulnerabilities found, halt and escalate per SECURITYAUDIT.md.

## Standard Checklist
- All production dependencies pinned; dev dependencies isolated.
- Vulnerability scans reviewed and tracked.
- Licenses compatible with project policy.
- Transitive risks assessed for high-impact packages.
- Build reproducibility verified after upgrades.

## Preserved Project Guidance (from DEPENDENCY_HEALTH.md)
- Maintain dependency hygiene to reduce container size and attack surface.
- Prefer removing unused development dependencies from production requirements.
- Document rationale for pins and upgrades.

---

## Summary (append-only)
- Pending entries.
