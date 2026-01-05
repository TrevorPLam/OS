# REPO_MAP.md — Architectural Directory & File Map

Document Type: Reference
Version: 2.0.0
Last Updated: 2026-01-02
Owner: Repository Root
Status: Active

Purpose: the “map of the house.” Use this before making structural changes so you don’t put a stove in the bedroom.

---

## 1) The architectural hierarchy
This repository is a governance-first template. The application-specific architecture lives in whatever project you apply this template to.

Hierarchy (what to read first):
1) `CODEBASECONSTITUTION.md`
2) `READMEAI.md`
3) `AGENTS.md`
4) `TODO.md`
5) Runbooks (`CODEAUDIT.md`, `SECURITYAUDIT.md`, `DEPENDENCYAUDIT.md`, `RELEASEAUDIT.md`, `DOCSAUDIT.md`)
6) `repo.manifest.yaml`
7) `PROJECT_STATUS.md`
8) `specs/*` (non-binding notes)
9) `docs/*`

---

## 2) Root directory
- `README.md` → points agents to `READMEAI.md`
- `READMEAI.md` → AI operating console
- `CODEBASECONSTITUTION.md` → highest authority
- `PROJECT_STATUS.md` → current truth + next step
- `repo.manifest.yaml` → how to run/verify/ship (machine-readable)
- `TODO.md` → task truth source
- `SECURITY.md` → reporting + baseline expectations
- `CHANGELOG.md` + `VERSION` → release hygiene

---

## 3) specs/
- `specs/project-spec.md` → what/why
- `specs/technical-plan.md` → how
- `specs/*` → non-binding notes; convert to tasks in `TODO.md` when actionable

---

## 4) docs/
- `docs/CONTEXT_MAP.md` → short routing table (where to edit)
- `docs/TESTING_STRATEGY.md` → verification expectations
- `docs/INTEGRATION_MAP.md` → external dependencies + contracts
- `docs/SECURITY_BASELINE.md` → secrets/auth/data rules
- `docs/OBSERVABILITY.md` → logging/metrics/tracing conventions
- `docs/DEPLOYMENT.md` → how to ship/run in environments
- `docs/AI_COST_POLICY.md` → session guard rails
- `docs/adr/*` → decision log

---

## 5) docs/scripts/
- `docs/scripts/bootstrap.sh` → initialize hooks + regenerate TODO
- `docs/scripts/sync-todo.sh` → generate TODO artifacts (informational)
- `docs/scripts/ai-audit.sh` → governance gate
- `docs/scripts/security-scan.sh` → secrets hygiene
- `docs/scripts/check.sh` → best-effort checks
- `docs/scripts/validate-enhancements.sh` → validate template consistency
- `docs/scripts/new-repo.sh` → stamp this template into another repo

---

## 6) Tool-specific determinism entrypoints
- Copilot: `.github/copilot-instructions.md`
- Cursor: `.cursor/rules/00-governance/RULE.md`
- Claude: `CLAUDE.md`
- Aider (optional): `.aider.conf.yml`

---

## 7) CI + hooks
- Local: `.githooks/pre-commit`
- CI: `githubactions/workflows (disabled by default)/governance-ci.yml`
