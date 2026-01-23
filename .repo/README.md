# Repository Governance Framework

This directory contains the complete governance framework for the repository.

## Overview

The governance framework provides:
- **Clear authority and decision-making** (Constitution)
- **Foundational principles** (23 principles P3-P25)
- **Quality standards** (gates, security, boundaries)
- **Agent guidelines** (rules, capabilities, templates)
- **Process templates** (ADRs, waivers, HITL items, task packets)

## Authority Chain

```
Constitution > Manifest > Agents > Policy > Standards > Product
```

## Directory Structure

```
.repo/
├── GOVERNANCE.md              # Governance overview and authority chain
├── repo.manifest.yaml         # Source of truth for commands and config
│
├── policy/                    # Core policies
│   ├── CONSTITUTION.md        # 8 fundamental articles
│   ├── PRINCIPLES.md          # 23 foundational principles (P3-P25)
│   ├── QUALITY_GATES.md       # Merge policy, coverage, performance
│   ├── SECURITY_BASELINE.md   # Security requirements and controls
│   ├── BOUNDARIES.md          # Architectural boundaries
│   └── HITL.md                # Human-In-The-Loop system
│
├── agents/                    # Agent framework
│   ├── AGENTS.md              # Core rules and requirements
│   ├── capabilities.md        # 11 agent capabilities
│   └── prompts/
│       └── task_packet.md     # Task packet template and guide
│
├── templates/                 # Document templates
│   ├── ADR.md                 # Architecture Decision Record
│   ├── WAIVER.md              # Quality gate waiver
│   └── HITL.md                # Human-In-The-Loop item
│
├── docs/                      # Documentation standards
│   └── standards/
│       ├── documentation.md   # Documentation standards
│       └── style.md           # Code style standards
│
├── hitl/                      # HITL items
│   ├── active/                # Active HITL items
│   └── resolved/              # Resolved HITL items
│
├── automation/                # Automation scripts (Phase 6)
│   └── [Future: governance-verify, boundary-checker, etc.]
│
├── templates/                 # Additional templates
│   └── [Future: more templates as needed]
│
└── archive/                   # Historical records
    └── [Archived documents]
```

## Quick Start

### For Developers

1. **Read First**: Start with `.repo/GOVERNANCE.md`
2. **Know the Principles**: Review `.repo/policy/PRINCIPLES.md`
3. **Follow the Manifest**: Check `.repo/repo.manifest.yaml` for commands
4. **Use Templates**: Copy from `.repo/templates/` for ADRs, waivers, etc.

### For Agents

1. **Core Rules**: Read `.repo/agents/AGENTS.md`
2. **Capabilities**: Check `.repo/agents/capabilities.md`
3. **Three-Pass Approach**: Plan → Implement → Verify
4. **When in Doubt**: Declare UNKNOWN and create HITL

### Common Commands

From `repo.manifest.yaml`:

```bash
# Install dependencies
make setup

# Quick local verification (5 min)
make lint && make typecheck

# Full CI verification (15 min)
make lint && make typecheck && make test

# Run specific verification profile
# (Profiles: quick, ci, release, governance)
```

## Key Concepts

### UNKNOWN is First-Class
If something is unclear, **declare UNKNOWN** and create a HITL item. Never guess.

### Evidence Over Vibes
Show proof: test results, benchmarks, logs. Claims need evidence.

### Filepaths Required
All documents, PRs, tasks, and comments must include **explicit filepaths**.

### Small Increments
Deliver in small, frequent, shippable increments. No mega-PRs.

### Safety Before Speed
When risk is detected, **STOP** and escalate. Don't proceed blindly.

## Constitutional Articles

The 8 fundamental articles:

1. **Final Authority**: Solo founder has final authority
2. **Verifiable Over Persuasive**: Decisions based on evidence
3. **No Guessing**: UNKNOWN handling required
4. **Incremental Delivery**: Small, frequent increments
5. **Strict Traceability**: Filepaths in all artifacts
6. **Safety Before Speed**: Stop and escalate on risk
7. **Consistency Over Innovation**: Follow existing patterns
8. **External Systems Require HITL**: All external integrations need approval

See `.repo/policy/CONSTITUTION.md` for details.

## Principles (P3-P25)

23 foundational principles guide all work:

