# Agent Guide (OS)

## Quick Start
1. Read `.repo/tasks/TODO.md` (current task).
2. Read `.repo/repo.manifest.yaml` (commands).
3. Read `.repo/agents/QUICK_REFERENCE.md` (rules).
4. Follow Plan → Change → Verify → Complete task.

## Tech Stack
- Backend: Django 4.2 on Python 3.11
- Frontend: React 18 + TypeScript

## Commands (source: `.repo/repo.manifest.yaml`)
- Install: `make setup`
- Lint: `make lint`
- Tests: `make test`
- Verify (CI): `make verify` or `make verify SKIP_HEAVY=0`

## Testing
- Run `make lint` before PRs.
- Use `make test` for local validation; `make verify` for CI-equivalent checks.
- Always capture command output as evidence.

## Project Structure
- `backend/`: Django app and APIs.
- `frontend/`: React + TypeScript UI.
- `docs/`: Architecture, ADRs, and project docs.
- `tests/`: Cross-cutting tests.
- `.repo/`: Policies, tasks, templates, automation.

## Code Style
- Match nearby patterns; prefer small, readable functions.
- No `try/catch` around imports.
- Example (Python):
  ```python
  def format_label(name: str, count: int) -> str:
      return f"{name} ({count})"
  ```
- Example (TypeScript/React):
  ```tsx
  export function Badge({ label }: { label: string }) {
    return <span className="badge">{label}</span>;
  }
  ```

## Git Workflow
- Keep commits small and task-linked (reference `.repo/tasks/TODO.md`).
- Update task checkboxes, add completion date, archive task when done.
- Use PR template and include: what/why, filepaths, verification, risks, rollback.

## Boundaries (Never Do)
- Do not touch auth/money/external systems without HITL.
- Do not cross module boundaries without ADR.
- Do not proceed on `<UNKNOWN>` items; create HITL instead.
- Do not commit secrets or `.env` files.
