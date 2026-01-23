# OS Project

Operating System project with Django backend and frontend.

## Quick Start

### Install Dependencies
```bash
make setup
```

### Verification
```bash
# Quick check (5 min)
make lint && make typecheck

# Full verification (15 min)
make lint && make typecheck && make test
```

### Development
```bash
# Start development servers
make dev
```

## Documentation

📚 **[Complete Documentation Index](/.repo/DOCS_INDEX.md)**

### For Developers
- **[Governance Framework](/.repo/GOVERNANCE.md)** - Start here
- **[Principles](/.repo/policy/PRINCIPLES.md)** - 23 foundational principles
- **[Repository Manifest](/.repo/repo.manifest.yaml)** - Commands and configuration

### Key Concepts
- **UNKNOWN is First-Class**: Don't guess, declare UNKNOWN and create HITL
- **Evidence Over Vibes**: Show proof with tests, benchmarks, logs
- **Filepaths Required**: Include absolute paths in all artifacts
- **Small Increments**: Frequent small PRs, not mega-PRs
- **Safety Before Speed**: Stop on risk, don't proceed blindly

## Project Structure

```
/
├── backend/          # Django backend
├── frontend/         # Frontend application
├── tests/            # Tests
├── scripts/          # Utility scripts
├── .repo/            # Governance framework
│   ├── policy/       # Policies and principles
│   ├── agents/       # Agent framework
│   ├── templates/    # Document templates
│   └── docs/         # Standards and documentation
├── waivers/          # Quality gate waivers
└── src/platform/     # Shared utilities
```

## Contributing

### Before Creating a PR

1. **Read the Governance**
   - [Governance Overview](/.repo/GOVERNANCE.md)
   - [Principles](/.repo/policy/PRINCIPLES.md)

2. **Create Task Packet** (for non-trivial changes)
   - Template: [/.repo/agents/prompts/task_packet.md](/.repo/agents/prompts/task_packet.md)

3. **Follow Three-Pass Approach**
   - Pass 1 (Plan): Understand, plan, identify risks
   - Pass 2 (Implement): Make changes, add tests
   - Pass 3 (Verify): Run checks, verify, document

4. **Run Verification**
   ```bash
   make lint && make typecheck && make test
   ```

5. **Create PR**
   - Use [PR Template](/.github/PULL_REQUEST_TEMPLATE.md)
   - Include filepaths
   - Show evidence
   - Document rollback

### When to Create HITL

Create a Human-In-The-Loop (HITL) item when:
- Integrating external systems
- Making security changes
- Requirements are unclear
- High-risk changes
- Need human decision or approval

Template: [/.repo/templates/HITL.md](/.repo/templates/HITL.md)

## Commands

### Setup and Installation
```bash
make setup              # Install all dependencies
```

### Development
```bash
make dev                # Start development servers
```

### Verification
```bash
make lint               # Run linting (backend + frontend)
make typecheck          # Run type checking
make test               # Run all tests
make test-performance   # Run performance tests
make e2e                # Run end-to-end tests
make verify             # Run complete verification suite
```

### Quality Checks
```bash
# Quick local check (5 min)
make lint && make typecheck

# Full CI check (15 min)
make lint && make typecheck && make test
```

## Governance Framework

This repository follows a comprehensive governance framework:

- **[Constitution](/.repo/policy/CONSTITUTION.md)**: 8 fundamental articles
- **[Principles](/.repo/policy/PRINCIPLES.md)**: 23 principles (P3-P25)
- **[Quality Gates](/.repo/policy/QUALITY_GATES.md)**: Merge policy, coverage, performance
- **[Security Baseline](/.repo/policy/SECURITY_BASELINE.md)**: Security requirements
- **[Boundaries](/.repo/policy/BOUNDARIES.md)**: Architectural boundaries
- **[HITL System](/.repo/policy/HITL.md)**: Human-In-The-Loop for critical decisions

**Full Index**: [/.repo/DOCS_INDEX.md](/.repo/DOCS_INDEX.md)

## License

[LICENSE](./LICENSE)

## Support

For questions or issues:
1. Check the [Documentation Index](/.repo/DOCS_INDEX.md)
2. Review relevant [Policies](/.repo/policy/)
3. Create a [HITL item](/.repo/templates/HITL.md) if unclear

---

**Remember**: When in doubt, declare UNKNOWN and create a HITL item. Safety over speed.