- **P3**: One Change Type Per PR
- **P4**: Make It Shippable
- **P5**: Don't Break Surprises
- **P6**: Evidence Over Vibes
- **P7**: UNKNOWN Is a First-Class State
- **P8**: Read Repo First
- **P9**: Assumptions Must Be Declared
- **P10**: Risk Triggers a Stop
- **P11**: Prefer Guardrails Over Heroics
- **P12**: Rollback Thinking
- **P13**: Respect Boundaries by Default
- **P14**: Localize Complexity
- **P15**: Consistency Beats Novelty
- **P16**: Decisions Written Down (Token-Optimized)
- **P17**: PR Narration
- **P18**: No Silent Scope Creep
- **P19**: Docs Age With Code
- **P20**: Examples Are Contracts
- **P21**: Naming Matters
- **P22**: Waivers Rare + Temporary
- **P23**: ADR Required When Triggered
- **P24**: Logs Required for Non-Docs
- **P25**: Token-Optimized TODO Discipline

See `.repo/policy/PRINCIPLES.md` for full descriptions.

## Quality Gates

- **Merge Policy**: Soft block with auto-generated waivers
- **Coverage**: Gradual ratchet (cannot decrease)
- **Performance**: Strict with fallback to defaults
- **Warnings**: Zero warnings policy
- **Security**: Every PR requires security check

See `.repo/policy/QUALITY_GATES.md` for details.

## Security Baseline

- **Secrets**: Absolute prohibition (never commit secrets)
- **Dependencies**: Vulnerability checks with always HITL
- **Review Triggers**: 8 types of security-sensitive changes
- **Forbidden Patterns**: 8 patterns that must never appear
- **HITL Actions**: 8 mandatory human approvals

See `.repo/policy/SECURITY_BASELINE.md` for details.

## Boundaries

**Model**: Hybrid Domain/Feature/Layer

**Structure**: `src/<domain>/<feature>/<layer>/`

**Import Direction**: UI → Domain → Data → Platform

**Cross-Feature Rule**: ADR required

See `.repo/policy/BOUNDARIES.md` for details.

## HITL System

**When Required**:
- External system integrations
- Security concerns
- Unclear requirements
- High-risk changes
- Complex architectural decisions

**Process**:
1. Create HITL item
2. Human reviews and decides
3. Implementation proceeds if approved
4. HITL archived when resolved

See `.repo/policy/HITL.md` for details.

## Templates

### ADR (Architecture Decision Record)
Use when making significant architectural decisions.

Template: `.repo/templates/ADR.md`

### Waiver
Use when quality gate fails and needs exception.

Template: `.repo/templates/WAIVER.md`

### HITL (Human-In-The-Loop)
Use when human decision or approval needed.

Template: `.repo/templates/HITL.md`

### Task Packet
Use to plan work before implementation.

Template: `.repo/agents/prompts/task_packet.md`

## Verification

### Quick (5 min)
```bash
make lint && make typecheck
```

### CI (15 min)
```bash
make lint && make typecheck && make test
```

### Release (30 min)
```bash
make verify
```

### Governance
```bash
# Future: make check:governance
echo "Governance checks not yet automated"
```

## Getting Help

1. **Read the docs**: Start with `.repo/GOVERNANCE.md`
2. **Check principles**: `.repo/policy/PRINCIPLES.md`
3. **Check manifest**: `.repo/repo.manifest.yaml`
4. **Create HITL**: When unclear, create HITL item

## Maintenance

### Adding New Policies
1. Propose via HITL
2. Create ADR if architectural
3. Update relevant policy documents
4. Communicate to team
5. Update this README

### Adding New Capabilities
1. Propose via HITL
2. Document in `.repo/agents/capabilities.md`
3. Update agent framework if needed
4. Communicate to agents

### Adding New Templates
1. Create template in `.repo/templates/`
2. Add example usage
3. Document in relevant policy
4. Update this README

## Version History

- **v1.0.0** (2024-01-15): Initial governance framework
  - Phase 0: Core infrastructure
  - Phase 1: Policy corpus
  - Phase 2: Manifest and commands
  - Phase 3: Agents framework
  - Phase 4-5: Templates

## Related Documents

- **Governance**: `.repo/GOVERNANCE.md`
- **Manifest**: `.repo/repo.manifest.yaml`
- **Constitution**: `.repo/policy/CONSTITUTION.md`
- **Principles**: `.repo/policy/PRINCIPLES.md`
- **Agents**: `.repo/agents/AGENTS.md`

---

**Remember**: When in doubt, declare UNKNOWN and create a HITL item. Safety over speed.
