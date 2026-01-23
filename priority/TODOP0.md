# Phase 0: Master Handoff Skeleton + Locked Decisions

## Phase Metadata

- **Phase**: P0
- **Priority**: Critical (P0)
- **Overall Status**: Not Started
- **Owner**: System Architect
- **Dependencies**: None (foundational phase)
- **Target Completion**: Sprint 1

## Scope

### In Scope:
- Establish core /.repo directory structure and authority chain
- Implement foundational principles (P3-P25) across all documentation
- Configure quality gates, security baseline, and boundaries
- Set up waivers system and HITL framework
- Establish enhancements (location anchors, code anchors, navigation aids)

### Out of Scope:
- Detailed policy documentation (Phase 1/P1)
- Manifest command resolution (Phase 2/P2)
- Agent-specific guides (Phase 3/P3)
- PR templates and workflows (Phase 4/P4)
- Automation implementation (Phase 6/P6)

## Success Criteria

- [ ] /.repo directory structure exists with all required subdirectories
- [ ] Authority chain is documented and enforced
- [ ] All 25 principles (P3-P25) are configured and traceable
- [ ] Quality gates, security baseline, and boundaries are configured
- [ ] Waivers system is operational with auto-generation capability
- [ ] HITL system is configured with index and items directory

## Work Packages

### WP-P0.1: Core Infrastructure Setup

**Block**: Infrastructure  
**Priority**: P0  
**Status**: Not Started  
**Owner**: System Architect  
**Effort**: M (8-16 hours)  
**Risk**: 🔴 High

**Dependencies:**
- Requires: None
- Blocks: All other work packages in P0

**Description:**
Establish the foundational /.repo directory structure and authority chain. This is the bedrock that all other phases depend on.

**Acceptance Criteria:**
- [ ] /.repo directory structure created with all subdirectories
- [ ] Authority chain documented: Manifest > Agents > Policy > Standards > Product
- [ ] Non-coder plain English requirement established
- [ ] Filepath requirement documented for all artifacts
- [ ] Small increments workflow defined

**Tasks:**
- [ ] **T-P0.1.1**: Create /.repo directory structure
  - Files: `/.repo/`, `/.repo/policy/`, `/.repo/agents/`, `/.repo/docs/`, `/.repo/templates/`, `/.repo/automation/`, `/.repo/hitl/`, `/.repo/archive/`
  - Commands: `tree /.repo -L 2`
  - Evidence: All directories exist and are committed

- [ ] **T-P0.1.2**: Document authority chain
  - Files: `/.repo/GOVERNANCE.md`
  - Commands: `grep -i "authority" /.repo/GOVERNANCE.md`
  - Evidence: Manifest > Agents > Policy > Standards > Product hierarchy documented

- [ ] **T-P0.1.3**: Establish non-coder plain English requirement
  - Files: `/.repo/GOVERNANCE.md`, `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -i "plain english" /.repo/GOVERNANCE.md`
  - Evidence: Plain English requirement documented in governance

