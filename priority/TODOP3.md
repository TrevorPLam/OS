# Phase 3: Agents Framework

## Phase Metadata

- **Phase**: P3
- **Priority**: High (P1)
- **Overall Status**: Not Started
- **Owner**: AI/ML Lead
- **Dependencies**: P0 (Master Handoff Skeleton), P1 (Policy Corpus), P2 (Manifest)
- **Target Completion**: Sprint 3

## Scope

### In Scope:
- Create /.repo/agents/AGENTS.md with core rules and requirements
- Create /.repo/agents/capabilities.md listing all agent capabilities
- Create agent role definitions (primary, secondary, reviewer, release)
- Create folder-level AGENT.md guides for key directories
- Document log and trace requirements for agents
- Document cross-feature import and boundary enforcement rules

### Out of Scope:
- Agent training and onboarding materials (future)
- Agent performance monitoring (future)
- Automated agent testing (P6)
- PR/task packet templates (P4)

## Success Criteria

- [ ] AGENTS.md created with core rules and requirements
- [ ] capabilities.md created with all capabilities listed
- [ ] All 4 agent roles documented (primary, secondary, reviewer, release)
- [ ] Folder-level AGENT.md files created for 6 key directories
- [ ] Log and trace requirements clearly documented
- [ ] Cross-feature and boundary rules documented

## Work Packages

### WP-P3.1: Agents Framework Core

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: AI/ML Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2, WP-P1.2
- Blocks: WP-P3.2, WP-P3.3

**Description:**
Create the core agents framework documentation including rules (no guessing, filepaths required, three-pass code generation), log requirements, trace requirements, cross-feature import rule, and boundary enforcement.

**Acceptance Criteria:**
- [ ] /.repo/agents/AGENTS.md created
- [ ] Core rules documented (no guessing, filepaths, three-pass)
- [ ] Log requirements documented with template reference
- [ ] Trace log requirements documented with schema reference
- [ ] Cross-feature import rule documented (ADR required)
- [ ] Boundary model enforcement documented

**Tasks:**
- [ ] **T-P3.1.1**: Create /.repo/agents/AGENTS.md with structure
  - Files: `/.repo/agents/AGENTS.md`
  - Commands: `test -f /.repo/agents/AGENTS.md && wc -l /.repo/agents/AGENTS.md`
  - Evidence: File exists with complete structure

- [ ] **T-P3.1.2**: Document core rules (no guessing, filepaths required, three-pass code generation)
  - Files: `/.repo/agents/AGENTS.md`
  - Commands: `grep -c "Rule [0-9]:" /.repo/agents/AGENTS.md` (should be ≥3)
  - Evidence: All core rules documented

- [ ] **T-P3.1.3**: Document log requirements (/.repo/templates/AGENT_LOG_TEMPLATE.md)
  - Files: `/.repo/agents/AGENTS.md`
  - Commands: `grep -A5 "log.*requirement" /.repo/agents/AGENTS.md`
  - Evidence: Log requirements documented with template reference

- [ ] **T-P3.1.4**: Document trace log requirements (/.repo/templates/AGENT_TRACE_SCHEMA.json)
  - Files: `/.repo/agents/AGENTS.md`
  - Commands: `grep -A5 "trace.*requirement" /.repo/agents/AGENTS.md`
  - Evidence: Trace requirements documented with schema reference

- [ ] **T-P3.1.5**: Document cross-feature import rule (ADR required)
  - Files: `/.repo/agents/AGENTS.md`
  - Commands: `grep -A5 "cross-feature" /.repo/agents/AGENTS.md`
  - Evidence: Cross-feature import rule documented

- [ ] **T-P3.1.6**: Document boundary model enforcement
  - Files: `/.repo/agents/AGENTS.md`
  - Commands: `grep -A5 "boundary.*enforcement" /.repo/agents/AGENTS.md`
  - Evidence: Boundary enforcement rules documented

**Out of Scope for This Work Package:**
- Specific agent capabilities (WP-P3.2)
- Agent roles (WP-P3.3)
- Folder-level guides (WP-P3.4)

