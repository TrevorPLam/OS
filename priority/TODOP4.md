# Phase 4: PR Operating System

## Phase Metadata

- **Phase**: P4
- **Priority**: High (P1)
- **Overall Status**: Not Started
- **Owner**: Process Lead
- **Dependencies**: P0 (Master Handoff Skeleton), P1 (Policy Corpus), P3 (Agents Framework)
- **Target Completion**: Sprint 3

## Scope

### In Scope:
- Create task packet prompt template
- Create PR template prompt
- Create checklists for change-plan, pr-review, and incident
- Create PR_TEMPLATE.md for GitHub integration
- Document task packet structure and requirements
- Document PR structure and requirements

### Out of Scope:
- Automation of task packet generation (P6)
- Automation of PR template population (P6)
- CI/CD integration (P6)
- Agent training on templates (future)

## Success Criteria

- [ ] Task packet prompt created with complete structure
- [ ] PR template prompt created with complete structure
- [ ] All 3 checklists created (change-plan, pr-review, incident)
- [ ] PR_TEMPLATE.md created for GitHub integration
- [ ] All templates follow P0 principles (filepaths, evidence, rollback)
- [ ] Templates are token-optimized and scannable

## Work Packages

### WP-P4.1: Task Packet Prompt

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Process Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2, WP-P3.1
- Blocks: WP-P4.2, WP-P4.4

**Description:**
Create the task packet prompt template that agents use to plan work before starting implementation. Task packets enforce thinking before coding and provide clear success criteria.

**Acceptance Criteria:**
- [ ] /.repo/agents/prompts/task_packet.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: goal, non_goals, acceptance_criteria, approach, files_touched, verification_plan, risks, rollback_plan, hitl_requirements, notes
- [ ] Examples included for each section

**Tasks:**
- [ ] **T-P4.1.1**: Create /.repo/agents/prompts/task_packet.md
  - Files: `/.repo/agents/prompts/task_packet.md`
  - Commands: `test -f /.repo/agents/prompts/task_packet.md && wc -l /.repo/agents/prompts/task_packet.md`
  - Evidence: File exists with template structure

- [ ] **T-P4.1.2**: Define template structure with all required sections
  - Files: `/.repo/agents/prompts/task_packet.md`
  - Commands: `grep -c "^## " /.repo/agents/prompts/task_packet.md` (should be ≥9)
  - Evidence: All 9+ sections documented
    - Goal
    - Non-Goals
    - Acceptance Criteria
    - Approach
    - Files Touched
    - Verification Plan
    - Risks
    - Rollback Plan
    - HITL Requirements
    - Notes

- [ ] **T-P4.1.3**: Add examples for each section
  - Files: `/.repo/agents/prompts/task_packet.md`
  - Commands: `grep -c "Example:" /.repo/agents/prompts/task_packet.md` (should be ≥5)
  - Evidence: Multiple examples included

- [ ] **T-P4.1.4**: Document when task packets are required
  - Files: `/.repo/agents/prompts/task_packet.md`
  - Commands: `grep -i "required" /.repo/agents/prompts/task_packet.md`
  - Evidence: Requirements documented (all non-trivial changes)

**Out of Scope for This Work Package:**
- Automated task packet generation (P6)
- Task packet validation automation (P6)

**Notes:**
- Task packets enforce P8 (Read Repo First) and P6 (Evidence Over Vibes)
- Task packets are living documents, update during implementation
- Include filepaths for traceability (P0 requirement)

---

### WP-P4.2: PR Template Prompt

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Process Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P0.2, WP-P3.1, WP-P4.1
- Blocks: WP-P4.4

**Description:**
Create the PR template prompt that agents use when creating pull requests. PR templates enforce documentation, evidence, and traceability for all changes.

**Acceptance Criteria:**
- [ ] /.repo/agents/prompts/pr_template.md created
- [ ] Template structure defined with all required sections
- [ ] Sections: change_type, summary, task_packet, filepath_changes, verification_commands_run, evidence, risks, rollback, hitl, notes
- [ ] Examples included for each change type

**Tasks:**
- [ ] **T-P4.2.1**: Create /.repo/agents/prompts/pr_template.md
  - Files: `/.repo/agents/prompts/pr_template.md`
  - Commands: `test -f /.repo/agents/prompts/pr_template.md && wc -l /.repo/agents/prompts/pr_template.md`
  - Evidence: File exists with template structure

- [ ] **T-P4.2.2**: Define template structure with all required sections
  - Files: `/.repo/agents/prompts/pr_template.md`
  - Commands: `grep -c "^## " /.repo/agents/prompts/pr_template.md` (should be ≥9)
  - Evidence: All sections documented
    - Change Type
    - Summary
    - Task Packet
    - Filepath Changes
    - Verification Commands Run
    - Evidence
    - Risks
    - Rollback
    - HITL
    - Notes

- [ ] **T-P4.2.3**: Document change types
  - Files: `/.repo/agents/prompts/pr_template.md`
  - Commands: `grep -c "change.*type" /.repo/agents/prompts/pr_template.md`
  - Evidence: Change types listed (feature, bugfix, refactor, docs, test, config, security, api-contract, schema)

- [ ] **T-P4.2.4**: Add examples for each change type
  - Files: `/.repo/agents/prompts/pr_template.md`
  - Commands: `grep -c "Example:" /.repo/agents/prompts/pr_template.md` (should be ≥3)
  - Evidence: Multiple examples included

**Out of Scope for This Work Package:**
- Automated PR template population (P6)
- PR validation automation (P6)

**Notes:**
- PR template enforces P17 (PR Narration) and P6 (Evidence Over Vibes)
- Link to task packet for traceability
- Include verification commands and evidence (not just promises)

