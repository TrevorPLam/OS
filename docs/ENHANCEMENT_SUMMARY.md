# ENHANCEMENT_SUMMARY.md — Governance Framework v3

Last Updated: 2026-01-02

This release adds determinism, enforcement, and environment reproducibility improvements.

## Added
- Redundant tool entrypoints: README.md, Copilot instructions, Cursor rules, CLAUDE.md, optional aider config
- Machine-readable run contract: repo.manifest.yaml
- Environment options: Devcontainer + mise/asdf templates, documented in docs/ENVIRONMENT.md
- Single-command workflow: Makefile + scripts/check.sh + scripts/bootstrap.sh
- CI gating: githubactions/workflows (disabled by default)/governance-ci.yml
- Security + release hygiene: SECURITY.md, CHANGELOG.md, VERSION, docs/SECURITY_BASELINE.md
- Decision log: docs/adr/* + template
- Cost controls: docs/AI_COST_POLICY.md
- Observability + deployment placeholders: docs/OBSERVABILITY.md, docs/DEPLOYMENT.md

## Changed
- READMEAI.md reader path reduced to a core set + conditional reads
- TODO.md is now strictly derived from specs/project-tasks.md (non-binding notes) (optional, non-binding) via scripts/sync-todo.sh
- Validation script avoids external Python dependencies

## Fixed
- Bash quoting/syntax issues in security scan (template-safe)
