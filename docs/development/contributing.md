# Contributing to UBOS

Thank you for contributing to UBOS! This guide will help you get started.

## Getting Started

1. **Read the Governance Framework** - See [`.repo/GOVERNANCE.md`](../../.repo/GOVERNANCE.md)
2. **Set Up Local Environment** - See [Local Setup](local-setup.md)
3. **Check Current Tasks** - See [`.repo/tasks/TODO.md`](../../.repo/tasks/TODO.md)

## Contribution Process

### 1. Check for Active Tasks
- Review `.repo/tasks/TODO.md` for current work
- Check `.repo/tasks/BACKLOG.md` for upcoming tasks
- Pick a task or create a new one

### 2. Follow Three-Pass Workflow

**Pass 1: Plan**
- List all actions
- Identify risks
- List files to modify (include filepaths)
- Mark UNKNOWN items
- Check if HITL needed

**Pass 2: Change**
- Apply edits
- Follow existing patterns
- Include filepaths
- Respect boundaries

**Pass 3: Verify**
- Run tests (`make test`)
- Run linters (`make lint`)
- Provide evidence
- Update logs

### 3. Link to Task
- All changes must link to task in `.repo/tasks/TODO.md`
- Include filepaths in all changes
- Archive completed tasks

## Code Standards

- Follow [Code Standards](standards.md)
- Respect module boundaries (see [`.repo/policy/BOUNDARIES.md`](../../.repo/policy/BOUNDARIES.md))
- Include filepaths everywhere
- Write tests for new features
- Update documentation when code changes

## Pull Request Process

1. **Create Branch** - From main/master
2. **Make Changes** - Follow three-pass workflow
3. **Run Checks** - `make verify`
4. **Create PR** - Use PR template
5. **Link to Task** - Reference task in PR
6. **Include Evidence** - Test results, verification

## Key Rules

**Always:**
- Include filepaths in all changes
- Link changes to task
- Mark UNKNOWN → Create HITL
- Show verification evidence

**Never:**
- Guess commands (use manifest)
- Skip filepaths
- Commit secrets/.env files
- Cross boundaries without ADR
- Proceed with UNKNOWN items

## Questions?

- Check [`.repo/GOVERNANCE.md`](../../.repo/GOVERNANCE.md)
- Review [`.repo/agents/QUICK_REFERENCE.md`](../../.repo/agents/QUICK_REFERENCE.md)
- Create HITL item if uncertain