- [ ] **T-P0.1.4**: Set up filepath requirement standard
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -i "filepath" /.repo/policy/PRINCIPLES.md`
  - Evidence: Filepath requirement documented for PRs, Task Packets, logs, ADRs, waivers

- [ ] **T-P0.1.5**: Establish deliver small increments workflow
  - Files: `/.repo/GOVERNANCE.md`
  - Commands: `grep -i "incremental" /.repo/GOVERNANCE.md`
  - Evidence: Small increments workflow documented

**Out of Scope for This Work Package:**
- Detailed policy documentation content (P1)
- Agent-specific configuration (P3)
- Template implementations (P5)

**Notes:**
- This is the most critical work package - everything depends on it
- Must be completed before any other work can proceed
- Review with stakeholders before proceeding

---

### WP-P0.2: Principles Implementation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Technical Lead  
**Effort**: L (16-40 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1
- Blocks: WP-P0.3, WP-P0.4, WP-P0.5, WP-P0.6

**Description:**
Implement all 23 foundational principles (P3-P25) with documentation and configuration. These principles guide all development work and must be clearly defined and traceable.

**Acceptance Criteria:**
- [ ] All 23 principles documented with plain English descriptions
- [ ] Each principle has implementation guidance
- [ ] Principles are cross-referenced in relevant documents
- [ ] Verification method documented for each principle

**Tasks:**
- [ ] **T-P0.2.1**: Implement P3: One Change Type Per PR
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P3:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P3 documented with examples

- [ ] **T-P0.2.2**: Implement P4: Make It Shippable
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P4:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P4 documented with criteria

- [ ] **T-P0.2.3**: Implement P5: Don't Break Surprises
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P5:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P5 documented with examples

- [ ] **T-P0.2.4**: Implement P6: Evidence Over Vibes
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P6:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P6 documented with verification requirements

- [ ] **T-P0.2.5**: Implement P7: UNKNOWN Is a First-Class State
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P7:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P7 documented with HITL routing rules

- [ ] **T-P0.2.6**: Implement P8: Read Repo First
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P8:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P8 documented with mandatory steps

- [ ] **T-P0.2.7**: Implement P9: Assumptions Must Be Declared
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P9:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P9 documented with declaration requirements

- [ ] **T-P0.2.8**: Implement P10: Risk Triggers a Stop
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P10:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P10 documented with escalation process

- [ ] **T-P0.2.9**: Implement P11: Prefer Guardrails Over Heroics
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P11:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P11 documented with automation-first approach

- [ ] **T-P0.2.10**: Implement P12: Rollback Thinking
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P12:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P12 documented with rollback requirements

- [ ] **T-P0.2.11**: Implement P13: Respect Boundaries by Default
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P13:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P13 documented with boundary rules

- [ ] **T-P0.2.12**: Implement P14: Localize Complexity (Option B)
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P14:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P14 documented with Option B strategy

- [ ] **T-P0.2.13**: Implement P15: Consistency Beats Novelty
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P15:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P15 documented with consistency guidelines

- [ ] **T-P0.2.14**: Implement P16: Decisions Written Down (Token-Optimized)
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P16:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P16 documented with ADR requirements

- [ ] **T-P0.2.15**: Implement P17: PR Narration
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P17:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P17 documented with narration template

- [ ] **T-P0.2.16**: Implement P18: No Silent Scope Creep
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P18:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P18 documented with scope change process

- [ ] **T-P0.2.17**: Implement P19: Docs Age With Code
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P19:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P19 documented with update requirements

- [ ] **T-P0.2.18**: Implement P20: Examples Are Contracts
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P20:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P20 documented with example maintenance rules

- [ ] **T-P0.2.19**: Implement P21: Naming Matters
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P21:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P21 documented with naming conventions

- [ ] **T-P0.2.20**: Implement P22: Waivers Rare + Temporary
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P22:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P22 documented with waiver policy

- [ ] **T-P0.2.21**: Implement P23: ADR Required When Triggered
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P23:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P23 documented with trigger conditions

- [ ] **T-P0.2.22**: Implement P24: Logs Required for Non-Docs
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P24:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P24 documented with log requirements

- [ ] **T-P0.2.23**: Implement P25: Token-Optimized TODO Discipline
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A5 "P25:" /.repo/policy/PRINCIPLES.md`
  - Evidence: P25 documented with TODO format

**Out of Scope for This Work Package:**
- Implementation of automation to enforce principles (P6)
- Agent training on principles (P3)

**Notes:**
- Each principle should have: name, description, rationale, examples, verification method
- Cross-reference principles in quality gates and boundaries documentation

---

### WP-P0.3: Quality Gates Configuration

**Block**: Configuration  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Quality Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2
- Blocks: WP-P0.4, WP-P0.5

**Description:**
Configure quality gates for merge policy, coverage strategy, performance budgets, and required checks. These gates ensure code quality standards are maintained.

**Acceptance Criteria:**
- [ ] Merge policy configured and documented
- [ ] Coverage strategy implemented with ratcheting
- [ ] Performance budgets defined with enforcement
- [ ] Zero warnings policy configured
- [ ] Governance verification checks enabled