**Notes:**
- Reference P0 principles (P7: UNKNOWN, P8: Read Repo First)
- Reference P1 policies (BOUNDARIES.md, PRINCIPLES.md)
- Three-pass code generation: 1) plan, 2) implement, 3) verify

---

### WP-P3.2: Agent Capabilities

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: AI/ML Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P3.1
- Blocks: WP-P3.3

**Description:**
Document all agent capabilities with clear descriptions. Capabilities define what actions agents are allowed to perform.

**Acceptance Criteria:**
- [ ] /.repo/agents/capabilities.md created
- [ ] All 11 capabilities listed and described
- [ ] Each capability has description, scope, and constraints

**Tasks:**
- [ ] **T-P3.2.1**: Create /.repo/agents/capabilities.md
  - Files: `/.repo/agents/capabilities.md`
  - Commands: `test -f /.repo/agents/capabilities.md && wc -l /.repo/agents/capabilities.md`
  - Evidence: File exists

- [ ] **T-P3.2.2**: List all capabilities with descriptions
  - Files: `/.repo/agents/capabilities.md`
  - Commands: `grep -c "^## " /.repo/agents/capabilities.md` (should be 11)
  - Evidence: All 11 capabilities documented
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

**Out of Scope for This Work Package:**
- Agent role assignments (WP-P3.3)
- Capability implementation automation (future)

**Notes:**
- Each capability should document: what it is, when to use it, constraints, required approvals
- Some capabilities are human-only (apply_waiver, update_release_process)

---

### WP-P3.3: Agent Roles

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: AI/ML Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P3.1, WP-P3.2
- Blocks: None

**Description:**
Define agent roles (primary, secondary, reviewer, release) with their assigned capabilities, responsibilities, and constraints. Roles determine what agents can do.

**Acceptance Criteria:**
- [ ] All 4 role files created in /.repo/agents/roles/
- [ ] Each role documents assigned capabilities
- [ ] Each role documents responsibilities and constraints
- [ ] Primary role: full capabilities except apply_waiver and update_release_process
- [ ] Secondary role: modify_existing, refactor/port within boundaries
- [ ] Reviewer role: human, controls waivers + enforcement
- [ ] Release role: human, controls update_release_process and deploy

**Tasks:**
- [ ] **T-P3.3.1**: Create /.repo/agents/roles/primary.md
  - Files: `/.repo/agents/roles/primary.md`
  - Commands: `test -f /.repo/agents/roles/primary.md && grep -c "capability" /.repo/agents/roles/primary.md`
  - Evidence: Primary role documented with full capabilities except apply_waiver and update_release_process

- [ ] **T-P3.3.2**: Create /.repo/agents/roles/secondary.md
  - Files: `/.repo/agents/roles/secondary.md`
  - Commands: `test -f /.repo/agents/roles/secondary.md && grep "modify_existing" /.repo/agents/roles/secondary.md`
  - Evidence: Secondary role documented with limited capabilities (modify_existing, refactor within boundaries)

- [ ] **T-P3.3.3**: Create /.repo/agents/roles/reviewer.md
  - Files: `/.repo/agents/roles/reviewer.md`
  - Commands: `test -f /.repo/agents/roles/reviewer.md && grep "human" /.repo/agents/roles/reviewer.md`
  - Evidence: Reviewer role documented (human, controls waivers + enforcement)

- [ ] **T-P3.3.4**: Create /.repo/agents/roles/release.md
  - Files: `/.repo/agents/roles/release.md`
  - Commands: `test -f /.repo/agents/roles/release.md && grep "update_release_process" /.repo/agents/roles/release.md`
  - Evidence: Release role documented (human, controls release + deploy)

**Out of Scope for This Work Package:**
- Role assignment automation (future)
- Role-based access control implementation (future)

**Notes:**
- Roles enforce separation of duties
- Human roles (reviewer, release) are non-negotiable
- Primary agents do most work, secondary for safe tasks

---

### WP-P3.4: Folder-Level Agent Guides

