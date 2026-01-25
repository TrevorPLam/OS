# Contributing

## Workflow

- Create a branch for your change.
- Keep changes focused and minimal.
- Run the verification suite before opening a PR.

## Golden commands

From repo root:
- `make setup`
- `make lint`
- `make test`
- `make verify`
- `make ci` (alias of `make verify`)

## CI pipeline (GitHub Actions)

- Workflow: `.github/workflows/ci.yml`
- Triggers: pushes to `main`/`develop` (and `claude/*`), plus PRs targeting `main`/`develop`
- Lint job:
  - Runs `make setup`
  - Installs `import-linter`
  - Runs boundary checks and `make lint`
- Test jobs:
  - Backend: `make -C backend test` and `make -C backend test-performance`
  - Frontend: `make -C frontend test` and `make -C frontend build`
- Governance job:
  - Installs `import-linter`
  - Runs `./scripts/governance-verify.sh`

## Backend tooling

- Lint: ruff (`make -C backend lint`)
- Format check: black (`make -C backend lint`)
- Typecheck: mypy (`make -C backend typecheck`)
- Tests: pytest (`make -C backend test`)

## Frontend tooling

- Lint: `npm run lint` via `make -C frontend lint`
- Typecheck: `npm run typecheck`
- Tests: `npm run test` via `make -C frontend test`
- E2E: `npm run e2e` via `make -C frontend e2e`

## Task Lifecycle Automation

### Automatic Task Management

The repository uses an automated task lifecycle system that:
- Automatically archives completed tasks when PRs are merged
- Promotes the next highest-priority task from the backlog
- Maintains a single active task in `.repo/tasks/TODO.md`

#### How It Works

1. **Trigger**: When a PR is merged to `main`, the `task-lifecycle.yml` workflow runs
2. **Detection**: Checks if the PR completes a task by looking for:
   - Keywords in PR title/body: "completes TASK-XXX", "resolves TASK-XXX", etc.
   - All acceptance criteria marked complete in `TODO.md` (all `[x]`)
3. **Archive**: Runs `scripts/archive-task.py` to move completed task to `ARCHIVE.md`
4. **Promote**: Runs `scripts/promote-task.sh` to move next task from `BACKLOG.md` to `TODO.md`
5. **Commit**: Automatically commits and pushes changes back to `main`

#### Manual Task Management

You can also manually manage tasks using the scripts:

```bash
# Archive the current task in TODO.md
python scripts/archive-task.py

# Force archive even if not all criteria are complete
python scripts/archive-task.py --force

# Promote next highest priority task from backlog
bash scripts/promote-task.sh

# Promote a specific task by ID
bash scripts/promote-task.sh TASK-025
```

#### Task Files

- `.repo/tasks/TODO.md` - Single active task (ONE only)
- `.repo/tasks/BACKLOG.md` - Prioritized queue (P0 → P1 → P2 → P3)
- `.repo/tasks/ARCHIVE.md` - Completed tasks with outcomes

#### Best Practices

- Complete all acceptance criteria before merging task-related PRs
- Mention task ID in PR title or body (e.g., "Complete TASK-019")
- Let automation handle task lifecycle (manual intervention rarely needed)
- If automation fails, check workflow logs and follow manual steps

For more details, see `.repo/agents/QUICK_REFERENCE.md` and `.repo/tasks/TODO.md`.
