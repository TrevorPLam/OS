# AGENTS.md — Audits Directory

Last Updated: 2026-01-21
Applies To: All agents working in `/audits/`

**IMPORTANT**: See `/BESTPR.md` for repo-wide best practices and patterns.

## Purpose

This directory contains audit artifacts, findings, and templates for various audit types.

## Structure

```
audits/
├── code/                  # Code audit artifacts
└── templates/             # Audit templates
```

## Audit Types

The following audits are defined at the root level:
- `CODEAUDIT.md` — Code quality and structure audit
- `SECURITYAUDIT.md` — Security audit
- `DEPENDENCYAUDIT.md` — Dependency audit
- `RELEASEAUDIT.md` — Release audit
- `DOCSAUDIT.md` — Documentation audit

## Running Audits

### Code Audit
```bash
# Run code audit
# See CODEAUDIT.md for instructions
```

### Security Audit
```bash
# Run security scan
docs/scripts/security-scan.sh

# See SECURITYAUDIT.md for comprehensive instructions
```

### Dependency Audit
```bash
# Check for vulnerable dependencies
pip-audit
npm audit

# See DEPENDENCYAUDIT.md for instructions
```

## Audit Results

- Store audit results in `audits/code/` or appropriate subdirectory
- Include timestamp in filenames
- Document findings and remediation steps
- Track audit history for compliance

## Reference

- **Root Audit Files**: `/{AUDIT_TYPE}AUDIT.md`
- **Best Practices**: `/BESTPR.md`
- **Governance**: `/CODEBASECONSTITUTION.md`
