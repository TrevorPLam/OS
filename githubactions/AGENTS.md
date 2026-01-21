# AGENTS.md — GitHub Actions Directory

Last Updated: 2026-01-21
Applies To: All agents working in `/githubactions/`

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.

## Purpose

This directory stores GitHub Actions workflows that are **OFF by default** for cost control.

## Structure

```
githubactions/
├── workflows/             # GitHub Actions workflow files (.yml)
└── README.md              # Enable/disable instructions
```

## Cost Control Policy

**CRITICAL**: GitHub Actions are DISABLED by default.

To enable workflows:
1. See `githubactions/README.md` for instructions
2. Move workflow files to `.github/workflows/`
3. Requires explicit owner approval

## Why OFF by Default?

- **Cost Control**: GitHub Actions minutes cost money
- **Prefer Local**: Use local scripts and `make` targets instead
- **Explicit Approval**: Owner must approve any automation that increases spend

## Workflow Storage

All workflows are stored here for safekeeping:
- CI/CD pipelines
- Automated testing
- Deployment workflows
- Scheduled jobs

## Alternative: Local Verification

Instead of GitHub Actions, use:

```bash
# Run locally
make lint       # Linting
make test       # Tests
make verify     # Full verification
```

## Enabling Workflows

**Only with owner approval**:

1. Review workflow in `githubactions/workflows/`
2. Get owner approval
3. Move to `.github/workflows/`
4. Document decision in `CHANGELOG.md`

## Reference

- **Enable Instructions**: `githubactions/README.md`
- **Cost Policy**: `/CODEBASECONSTITUTION.md` section 4
- **Local Verification**: `/repo.manifest.yaml`
- **Best Practices**: `/BESTPR.md`
