# Repository Index

**File**: `INDEX.md`

This is the master index of all directories in the repository. Each major directory has its own `INDEX.md` file with detailed contents.

## Directory Index

| Directory       | Purpose                                      | Index File                         |
| --------------- | -------------------------------------------- | ---------------------------------- |
| `.repo/`        | Governance framework, policies, agent rules   | [`.repo/INDEX.md`](.repo/INDEX.md) |
| `backend/`      | Django backend application                   | [`backend/INDEX.md`](backend/INDEX.md) |
| `frontend/`     | React/TypeScript frontend application        | [`frontend/INDEX.md`](frontend/INDEX.md) |
| `tests/`        | Cross-cutting and integration tests          | [`tests/INDEX.md`](tests/INDEX.md) |
| `scripts/`      | Automation and utility scripts               | [`scripts/INDEX.md`](scripts/INDEX.md) |
| `docs/`          | Documentation (comprehensive docs structure) | See [`docs/README.md`](docs/README.md) |
| `.repo/tasks/`   | Task management (TODO, BACKLOG, ARCHIVE)     | See `.repo/tasks/` directory |

## Quick Navigation

### Code Directories

- **Backend**: [`backend/INDEX.md`](backend/INDEX.md) - Django API, modules, configuration
- **Frontend**: [`frontend/INDEX.md`](frontend/INDEX.md) - React components, pages, API clients

### Supporting Directories

- **Tests**: [`tests/INDEX.md`](tests/INDEX.md) - Test suites organized by module
- **Scripts**: [`scripts/INDEX.md`](scripts/INDEX.md) - Automation scripts
- **Docs**: See [`docs/README.md`](docs/README.md) - Comprehensive documentation

### Governance

- **Governance**: [`.repo/INDEX.md`](.repo/INDEX.md) - Policies, agent framework, HITL

## Repository Structure Overview

```text
.
├── INDEX.md              ← You are here (master index)
├── .repo/                ← Governance framework
│   ├── INDEX.md         ← Governance index
│   ├── policy/          ← Policy files
│   ├── agents/          ← Agent framework
│   └── templates/       ← Document templates
├── backend/              ← Django backend
│   ├── INDEX.md        ← Backend index
│   ├── api/            ← API endpoints
│   ├── modules/        ← Domain modules
│   └── config/         ← Django configuration
├── frontend/             ← React frontend
│   ├── INDEX.md        ← Frontend index
│   └── src/            ← Application source
├── tests/                ← Test suites
│   └── INDEX.md        ← Tests index
├── scripts/              ← Automation scripts
│   └── INDEX.md        ← Scripts index
└── .repo/                ← Governance & documentation
    ├── tasks/            ← Task management
    └── docs/             ← Documentation
```

## See Also

- [`.repo/GOVERNANCE.md`](.repo/GOVERNANCE.md) - Governance framework entry point
- [`README.md`](README.md) - Project overview and quick start
- [`AGENTS.md`](AGENTS.md) - AI contribution guide
- [`.repo/policy/BESTPR.md`](.repo/policy/BESTPR.md) - Repository best practices