**Tasks:**
- [ ] **T-P0.3.1**: Configure merge policy: soft_block_with_auto_generated_waivers
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "merge_policy" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Merge policy documented with waiver auto-generation

- [ ] **T-P0.3.2**: Set up coverage strategy: gradual_ratchet
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "coverage" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Coverage ratcheting strategy documented

- [ ] **T-P0.3.3**: Configure performance budgets: strict_with_fallback_to_default
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "performance" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Performance budget strategy documented

- [ ] **T-P0.3.4**: Enforce zero warnings policy
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "warnings" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Zero warnings policy documented

- [ ] **T-P0.3.5**: Configure governance_verify_checks to run all checks
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "governance_verify" /.repo/policy/QUALITY_GATES.md`
  - Evidence: All governance checks documented and configured

**Out of Scope for This Work Package:**
- Implementation of automated quality checks (P6)
- CI/CD configuration (P6)

**Notes:**
- Soft block allows waivers but requires documentation
- Gradual ratchet: coverage cannot decrease over time
- Fallback to default prevents blocking if budgets not defined

---

### WP-P0.4: Waivers System Setup

**Block**: Infrastructure  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Governance Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P0.3
- Blocks: None

**Description:**
Set up the waivers system for handling quality gate exceptions. Waivers must be auto-generated, tracked, and expire automatically.

**Acceptance Criteria:**
- [ ] Waivers directory structure created
- [ ] Auto-generation configured for all failures
- [ ] Full history lifecycle tracking enabled
- [ ] Historical waivers directory exists

**Tasks:**
- [ ] **T-P0.4.1**: Set up auto-generate waivers for all failures
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "auto.*waiver" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Auto-waiver generation documented

- [ ] **T-P0.4.2**: Implement full_history lifecycle tracking
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -i "lifecycle" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Waiver lifecycle tracking documented

- [ ] **T-P0.4.3**: Create /waivers/historical/ directory structure
  - Files: `/waivers/`, `/waivers/historical/`
  - Commands: `tree /waivers/ -L 2`
  - Evidence: Directory structure exists

**Out of Scope for This Work Package:**
- Waiver template creation (P5)
- Automation scripts for waiver generation (P6)

**Notes:**
- Waivers should be rare and temporary (P22)
- All waivers must have expiration dates
- Historical waivers provide audit trail

---

### WP-P0.5: Security Baseline Configuration

**Block**: Security  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Security Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🔴 High

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2
- Blocks: WP-P0.7

**Description:**
Configure security baseline including dependency checks, secrets handling, security review triggers, forbidden patterns, and HITL requirements. Security is non-negotiable.

**Acceptance Criteria:**
- [ ] Dependency vulnerability checks configured (always_hitl)
- [ ] Secrets handling policy: absolute_prohibition
- [ ] Security review triggers documented and configured
- [ ] Forbidden patterns defined and enforced
- [ ] Security check frequency: every_pr
- [ ] Mandatory HITL actions documented

**Tasks:**
- [ ] **T-P0.5.1**: Configure dependency vulnerability checks (always_hitl)
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -i "dependency.*vulnerability" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Dependency check policy documented with HITL requirement

- [ ] **T-P0.5.2**: Implement secrets handling: absolute_prohibition
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -i "secrets.*prohibition" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Secrets prohibition policy documented

- [ ] **T-P0.5.3**: Set up security review triggers [1,2,4,5,6,8,9,10]
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -i "security.*trigger" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: All 8 triggers documented with meanings

- [ ] **T-P0.5.4**: Define and enforce forbidden patterns [A-H]
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -i "forbidden.*pattern" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: All forbidden patterns documented

- [ ] **T-P0.5.5**: Configure security_check_frequency: every_pr
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -i "check.*frequency" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Every PR check frequency documented

- [ ] **T-P0.5.6**: Implement mandatory HITL actions [1-8]
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -i "mandatory.*hitl" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: All 8 HITL actions documented with meanings

**Out of Scope for This Work Package:**
- Implementation of security scanning tools (P6)
- Security automation scripts (P6)

**Notes:**
- Security baseline is non-waiverable
- Any security trigger requires HITL review
- Forbidden patterns must be checked on every commit

---

### WP-P0.6: Boundaries Configuration

**Block**: Architecture  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Architect  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2
- Blocks: None

**Description:**
Configure architectural boundaries using the hybrid_domain_feature_layer model. Boundaries prevent coupling and enforce clean architecture.

**Acceptance Criteria:**
- [ ] Hybrid domain/feature/layer model documented
- [ ] Import direction enforced: ui → domain → data → shared_platform
- [ ] Cross-feature rule: ADR required
- [ ] src/platform/ shared directory created
- [ ] Structure pattern defined: src/<domain>/<feature>/<layer>/
- [ ] Enforcement method configured: hybrid_static_checker_plus_manifest
- [ ] Violation severity: waiver_plus_auto_task

**Tasks:**
- [ ] **T-P0.6.1**: Set up hybrid_domain_feature_layer model
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -i "hybrid.*domain" /.repo/policy/BOUNDARIES.md`
  - Evidence: Boundary model documented

