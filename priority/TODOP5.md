# Phase 5: Logging + Trace + Waiver + ADR Templates

## Phase Metadata

- **Phase**: P5
- **Priority**: High (P1)
- **Overall Status**: Not Started
- **Owner**: Technical Writer
- **Dependencies**: P0 (Master Handoff Skeleton), P1 (Policy Corpus)
- **Target Completion**: Sprint 3-4

## Scope

### In Scope:
- Create AGENT_LOG_TEMPLATE.md for agent logging
- Create AGENT_TRACE_SCHEMA.json for structured trace logs
- Create WAIVER_TEMPLATE.md for quality gate waivers
- Create ADR_TEMPLATE.md for architectural decision records
- Create RUNBOOK_TEMPLATE.md for operational procedures
- Create RFC_TEMPLATE.md for request for comments

### Out of Scope:
- Automation of log/trace generation (P6)
- Automation of waiver generation (P6)
- ADR governance automation (P6)
- Log analysis tools (future)

## Success Criteria

- [ ] All 6 template files created and complete
- [ ] Agent log template includes: intent, plan, actions, evidence, decisions, risks
- [ ] Trace schema includes: intent, files, commands, evidence, hitl, unknowns
- [ ] Waiver template includes: waives, why, scope, owner, expiration, remediation_plan
- [ ] ADR template includes: context, decision, consequences, modules, boundary_impact
- [ ] All templates follow token-optimized format
- [ ] All templates include examples

## Work Packages

### WP-P5.1: Agent Log Template

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.2, WP-P1.2
- Blocks: None

**Description:**
Create agent log template for documenting agent work. Logs provide narrative explanation of what the agent did and why.

**Acceptance Criteria:**
- [ ] /.repo/templates/AGENT_LOG_TEMPLATE.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: intent, plan, actions, evidence, decisions, risks, follow_ups, reasoning_summary, notes
- [ ] Example log included

**Tasks:**
- [ ] **T-P5.1.1**: Create /.repo/templates/AGENT_LOG_TEMPLATE.md
  - Files: `/.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Commands: `test -f /.repo/templates/AGENT_LOG_TEMPLATE.md && wc -l /.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Evidence: File exists with template structure

- [ ] **T-P5.1.2**: Define template structure with all required sections
  - Files: `/.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Commands: `grep -c "^## " /.repo/templates/AGENT_LOG_TEMPLATE.md` (should be ≥8)
  - Evidence: All sections documented
    - Intent
    - Plan
    - Actions
    - Evidence
    - Decisions
    - Risks
    - Follow Ups
    - Reasoning Summary
    - Notes

- [ ] **T-P5.1.3**: Add example log
  - Files: `/.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Commands: `grep -A20 "Example" /.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Evidence: Complete example log included

- [ ] **T-P5.1.4**: Document when logs are required
  - Files: `/.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Commands: `grep -i "required" /.repo/templates/AGENT_LOG_TEMPLATE.md`
  - Evidence: Requirements documented (P24: Logs Required for Non-Docs)

**Out of Scope for This Work Package:**
- Automated log generation (P6)
- Log validation automation (P6)

**Notes:**
- Logs enforce P24 (Logs Required for Non-Docs)
- Logs are human-readable narrative, traces are machine-readable
- Include filepaths for traceability

---

### WP-P5.2: Agent Trace Schema

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.2, WP-P1.2
- Blocks: None

**Description:**
Create JSON schema for agent trace logs. Trace logs are structured, machine-readable records of agent actions for automation and verification.

**Acceptance Criteria:**
- [ ] /.repo/templates/AGENT_TRACE_SCHEMA.json created
- [ ] Valid JSON schema with required fields
- [ ] Required fields: intent, files, commands, evidence, hitl, unknowns
- [ ] Schema includes field descriptions and constraints
- [ ] Example trace JSON included

**Tasks:**
- [ ] **T-P5.2.1**: Create /.repo/templates/AGENT_TRACE_SCHEMA.json
  - Files: `/.repo/templates/AGENT_TRACE_SCHEMA.json`
  - Commands: `cat /.repo/templates/AGENT_TRACE_SCHEMA.json | jq .`
  - Evidence: Valid JSON file created

- [ ] **T-P5.2.2**: Define JSON schema with required fields
  - Files: `/.repo/templates/AGENT_TRACE_SCHEMA.json`
  - Commands: `cat /.repo/templates/AGENT_TRACE_SCHEMA.json | jq '.required'`
  - Evidence: Required fields defined: intent, files, commands, evidence, hitl, unknowns

- [ ] **T-P5.2.3**: Add field descriptions and constraints
  - Files: `/.repo/templates/AGENT_TRACE_SCHEMA.json`
  - Commands: `cat /.repo/templates/AGENT_TRACE_SCHEMA.json | jq '.properties'`
  - Evidence: All fields have description, type, and constraints

