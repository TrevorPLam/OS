# Documentation Best Practices

This document outlines the documentation standards and best practices used in the ConsultantPro project.

## Documentation Framework

We follow the [Diátaxis framework](https://diataxis.fr/), which organizes documentation into four distinct categories:

### 1. Tutorials (Learning-Oriented)
**Purpose:** Help newcomers learn by doing
**Location:** `docs/01-tutorials/`
**Characteristics:**
- Step-by-step instructions
- Focused on learning outcomes
- Practical, hands-on approach
- Assumes minimal prior knowledge

**Example:** [Getting Started Tutorial](../01-tutorials/getting-started.md)

### 2. How-To Guides (Task-Oriented)
**Purpose:** Help users accomplish specific tasks
**Location:** `docs/02-how-to/`
**Characteristics:**
- Goal-oriented instructions
- Assumes prior knowledge
- Focused on practical results
- Concise and actionable

**Example:** [Production Deployment Guide](../02-how-to/production-deployment.md)

### 3. Reference (Information-Oriented)
**Purpose:** Provide technical descriptions and specifications
**Location:** `docs/03-reference/`
**Characteristics:**
- Accurate and complete
- Structured and consistent
- Neutral tone
- Easy to scan and search

**Examples:** [API Reference](../03-reference/api-usage.md), [Tier System Reference](../03-reference/tier-system.md)

### 4. Explanation (Understanding-Oriented)
**Purpose:** Clarify and illuminate concepts
**Location:** `docs/04-explanation/`
**Characteristics:**
- Conceptual discussions
- Provides context and background
- Explains design decisions
- Explores alternatives

**Example:** [Architecture Overview](../04-explanation/architecture-overview.md)

## Writing Guidelines

### General Principles

1. **Single Source of Truth** - Avoid duplicating information across documents
2. **Cross-Reference, Don't Duplicate** - Link to related information instead of repeating it
3. **Keep It Current** - Update documentation in the same PR as code changes
4. **Use Clear Headings** - Make documents scannable with descriptive headings
5. **Include Examples** - Show don't just tell, especially in tutorials and how-tos

### Markdown Standards

- Use ATX-style headers (`#`, `##`, `###`)
- Include a table of contents for documents over 200 lines
- Use code fences with language specifiers (```python, ```bash)
- Use relative links for internal documentation
- Use descriptive link text (not "click here")

### File Naming

- Use lowercase with hyphens: `getting-started.md`, not `GettingStarted.md`
- Be descriptive: `production-deployment.md` not `deploy.md`
- Group related files in directories

### Content Organization

- Start with a brief introduction
- Use a logical hierarchy of headings
- Include "Next Steps" or "See Also" sections
- Add a "Last Updated" date for time-sensitive content

## Documentation Maintenance

### When to Update Documentation

- **Code Changes:** Update relevant docs in the same PR
- **API Changes:** Update API reference and any affected tutorials
- **Architecture Changes:** Update architecture overview and tier docs
- **Deprecations:** Mark deprecated features and provide migration paths
- **New Features:** Add tutorials, how-tos, and reference documentation

### Review Process

All documentation changes should be reviewed for:
- Accuracy
- Clarity
- Completeness
- Consistency with other docs
- Proper categorization (tutorial vs how-to vs reference vs explanation)

### Broken Link Prevention

- Use relative links for internal documentation
- Test links after moving or renaming files
- Use a link checker in CI (if available)
- Keep file structure stable

## Common Patterns

### Linking Between Documents

```markdown
<!-- Good: Relative link with descriptive text -->
See [API Reference](../03-reference/api-usage.md) for endpoint details.

<!-- Bad: Absolute link or unclear text -->
See [here](/docs/03-reference/api-usage.md) for more info.
```

### Code Examples

```markdown
<!-- Good: Language-specific code fence with context -->
Create a virtual environment:

\```bash
python -m venv .venv
source .venv/bin/activate
\```

<!-- Bad: No language or context -->
\```
python -m venv .venv
\```
```

### Cross-References

```markdown
<!-- Good: Provides context about what the link contains -->
For detailed security requirements, see [Tier 0: Foundational Safety](tier-system.md#tier-0-foundational-safety).

<!-- Bad: Unclear what the link leads to -->
See [tier system](tier-system.md).
```

## Documentation Structure

### Root-Level Documentation
Keep only essential files at the root:
- `README.md` - Project overview
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy
- `TODO.md` - Current work status

### Organized Documentation
Place detailed documentation in `docs/` following Diátaxis:
- Tutorials → `docs/01-tutorials/`
- How-To Guides → `docs/02-how-to/`
- Reference → `docs/03-reference/`
- Explanation → `docs/04-explanation/`
- Decisions → `docs/05-decisions/`
- User Guides → `docs/06-user-guides/`

### Specifications
Keep frozen specs in `spec/`:
- System invariants
- API contracts
- Data schemas
- Integration contracts

## Anti-Patterns to Avoid

### ❌ Don't: Mix Documentation Types
Don't combine tutorials with reference material in the same document.

### ❌ Don't: Create Duplicate Content
Don't repeat the same information in multiple places.

### ❌ Don't: Use Outdated Examples
Keep code examples current with the codebase.

### ❌ Don't: Create Orphan Documents
Every document should be linked from at least one other document.

### ❌ Don't: Ignore Documentation Debt
Address outdated docs in the same PR that changes the code.

## Resources

- [Diátaxis Framework](https://diataxis.fr/) - Documentation system we follow
- [Markdown Guide](https://www.markdownguide.org/) - Markdown syntax reference
- [Writing Style Guide](https://developers.google.com/style) - Google's developer documentation style guide

## Questions?

If you're unsure where to place documentation or how to structure it, open a discussion or ask in the PR review.