---

### WP-P4.3: Checklists

**Block**: Documentation  
**Priority**: P1  
**Status**: Not Started  
**Owner**: Process Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.2, WP-P3.1
- Blocks: None

**Description:**
Create checklists for change-plan, pr-review, and incident handling. Checklists ensure consistency and completeness for common processes.

**Acceptance Criteria:**
- [ ] All 3 checklist files created
- [ ] change-plan.md: checklist for planning changes
- [ ] pr-review.md: checklist for reviewing PRs
- [ ] incident.md: checklist for handling incidents
- [ ] Each checklist has clear, actionable items

**Tasks:**
- [ ] **T-P4.3.1**: Create /.repo/agents/checklists/change-plan.md
  - Files: `/.repo/agents/checklists/change-plan.md`
  - Commands: `test -f /.repo/agents/checklists/change-plan.md && grep -c "\[ \]" /.repo/agents/checklists/change-plan.md`
  - Evidence: Change planning checklist created (≥10 items)

- [ ] **T-P4.3.2**: Create /.repo/agents/checklists/pr-review.md
  - Files: `/.repo/agents/checklists/pr-review.md`
  - Commands: `test -f /.repo/agents/checklists/pr-review.md && grep -c "\[ \]" /.repo/agents/checklists/pr-review.md`
  - Evidence: PR review checklist created (≥15 items)

- [ ] **T-P4.3.3**: Create /.repo/agents/checklists/incident.md
  - Files: `/.repo/agents/checklists/incident.md`
  - Commands: `test -f /.repo/agents/checklists/incident.md && grep -c "\[ \]" /.repo/agents/checklists/incident.md`
  - Evidence: Incident handling checklist created (≥12 items)

**Out of Scope for This Work Package:**
- Automated checklist enforcement (P6)
- Additional checklists (created as needed)

**Notes:**
- Checklists enforce consistency and reduce errors
- Keep items clear, actionable, and verifiable
- Reference P0 principles and P1 policies

---

### WP-P4.4: GitHub PR Template

**Block**: Configuration  
**Priority**: P0  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P4.1, WP-P4.2
- Blocks: None

**Description:**
Create PR_TEMPLATE.md for GitHub integration. This template auto-populates when creating PRs and enforces documentation standards.

**Acceptance Criteria:**
- [ ] /.repo/templates/PR_TEMPLATE.md created
- [ ] Template structure matches pr_template.md prompt
- [ ] Template includes: title, change_type, task_packet, changes, evidence, verification_commands_run, hitl, waivers, notes
- [ ] Template uses GitHub markdown features (checklists, code blocks)

**Tasks:**
- [ ] **T-P4.4.1**: Create /.repo/templates/PR_TEMPLATE.md
  - Files: `/.repo/templates/PR_TEMPLATE.md`
  - Commands: `test -f /.repo/templates/PR_TEMPLATE.md && wc -l /.repo/templates/PR_TEMPLATE.md`
  - Evidence: PR template file created

- [ ] **T-P4.4.2**: Define template structure matching pr_template.md
  - Files: `/.repo/templates/PR_TEMPLATE.md`
  - Commands: `grep -c "^## " /.repo/templates/PR_TEMPLATE.md` (should be ≥8)
  - Evidence: All required sections included

- [ ] **T-P4.4.3**: Add GitHub markdown features
  - Files: `/.repo/templates/PR_TEMPLATE.md`
  - Commands: `grep -E "\[ \]|```" /.repo/templates/PR_TEMPLATE.md`
  - Evidence: Checklists and code blocks used

- [ ] **T-P4.4.4**: Add inline instructions and examples
  - Files: `/.repo/templates/PR_TEMPLATE.md`
  - Commands: `grep -i "<!--" /.repo/templates/PR_TEMPLATE.md`
  - Evidence: HTML comments with instructions included

**Out of Scope for This Work Package:**
- Custom GitHub Actions for PR validation (P6)
- PR template enforcement automation (P6)

**Notes:**
- Template auto-loads when creating PR in GitHub
- Use HTML comments for instructions (won't show in rendered view)
- Keep template concise but complete

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Templates too verbose, agents skip sections | Medium | Medium | Make templates scannable, use bullets, clear headers |
| Task packets not used consistently | Medium | High | Make task packets easy to create, provide examples |
| PR template not enforced, incomplete PRs merged | High | High | Implement automated checks in P6, peer review all PRs |
| Checklists too long, not practical | Low | Medium | Keep checklists focused, prioritize critical items |
| Change types unclear, inconsistent usage | Medium | Medium | Provide clear definitions, examples for each type |
| GitHub template not discoverable | Low | Low | Document location, link from README |

## Definition of Done

- [ ] All WP-P4.1 through WP-P4.4 work packages marked complete
- [ ] Task packet prompt created and committed
- [ ] PR template prompt created and committed
- [ ] All 3 checklists created and committed
- [ ] GitHub PR template created and committed
- [ ] Peer review completed
- [ ] Templates tested with sample PR
- [ ] No blockers for Phase 5 (P5)

## Notes & References

- **Related ADRs**: None yet
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: GitHub (for PR_TEMPLATE.md integration)
- **Key Decisions**:
  - Task packets required for all non-trivial changes
  - PR template enforces P17 (PR Narration)
  - Change types enforce P3 (One Change Type Per PR)
  - Verification commands required (P6: Evidence Over Vibes)

## Next Phase

After completing P4, proceed to:
- **Phase 5 (P5)**: Logging + Trace + Waiver + ADR Templates - template files for all artifacts
