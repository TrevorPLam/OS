# Documentation Index

Complete index of all governance, policy, standards, and documentation in this repository.

## Quick Navigation

- **Getting Started**: Start here → [Governance Overview](/.repo/GOVERNANCE.md)
- **For Developers**: [Quick Reference](#developer-quick-reference)
- **For Agents**: [Agent Framework](#agent-framework)
- **Policies**: [All Policies](#policies)
- **Templates**: [All Templates](#templates)

---

## Core Governance

### Primary Documents

1. **[Constitution](/.repo/policy/CONSTITUTION.md)**
   - 8 fundamental articles
   - Highest authority after founder
   - Key: No guessing, Evidence-based, Safety first

2. **[Governance Overview](/.repo/GOVERNANCE.md)**
   - Authority chain: Constitution > Manifest > Agents > Policy > Standards > Product
   - Plain English requirement
   - Small increments workflow
   - Filepath requirement

3. **[Repository Manifest](/.repo/repo.manifest.yaml)**
   - Source of truth for commands
   - Verification profiles
   - Test configuration
   - Security settings
   - Boundaries configuration

---

## Policies

All policies are located in `/.repo/policy/`

### 1. [Principles](/.repo/policy/PRINCIPLES.md)
23 foundational principles (P3-P25) that guide all development:

**Key Principles**:
- **P3**: One Change Type Per PR
- **P6**: Evidence Over Vibes
- **P7**: UNKNOWN Is a First-Class State
- **P8**: Read Repo First
- **P10**: Risk Triggers a Stop
- **P13**: Respect Boundaries by Default
- **P22**: Waivers Rare + Temporary

[Full list of 23 principles](/.repo/policy/PRINCIPLES.md)

### 2. [Quality Gates](/.repo/policy/QUALITY_GATES.md)
Merge policy and quality standards:

- **Merge Policy**: Soft block with auto-generated waivers
- **Coverage**: Gradual ratchet (cannot decrease)
- **Performance**: Strict with fallback to defaults
- **Warnings**: Zero warnings
- **Verification Checks**: All enabled

### 3. [Security Baseline](/.repo/policy/SECURITY_BASELINE.md)
Security requirements and controls:

- **Secrets**: Absolute prohibition
- **Dependencies**: Always HITL for vulnerabilities
- **Review Triggers**: 8 types of security-sensitive changes
- **Forbidden Patterns**: 8 patterns that must never appear
- **Mandatory HITL**: 8 actions requiring human approval

### 4. [Boundaries](/.repo/policy/BOUNDARIES.md)
Architectural boundaries and enforcement:

- **Model**: Hybrid Domain/Feature/Layer
- **Structure**: `src/<domain>/<feature>/<layer>/`
- **Import Direction**: UI → Domain → Data → Platform
- **Cross-Feature Rule**: ADR required
- **Enforcement**: Hybrid static checker + manifest

### 5. [HITL System](/.repo/policy/HITL.md)
Human-In-The-Loop system:

- **When Required**: External systems, security, unclear requirements, high risk
- **Storage**: `/.repo/hitl/`
- **Process**: Create → Review → Decide → Archive
- **Categories**: External Integration, Clarification, Risk, Security, Architecture, Compliance

---

## Agent Framework

### Core Documents

1. **[Agents Framework](/.repo/agents/AGENTS.md)**
   - **Rule 1**: No Guessing - UNKNOWN required
   - **Rule 2**: Filepaths required everywhere
   - **Rule 3**: Three-pass code generation (Plan → Implement → Verify)
   - Log requirements
   - Trace log requirements
   - Cross-feature import rules
   - Boundary enforcement

2. **[Agent Capabilities](/.repo/agents/capabilities.md)**
   11 defined capabilities:
   - create_feature
   - modify_existing
   - add_dependency
   - change_api_contract
   - change_schema
   - update_security
   - update_release_process
   - apply_waiver
   - create_adr
   - create_task_packet
   - run_verification_profiles

3. **[Task Packet Template](/.repo/agents/prompts/task_packet.md)**
   - When to use task packets
   - Complete template with examples
   - Best practices

---

## Templates

All templates are located in `/.repo/templates/`

### Document Templates

1. **[ADR Template](/.repo/templates/ADR.md)**
   - Architecture Decision Record
   - Use for significant architectural decisions
   - Format: Context → Decision → Rationale → Alternatives → Consequences

2. **[Waiver Template](/.repo/templates/WAIVER.md)**
   - Quality gate exception
   - Use when quality gate fails
   - Must include: Reason, Remediation Plan, Risk Assessment, Expiration

3. **[HITL Template](/.repo/templates/HITL.md)**
   - Human-In-The-Loop item
   - Use when human decision needed
   - Format: Context → Options → Questions → Impact → Decision

4. **[Agent Log Template](/.repo/templates/AGENT_LOG_TEMPLATE.md)**
   - Human-readable agent log
   - Required for all agent actions
   - Format: Plan → Execution → Verification → Issues → Resolution

5. **[Agent Trace Schema](/.repo/templates/AGENT_TRACE_SCHEMA.json)**
   - Machine-readable trace log
   - JSON Schema for governance verification
   - Required fields: files_changed, verification_results, status

### GitHub Templates

- **[Pull Request Template](/.github/PULL_REQUEST_TEMPLATE.md)**
  - Standard PR format
  - Includes: Description, Type, Files Changed, Verification, Security, Rollback

---

## Standards

Documentation and code standards are in `/.repo/docs/standards/`

### 1. [Documentation Standards](/.repo/docs/standards/documentation.md)

**Location Anchors**:
- File headers with filepaths
- Filepaths in PRs, tasks, ADRs, waivers
- Filepaths in code comments

**Navigation Aids**:
- Domain index files
- Feature index files
- Directory READMEs
- Full path imports

**Iteration Accelerators**:
- Pattern references
- Verification commands
- File touch reasons
- TODO archive references

### 2. [Code Style Standards](/.repo/docs/standards/style.md)

**Code Anchors**:
- Region comments for important sections
- Critical code excerpts in PRs
- Named function anchors

**Safety Heuristics**:
- Impact summary required
- Explicit unknowns required
- Rollback plan required

**Code Organization**:
- File structure conventions
- Function ordering
- Naming conventions
- Error handling patterns

---

## Developer Quick Reference

### Getting Started

1. **Read These First**:
   - [Governance Overview](/.repo/GOVERNANCE.md)
   - [Principles](/.repo/policy/PRINCIPLES.md)
   - [Repository Manifest](/.repo/repo.manifest.yaml)

2. **Install Dependencies**:
   ```bash
   make setup
   ```

3. **Verify Your Setup**:
   ```bash
   make lint && make typecheck
   ```

### Common Commands

From [repo.manifest.yaml](/.repo/repo.manifest.yaml):

```bash
# Install all dependencies
make setup

# Quick local verification (5 min)
make lint && make typecheck

# Full CI verification (15 min)
make lint && make typecheck && make test

# Run tests
make test

# Development server
make dev

# E2E tests
make e2e
```

### Before Creating a PR

1. **Create Task Packet** (if non-trivial change)
   - Copy [Task Packet Template](/.repo/agents/prompts/task_packet.md)
   - Define goal, approach, files, verification

2. **Follow Three-Pass Approach**:
   - **Pass 1 (Plan)**: Understand requirements, plan changes, identify risks
   - **Pass 2 (Implement)**: Make changes, follow patterns, add tests
   - **Pass 3 (Verify)**: Run checks, verify results, document evidence

3. **Run Verification**:
   ```bash
   make lint && make typecheck && make test
   ```

4. **Check for HITL Needs**:
   - External system? Create HITL
   - Security change? Create HITL
   - Breaking change? Create HITL
   - Unclear requirement? Create HITL

5. **Create PR**:
   - Use [PR Template](/.github/PULL_REQUEST_TEMPLATE.md)
   - Include filepaths
   - Show verification evidence
   - Document rollback plan

### When to Create What

| Document | When to Create |
|----------|---------------|
| **Task Packet** | Non-trivial changes (>50 lines), new features, complex bugs |
| **ADR** | Architectural decisions, technology choices, significant patterns |
| **Waiver** | Quality gate failure (auto-generated, you approve) |
| **HITL** | Need human decision, external systems, unclear requirements, security |

### Key Principles to Remember

1. **UNKNOWN is okay** - Declare it, create HITL, don't guess
2. **Evidence required** - Show proof, not just claims
3. **Filepaths everywhere** - Always include absolute paths
4. **Small increments** - Frequent small PRs, not mega-PRs
5. **Safety first** - Stop on risk, don't proceed blindly
6. **Read repo first** - Check docs before starting work
7. **Respect boundaries** - Follow architectural boundaries
8. **One change type** - Don't mix features, bugs, refactors

---

## Directory Structure

```
/
├── .repo/                        # Governance framework
│   ├── GOVERNANCE.md             # Overview and authority chain
│   ├── README.md                 # This index
│   ├── repo.manifest.yaml        # Commands and configuration
│   │
│   ├── policy/                   # Core policies
│   │   ├── CONSTITUTION.md       # 8 fundamental articles
│   │   ├── PRINCIPLES.md         # 23 principles (P3-P25)
│   │   ├── QUALITY_GATES.md      # Quality standards
│   │   ├── SECURITY_BASELINE.md  # Security requirements
│   │   ├── BOUNDARIES.md         # Architectural boundaries
│   │   └── HITL.md               # HITL system
│   │
│   ├── agents/                   # Agent framework
│   │   ├── AGENTS.md             # Core rules
│   │   ├── capabilities.md       # 11 capabilities
│   │   └── prompts/
│   │       └── task_packet.md    # Task packet template
│   │
│   ├── templates/                # Document templates
│   │   ├── ADR.md                # Architecture Decision Record
│   │   ├── WAIVER.md             # Quality gate waiver
│   │   ├── HITL.md               # HITL item
│   │   ├── AGENT_LOG_TEMPLATE.md # Agent log
│   │   └── AGENT_TRACE_SCHEMA.json # Trace schema
│   │
│   ├── docs/standards/           # Standards documentation
│   │   ├── documentation.md      # Documentation standards
│   │   └── style.md              # Code style standards
│   │
│   ├── hitl/                     # HITL items
│   ├── automation/               # Automation scripts
│   └── archive/                  # Historical records
│
├── waivers/                      # Quality gate waivers
│   ├── active/                   # Active waivers
│   └── historical/               # Resolved waivers
│
├── src/platform/                 # Shared platform utilities
│
├── .github/                      # GitHub configuration
│   └── PULL_REQUEST_TEMPLATE.md  # PR template
│
└── [Other project directories]
```

---

## Version History

- **v1.0.0** (2024-01-15): Initial governance framework release
  - Phase 0-5 complete
  - All core documents created
  - Templates and standards defined

---

## Getting Help

1. **Check this index** for relevant documents
2. **Read the principles** (/.repo/policy/PRINCIPLES.md)
3. **Check the manifest** (/.repo/repo.manifest.yaml) for commands
4. **Create HITL** if still unclear

---

**Remember**: When in doubt, declare UNKNOWN and create a HITL item. Safety over speed.
