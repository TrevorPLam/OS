# DOCS_INDEX.md — Documentation Index
Document Type: Reference
Version: 1.0.0
Last Updated: 2026-01-03
Owner: Repository Root
Status: Active

## Quick Navigation

| You are trying to... | Go to |
| --- | --- |
| Set up the project | [SETUP.md](SETUP.md) |
| Understand the architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Navigate the codebase | [REPO_MAP.md](REPO_MAP.md) |
| Understand domain entities | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Work with the API | API docs at `/api/docs/` when running |
| Understand governance | [../CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) |
| AI agent instructions | [../READMEAI.md](../READMEAI.md) |
| Current priorities | [../TODO.md](../TODO.md) |

## Documentation Structure

This repository follows the [Diátaxis framework](https://diataxis.fr/) for documentation organization:

### 📚 Tutorials (Learning-oriented)
- Step-by-step guides for learning
- Goal: Education and initial exposure

### 🔧 How-To Guides (Problem-oriented)  
- Practical guides to solve specific problems
- Goal: Achievement of specific outcomes

### 📖 Reference (Information-oriented)
- Technical descriptions and API documentation
- Goal: Information lookup

### 💡 Explanation (Understanding-oriented)
- Conceptual guides and background
- Goal: Deep understanding

### 📝 Decisions (Architecture Decision Records)
- Historical context for architectural choices
- Goal: Understanding why, not just what

### 👥 User Guides (End-user oriented)
- Documentation for end users (firm admins, clients)
- Goal: Feature usage and workflows

## Core Documents

### Governance
- [CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) - Repository standards and rules
- [READMEAI.md](../READMEAI.md) - AI agent operating instructions
- [codingconstitution.md](../docs/codingconstitution.md) - Comprehensive governance (if in main repo)

### Getting Started
- [README.md](../README.md) - Project overview
- [SETUP.md](SETUP.md) - Development environment setup
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

### Architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) - Core domain entities
- [REPO_MAP.md](REPO_MAP.md) - Repository structure

### Development
- [TODO.md](../TODO.md) - Development roadmap
- [CHANGELOG.md](../CHANGELOG.md) - Release history

### Operations
- API documentation: `/api/docs/` (Swagger UI when running)
- Health check: `/health/`

## Finding What You Need

**I'm new to the project:**
1. Start with [README.md](../README.md)
2. Follow [SETUP.md](SETUP.md)
3. Read [ARCHITECTURE.md](ARCHITECTURE.md)
4. Explore [REPO_MAP.md](REPO_MAP.md)

**I need to implement a feature:**
1. Check [TODO.md](../TODO.md) for current priorities
2. Review [CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) for standards
3. Find the relevant module in [REPO_MAP.md](REPO_MAP.md)
4. Review module-specific documentation

**I'm fixing a bug:**
1. Check tests in the relevant module
2. Review module models and serializers
3. Use API docs at `/api/docs/` for endpoint reference

**I need to understand a decision:**
- Check `05-decisions/` folder for ADRs
- Review git history and commit messages
- Check issue/PR discussions in GitHub

## Documentation Standards

All documentation should include:
- Document Type
- Version
- Last Updated
- Owner
- Status
- Dependencies (if applicable)

See [CODEBASECONSTITUTION.md](../CODEBASECONSTITUTION.md) §5 for full standards.
