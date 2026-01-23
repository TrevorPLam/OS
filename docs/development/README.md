# Development Guide

This guide covers development practices, workflows, and standards for UBOS.

## Quick Links

- [Local Setup](local-setup.md) - Setting up your development environment
- [Contributing](contributing.md) - How to contribute
- [Code Standards](standards.md) - Coding standards and conventions
- [Testing](testing.md) - Testing strategies

## Development Workflow

### Getting Started
1. Set up local environment - See [Local Setup](local-setup.md)
2. Read [Contributing Guidelines](contributing.md)
3. Review [Code Standards](standards.md)

### Daily Development
- Use `make dev` to run dev servers
- Run `make lint` before committing
- Run `make test` to verify changes
- Use `make verify` for full CI checks

## Development Resources

### Automation & Tools
- [Automation Scripts](automation_scripts.md) - Available automation scripts
- [Boundary Checker](boundary_checker.md) - Module boundary enforcement
- [CI Integration](ci_integration.md) - CI/CD integration

### Standards
- [Manifest Standards](standards/manifest.md) - Command manifest standards

## Key Practices

1. **Follow Three-Pass Workflow** - Plan → Change → Verify
2. **Include Filepaths** - All changes must include filepaths
3. **Link to Tasks** - All changes link to `.repo/tasks/TODO.md`
4. **Respect Boundaries** - Follow module boundary rules
5. **Test Everything** - Write tests for new features

## Related Documentation

- [Architecture](../architecture/README.md) - System architecture
- [Operations](../operations/README.md) - Deployment practices
- [API Reference](../reference/api/README.md) - API documentation