- [ ] **T-P0.6.2**: Implement allowed import direction: ui → domain → data → shared_platform
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -i "import.*direction" /.repo/policy/BOUNDARIES.md`
  - Evidence: Import direction documented with examples

- [ ] **T-P0.6.3**: Enforce cross-feature rule: ADR required
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -i "cross.*feature" /.repo/policy/BOUNDARIES.md`
  - Evidence: Cross-feature rule documented

- [ ] **T-P0.6.4**: Create src/platform/ shared platform directory
  - Files: `src/platform/`, `src/platform/README.md`
  - Commands: `test -d src/platform && echo "exists"`
  - Evidence: Directory exists with README

- [ ] **T-P0.6.5**: Implement structure pattern: src/<domain>/<feature>/<layer>/
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -i "structure.*pattern" /.repo/policy/BOUNDARIES.md`
  - Evidence: Structure pattern documented with examples

- [ ] **T-P0.6.6**: Configure hybrid_static_checker_plus_manifest enforcement
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -i "enforcement.*method" /.repo/policy/BOUNDARIES.md`
  - Evidence: Enforcement method documented

- [ ] **T-P0.6.7**: Set up violation severity: waiver_plus_auto_task
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -i "violation.*severity" /.repo/policy/BOUNDARIES.md`
  - Evidence: Violation handling documented

**Out of Scope for This Work Package:**
- Implementation of boundary checker tool (P6)
- Migration of existing code to new structure (future)

**Notes:**
- Hybrid model provides flexibility while maintaining discipline
- Static checker catches most violations at build time
- Manifest provides source of truth for allowed edges

---

### WP-P0.7: Enhancements Implementation

**Block**: Documentation  
**Priority**: P1  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2, WP-P0.5, WP-P0.6
- Blocks: None

**Description:**
Implement enhancements to improve code navigation, safety, and iteration speed. These include location anchors, code anchors, navigation aids, safety heuristics, and iteration accelerators.

**Acceptance Criteria:**
- [ ] Location anchors implemented (file headers, filepaths)
- [ ] Code anchors implemented (region comments, named anchors)
- [ ] Navigation aids created (indexes, READMEs, full path imports)
- [ ] Safety heuristics documented (impact summary, unknowns, rollback)
- [ ] Iteration accelerators configured (patterns, verification, TODO archive)

**Tasks:**
- [ ] **T-P0.7.1**: Implement location anchors (file headers, filepaths in PRs/tasks/ADRs/waivers)
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `grep -i "location.*anchor" /.repo/docs/standards/documentation.md`
  - Evidence: Location anchor requirements documented

- [ ] **T-P0.7.2**: Add code anchors (region comments, critical code excerpts, named function anchors)
  - Files: `/.repo/docs/standards/style.md`
  - Commands: `grep -i "code.*anchor" /.repo/docs/standards/style.md`
  - Evidence: Code anchor conventions documented

- [ ] **T-P0.7.3**: Create navigation aids (domain/feature index files, directory READMEs, full path imports)
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `grep -i "navigation" /.repo/docs/standards/documentation.md`
  - Evidence: Navigation aids documented

- [ ] **T-P0.7.4**: Add safety heuristics (impact summary, explicit unknowns, rollback plan)
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -i "safety.*heuristic" /.repo/policy/PRINCIPLES.md`
  - Evidence: Safety heuristics documented