- [ ] **T-P5.2.4**: Create example trace JSON
  - Files: `/.repo/templates/AGENT_TRACE_EXAMPLE.json`
  - Commands: `cat /.repo/templates/AGENT_TRACE_EXAMPLE.json | jq .`
  - Evidence: Example trace JSON created and validates against schema

**Out of Scope for This Work Package:**
- Automated trace generation (P6)
- Trace validation implementation (P6)

**Notes:**
- Trace logs are machine-readable, logs are human-readable
- Trace enables automation and verification
- Schema validation will be implemented in P6

---

### WP-P5.3: Waiver Template

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Quality Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.3, WP-P0.4, WP-P1.3
- Blocks: None

**Description:**
Create waiver template for documenting quality gate exceptions. Waivers must be rare, temporary, and have remediation plans.

**Acceptance Criteria:**
- [ ] /.repo/templates/WAIVER_TEMPLATE.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: waives, why, scope, owner, expiration, remediation_plan, link, notes
- [ ] Example waiver included

**Tasks:**
- [ ] **T-P5.3.1**: Create /.repo/templates/WAIVER_TEMPLATE.md
  - Files: `/.repo/templates/WAIVER_TEMPLATE.md`
  - Commands: `test -f /.repo/templates/WAIVER_TEMPLATE.md && wc -l /.repo/templates/WAIVER_TEMPLATE.md`
  - Evidence: File exists with template structure

- [ ] **T-P5.3.2**: Define template structure with all required sections
  - Files: `/.repo/templates/WAIVER_TEMPLATE.md`
  - Commands: `grep -c "^## " /.repo/templates/WAIVER_TEMPLATE.md` (should be ≥7)
  - Evidence: All sections documented
    - Waives
    - Why
    - Scope
    - Owner
    - Expiration
    - Remediation Plan
    - Link
    - Notes

- [ ] **T-P5.3.3**: Add example waiver
  - Files: `/.repo/templates/WAIVER_TEMPLATE.md`
  - Commands: `grep -A15 "Example" /.repo/templates/WAIVER_TEMPLATE.md`
  - Evidence: Complete example waiver included

- [ ] **T-P5.3.4**: Document waiver policy
  - Files: `/.repo/templates/WAIVER_TEMPLATE.md`
  - Commands: `grep -i "rare.*temporary" /.repo/templates/WAIVER_TEMPLATE.md`
  - Evidence: P22 policy documented (Waivers Rare + Temporary)

**Out of Scope for This Work Package:**
- Automated waiver generation (P6)
- Waiver expiration automation (P6)

**Notes:**
- Waivers enforce P22 (Waivers Rare + Temporary)
- All waivers must have expiration date
- Non-waiverable gates: security, secrets (P1)

---

### WP-P5.4: ADR Template

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Architect  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.2, WP-P0.6, WP-P1.2
- Blocks: None

**Description:**
Create ADR (Architectural Decision Record) template for documenting significant decisions. ADRs enforce P16 (Decisions Written Down) and P23 (ADR Required When Triggered).

**Acceptance Criteria:**
- [ ] /.repo/templates/ADR_TEMPLATE.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: context, decision_drivers, options, decision, consequences, modules, commands, migration, boundary_impact, hitl
- [ ] Example ADR included

**Tasks:**
- [ ] **T-P5.4.1**: Create /.repo/templates/ADR_TEMPLATE.md
  - Files: `/.repo/templates/ADR_TEMPLATE.md`
  - Commands: `test -f /.repo/templates/ADR_TEMPLATE.md && wc -l /.repo/templates/ADR_TEMPLATE.md`
  - Evidence: File exists with template structure

- [ ] **T-P5.4.2**: Define template structure with all required sections
  - Files: `/.repo/templates/ADR_TEMPLATE.md`
  - Commands: `grep -c "^## " /.repo/templates/ADR_TEMPLATE.md` (should be ≥9)
  - Evidence: All sections documented
    - Context
    - Decision Drivers
    - Options
    - Decision
    - Consequences
    - Modules
    - Commands
    - Migration
    - Boundary Impact
    - HITL

- [ ] **T-P5.4.3**: Add example ADR
  - Files: `/.repo/templates/ADR_TEMPLATE.md`
  - Commands: `grep -A30 "Example" /.repo/templates/ADR_TEMPLATE.md`
  - Evidence: Complete example ADR included

- [ ] **T-P5.4.4**: Document ADR triggers
  - Files: `/.repo/templates/ADR_TEMPLATE.md`
  - Commands: `grep -A10 "trigger" /.repo/templates/ADR_TEMPLATE.md`
  - Evidence: P23 triggers documented (cross-feature import, API changes, schema changes, etc.)

**Out of Scope for This Work Package:**
- ADR governance automation (P6)
- ADR index maintenance automation (P6)

**Notes:**
- ADRs enforce P16 (Decisions Written Down) and P23 (ADR Required When Triggered)
- Token-optimized format: concise, scannable
- Include boundary impact for traceability

---

### WP-P5.5: Runbook Template