**Block**: Documentation  
**Priority**: P1  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P3.1, WP-P3.2
- Blocks: None

**Description:**
Create folder-level AGENT.md guides for key directories. These guides help agents understand the purpose of each directory, allowed operations, forbidden patterns, and required links.

**Acceptance Criteria:**
- [ ] 6 folder-level AGENT.md files created
- [ ] Each guide documents: purpose, allowed operations, forbidden patterns, required links
- [ ] Guides cover: /.repo/, /src/, /src/platform/, /tests/, /docs/, /scripts/

**Tasks:**
- [ ] **T-P3.4.1**: Create /.repo/AGENT.md
  - Files: `/.repo/AGENT.md`
  - Commands: `test -f /.repo/AGENT.md && grep -i "purpose" /.repo/AGENT.md`
  - Evidence: Guide documents governance structure purpose, allowed operations, forbidden patterns

- [ ] **T-P3.4.2**: Create /src/AGENT.md
  - Files: `/src/AGENT.md`
  - Commands: `test -f /src/AGENT.md && grep -i "boundary" /src/AGENT.md`
  - Evidence: Guide documents source code structure, boundary rules, allowed operations

- [ ] **T-P3.4.3**: Create /src/platform/AGENT.md
  - Files: `/src/platform/AGENT.md`
  - Commands: `test -f /src/platform/AGENT.md && grep -i "shared" /src/platform/AGENT.md`
  - Evidence: Guide documents shared platform purpose, strict rules, allowed operations

- [ ] **T-P3.4.4**: Create /tests/AGENT.md
  - Files: `/tests/AGENT.md`
  - Commands: `test -f /tests/AGENT.md && grep -i "test" /tests/AGENT.md`
  - Evidence: Guide documents test organization, allowed operations, forbidden patterns

- [ ] **T-P3.4.5**: Create /docs/AGENT.md
  - Files: `/docs/AGENT.md`
  - Commands: `test -f /docs/AGENT.md && grep -i "documentation" /docs/AGENT.md`
  - Evidence: Guide documents documentation structure, update requirements, allowed operations

- [ ] **T-P3.4.6**: Create /scripts/AGENT.md
  - Files: `/scripts/AGENT.md`
  - Commands: `test -f /scripts/AGENT.md && grep -i "automation" /scripts/AGENT.md`
  - Evidence: Guide documents scripts purpose, safety requirements, allowed operations

**Out of Scope for This Work Package:**
- Domain/feature-specific guides (created as needed)
- Automated guide enforcement (future)

**Notes:**
- Keep guides concise and actionable
- Focus on what's different/special about each folder
- Include examples of good/bad operations

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agents don't follow documented rules | Medium | High | Implement automated checks in P6, peer review all agent work |
| Capabilities too restrictive, block progress | Low | Medium | Start strict, relax based on experience, use waivers |
| Role definitions unclear, cause confusion | Medium | Medium | Provide clear examples, visual role matrix, training |
| Folder-level guides not comprehensive | Medium | Low | Iterate based on agent feedback, add guides as needed |
| Three-pass code generation too slow | Low | Medium | Allow single-pass for trivial changes with explicit justification |
| Log requirements too burdensome | Medium | Medium | Automate log generation, provide templates, make it easy |

## Definition of Done

- [ ] All WP-P3.1 through WP-P3.4 work packages marked complete
- [ ] All agents framework documents created and committed
- [ ] All 4 agent roles documented
- [ ] All 6 folder-level guides created
- [ ] Peer review completed
- [ ] No conflicts with P0/P1 policies
- [ ] Examples included for all complex concepts
- [ ] No blockers for Phase 4 (P4)

## Notes & References

- **Related ADRs**: None yet
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: None
- **Key Decisions**:
  - Three-pass code generation enforces quality
  - Human-only roles (reviewer, release) enforce safety
  - Folder-level guides provide context without overwhelming
  - Capabilities-based model allows fine-grained control

## Next Phase

After completing P3, proceed to:
- **Phase 4 (P4)**: PR Operating System - task packets, PR templates, checklists
