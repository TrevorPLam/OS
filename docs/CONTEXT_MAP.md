# CONTEXT_MAP.md

Last Updated: 2026-01-02

This is the shortest “where do I edit?” routing table for humans and AI.

## Start here
1) `READMEAI.md` (how to operate)
2) `PROJECT_STATUS.md` (what to do next)
3) `repo.manifest.yaml` (how to run/verify)
4) `specs/project-tasks.md (non-binding notes) (optional, non-binding)` (tasks source of truth)

## Common edits
- Change what the project is: `specs/project-spec.md`
- Change technical design: `specs/technical-plan.md`
- Add/modify tasks: `specs/project-tasks.md (non-binding notes) (optional, non-binding)` (then run `scripts/sync-todo.sh`)
- Update state: `PROJECT_STATUS.md`
- Security rules: `docs/SECURITY_BASELINE.md`
- UI conventions: `docs/UI_DESIGN_SYSTEM.md`
- Integration contracts: `docs/INTEGRATION_MAP.md`
- Emergency stop-the-line: `docs/EMERGENCY_PROTOCOL.md`

## Tool-specific “always read” entrypoints
- GitHub Copilot: `.github/copilot-instructions.md`
- Cursor: `.cursor/rules/00-governance/RULE.md`
- Claude: `CLAUDE.md`
- Aider (optional): `.aider.conf.yml`
