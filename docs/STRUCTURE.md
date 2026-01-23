# Documentation Structure

**Purpose:** This document explains the documentation structure and organization principles.

## Structure Overview

The documentation follows a **role-based, task-oriented** structure designed for different audiences and use cases.

## Directory Organization

```
docs/
├── README.md                    ← Main documentation index
├── getting-started/             ← Quick start for new users
│   ├── README.md
│   └── onboarding.md
├── guides/                      ← User-facing guides
│   ├── user/                   ← End-user documentation
│   ├── admin/                  ← Administrative guides
│   └── api/                    ← API usage guides
├── architecture/                ← Technical architecture
│   ├── README.md
│   ├── modules/                ← Module documentation
│   ├── decisions/              ← ADRs
│   └── data-models/            ← Database schema
├── development/                 ← Developer documentation
│   ├── README.md
│   ├── local-setup.md
│   ├── contributing.md
│   ├── testing.md
│   ├── standards.md
│   └── standards/              ← Development standards
├── operations/                  ← Operations documentation
│   ├── README.md
│   ├── monitoring.md
│   ├── troubleshooting.md
│   ├── disaster-recovery.md
│   └── runbooks/               ← Operational runbooks
├── reference/                   ← Technical reference
│   ├── api/                    ← API reference
│   ├── modules/                ← Module reference
│   ├── configuration.md
│   └── cli.md
├── security/                    ← Security documentation
│   ├── README.md
│   ├── compliance.md
│   └── data-privacy.md
├── integrations/                ← Integration docs
│   ├── README.md
│   ├── webhooks.md
│   └── api.md
└── archive/                     ← Historical documentation
    ├── analysis/               ← Analysis documents
    └── redundant/              ← Superseded docs
```

## Organization Principles

### 1. Role-Based Navigation
- **Developers** → `getting-started/` → `development/` → `architecture/`
- **Operators** → `getting-started/` → `operations/`
- **Users** → `getting-started/` → `guides/user/`
- **Integrators** → `guides/api/` → `integrations/`

### 2. Task-Oriented Structure
- Each section organized by what you're trying to do
- Clear entry points for common tasks
- Progressive disclosure (start simple, go deeper)

### 3. Comprehensive Coverage
- **Getting Started** - First steps
- **Guides** - How-to documentation
- **Architecture** - System design
- **Development** - Developer practices
- **Operations** - Deployment and operations
- **Reference** - Complete technical reference
- **Security** - Security and compliance
- **Integrations** - Third-party integrations

### 4. Anticipated Needs
Based on UBOS application structure:
- Multi-tenant architecture → Architecture docs
- Many modules → Module documentation
- API-first → API reference
- Integrations → Integration docs
- Security-focused → Security documentation
- Operations → Runbooks and operations

## Documentation Standards

- **Clear and concise** - Easy to understand
- **Up-to-date** - Documentation ages with code
- **Examples included** - Code examples and use cases
- **Filepaths required** - All references include filepaths
- **Versioned** - Documentation reflects current system

## Adding New Documentation

1. **Choose the right location** - Based on audience and purpose
2. **Follow structure** - Use existing patterns
3. **Include filepaths** - Reference actual files
4. **Link appropriately** - Cross-reference related docs
5. **Update indexes** - Update README files

## Related Documentation

- [Main README](README.md) - Documentation overview
- [Development Guide](development/README.md) - Contributing to docs
- [`.repo/policy/PRINCIPLES.md`](../.repo/policy/PRINCIPLES.md) - Principle 19: Docs Age With Code