**Block**: Documentation  
**Priority**: P1  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.2, WP-P1.2
- Blocks: None

**Description:**
Create runbook template for operational procedures. Runbooks document how to perform operational tasks and handle incidents.

**Acceptance Criteria:**
- [ ] /.repo/templates/RUNBOOK_TEMPLATE.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: title, summary, steps, rollback, verification, notes
- [ ] Example runbook included

**Tasks:**
- [ ] **T-P5.5.1**: Create /.repo/templates/RUNBOOK_TEMPLATE.md
  - Files: `/.repo/templates/RUNBOOK_TEMPLATE.md`
  - Commands: `test -f /.repo/templates/RUNBOOK_TEMPLATE.md && wc -l /.repo/templates/RUNBOOK_TEMPLATE.md`
  - Evidence: File exists with template structure

- [ ] **T-P5.5.2**: Define template structure with all required sections
  - Files: `/.repo/templates/RUNBOOK_TEMPLATE.md`
  - Commands: `grep -c "^## " /.repo/templates/RUNBOOK_TEMPLATE.md` (should be ≥5)
  - Evidence: All sections documented
    - Title
    - Summary
    - Steps
    - Rollback
    - Verification
    - Notes

- [ ] **T-P5.5.3**: Add example runbook
  - Files: `/.repo/templates/RUNBOOK_TEMPLATE.md`
  - Commands: `grep -A20 "Example" /.repo/templates/RUNBOOK_TEMPLATE.md`
  - Evidence: Complete example runbook included

**Out of Scope for This Work Package:**
- Runbook automation (future)
- Runbook validation (future)

**Notes:**
- Runbooks enforce P12 (Rollback Thinking)
- Include verification steps (P6: Evidence Over Vibes)
- Keep steps clear and actionable

---

### WP-P5.6: RFC Template

**Block**: Documentation  
**Priority**: P2  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.2, WP-P1.2
- Blocks: None

**Description:**
Create RFC (Request for Comments) template for proposing significant changes. RFCs facilitate discussion before implementation.

**Acceptance Criteria:**
- [ ] /.repo/templates/RFC_TEMPLATE.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: title, problem, proposed_solution, alternatives, impact, risks, notes
- [ ] Example RFC included

**Tasks:**
- [ ] **T-P5.6.1**: Create /.repo/templates/RFC_TEMPLATE.md
  - Files: `/.repo/templates/RFC_TEMPLATE.md`
  - Commands: `test -f /.repo/templates/RFC_TEMPLATE.md && wc -l /.repo/templates/RFC_TEMPLATE.md`
  - Evidence: File exists with template structure

- [ ] **T-P5.6.2**: Define template structure with all required sections
  - Files: `/.repo/templates/RFC_TEMPLATE.md`
  - Commands: `grep -c "^## " /.repo/templates/RFC_TEMPLATE.md` (should be ≥6)
  - Evidence: All sections documented
    - Title
    - Problem
    - Proposed Solution
    - Alternatives
    - Impact
    - Risks
    - Notes

- [ ] **T-P5.6.3**: Add example RFC
  - Files: `/.repo/templates/RFC_TEMPLATE.md`
  - Commands: `grep -A25 "Example" /.repo/templates/RFC_TEMPLATE.md`
  - Evidence: Complete example RFC included

**Out of Scope for This Work Package:**
- RFC approval workflow (future)
- RFC tracking system (future)

**Notes:**
- RFCs facilitate discussion before ADRs
- RFCs are optional, ADRs are required (P23)
- Include alternatives considered (good decision-making)

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Templates too verbose, not used consistently | Medium | Medium | Token-optimize all templates, use bullets, clear structure |
| Trace schema too rigid, doesn't fit all cases | Low | Medium | Include "notes" field for flexibility, iterate based on usage |
| Waivers used too frequently | Medium | High | Enforce P22 (Rare + Temporary), peer review all waivers |
| ADRs not written when required | Medium | High | Document clear triggers (P23), implement checks in P6 |
| Templates not discoverable | Low | Low | Document in DOCS_INDEX.md, link from GOVERNANCE.md |
| JSON schema validation fails on valid traces | Low | Medium | Test schema thoroughly, include multiple examples |

## Definition of Done

- [ ] All WP-P5.1 through WP-P5.6 work packages marked complete
- [ ] All 6 template files created and committed
- [ ] All templates include complete structure and examples
- [ ] Peer review completed on all templates
- [ ] Templates follow token-optimized format
- [ ] JSON schema validated
- [ ] No blockers for Phase 6 (P6)

## Notes & References

- **Related ADRs**: None yet
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: None
- **Key Decisions**:
  - Logs are narrative (human), traces are structured (machine)
  - All templates token-optimized for efficiency
  - Waivers must be rare, temporary, with remediation
  - ADRs required for P23 triggers (cross-feature, API, schema, etc.)

## Next Phase

After completing P5, proceed to:
- **Phase 6 (P6)**: Automation Stubs - CI configuration, automation scripts, validation tools
