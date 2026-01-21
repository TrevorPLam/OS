# ENHANCEMENT_SUMMARY.md — Governance Framework v3

Last Updated: 2026-01-02

This release adds determinism, enforcement, and environment reproducibility improvements.

## Added
- Redundant tool entrypoints: README.md, Copilot instructions, Cursor rules, CLAUDE.md, optional aider config
- Machine-readable run contract: repo.manifest.yaml
- Environment options: Devcontainer + mise/asdf templates, documented in docs/ENVIRONMENT.md
- Single-command workflow: Makefile + docs/scripts/check.sh + docs/scripts/bootstrap.sh
- CI gating: .github/workflows/ci.yml
- Security + release hygiene: SECURITY.md, CHANGELOG.md, VERSION, docs/SECURITY_BASELINE.md
- Decision log: docs/adr/* + template
- Observability + deployment placeholders: docs/OBSERVABILITY.md, docs/DEPLOYMENT.md

## Changed
- READMEAI.md reader path reduced to a core set + conditional reads
- TODO.md is the task truth source; docs/scripts/sync-todo.sh can generate TODO.generated.md from specs/project-tasks.md (non-binding notes)
- Validation script avoids external Python dependencies

## Fixed
- Bash quoting/syntax issues in security scan (template-safe)