- [ ] **T-P0.7.5**: Set up iteration accelerators (pattern reference, verification commands, file touch reason, TODO archive references)
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `grep -i "iteration.*accelerator" /.repo/docs/standards/documentation.md`
  - Evidence: Iteration accelerators documented

**Out of Scope for This Work Package:**
- Retroactive application to existing code (gradual)
- Automated enforcement of enhancements (future)

**Notes:**
- Enhancements are guidelines, not hard requirements
- Apply to new code immediately, existing code gradually
- Focus on high-value, high-traffic areas first

---

### WP-P0.8: HITL System Configuration

**Block**: Infrastructure  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Process Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P0.5
- Blocks: None

**Description:**
Configure the Human-In-The-Loop (HITL) system for handling external integrations, clarifications, risks, and unknowns. HITL ensures critical decisions involve humans.

**Acceptance Criteria:**
- [ ] /.repo/policy/HITL.md index created
- [ ] /.repo/hitl/ items directory created
- [ ] auto_sync_pr_and_hitl model configured
- [ ] External system detection configured (keywords + manifest + change type)

**Tasks:**
- [ ] **T-P0.8.1**: Create /.repo/policy/HITL.md index
  - Files: `/.repo/policy/HITL.md`
  - Commands: `test -f /.repo/policy/HITL.md && echo "exists"`
  - Evidence: HITL index file exists

- [ ] **T-P0.8.2**: Create /.repo/hitl/ items directory
  - Files: `/.repo/hitl/`
  - Commands: `test -d /.repo/hitl && echo "exists"`
  - Evidence: HITL items directory exists

- [ ] **T-P0.8.3**: Implement auto_sync_pr_and_hitl model
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -i "auto.*sync" /.repo/policy/HITL.md`
  - Evidence: Auto-sync model documented

- [ ] **T-P0.8.4**: Set up external system detection (keywords + manifest + change type)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -i "external.*detection" /.repo/policy/HITL.md`
  - Evidence: Detection methods documented

**Out of Scope for This Work Package:**
- HITL template creation (P5)
- HITL automation scripts (P6)
- Detailed HITL documentation (P1)

**Notes:**
- HITL is critical for safety (P6)
- External system changes always require HITL
- HITL items block PR merge until resolved

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Directory structure conflicts with existing files | Medium | High | Audit existing structure first, resolve conflicts before creation |
| Principles too numerous to implement consistently | Medium | Medium | Prioritize P0 principles, implement others gradually |
| Quality gates too strict, blocking progress | Low | High | Use soft_block with waivers, allow gradual ratcheting |
| Security baseline missed edge cases | Medium | High | Include security review with external experts |
| Boundaries too complex for team to follow | Medium | Medium | Provide clear examples, training, and tooling support |
| HITL system creates bottlenecks | Low | Medium | Minimize HITL required, streamline approval process |

## Definition of Done

- [ ] All WP-P0.1 through WP-P0.8 work packages marked complete
- [ ] All files committed and pushed to repository
- [ ] Peer review completed on all configuration documents
- [ ] Smoke test: Can navigate /.repo structure and find all policies
- [ ] No blockers for Phase 1 (P1)
- [ ] Stakeholder sign-off obtained

## Notes & References

- **Related ADRs**: None yet (this is foundational)
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: None
- **Key Decisions**:
  - Using hybrid_domain_feature_layer for boundaries (balances flexibility and discipline)
  - Soft block with auto-waivers (allows progress while maintaining visibility)
  - UNKNOWN as first-class state (safety over speed)
  - Secrets: absolute_prohibition (no exceptions)

## Next Phase

After completing P0, proceed to:
- **Phase 1 (P1)**: Policy Corpus - detailed documentation of all policies
