# Phase 1: Policy Corpus (Authoritative Rules)

## Phase Metadata

- **Phase**: P1
- **Priority**: Critical (P0)
- **Overall Status**: Not Started
- **Owner**: Policy Lead
- **Dependencies**: P0 (Master Handoff Skeleton)
- **Target Completion**: Sprint 2

## Scope

### In Scope:
- Create comprehensive policy documentation in /.repo/policy/
- Document Constitution (Articles 1-8)
- Document all 25 Principles (P3-P25) with plain English descriptions
- Document Quality Gates with merge policy and coverage strategy
- Document Security Baseline with absolute prohibitions and triggers
- Document Boundaries with hybrid model and enforcement
- Document HITL system with categories, statuses, and file format

### Out of Scope:
- Implementation of enforcement automation (P6)
- Agent-specific guides (P3)
- Template files (P5)
- Manifest creation (P2)

## Success Criteria

- [ ] All 6 core policy documents created and complete
- [ ] Constitution articles documented with clear authority
- [ ] All 25 principles documented with plain English
- [ ] Quality gates documented with examples
- [ ] Security baseline documented with forbidden patterns
- [ ] Boundaries documented with practical examples
- [ ] HITL system documented with index tables

## Work Packages

### WP-P1.1: Constitution Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Policy Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1
- Blocks: WP-P1.2, WP-P1.3, WP-P1.4, WP-P1.5, WP-P1.6

**Description:**
Create the Constitution document that establishes the fundamental governance principles. This is the highest authority document that defines how decisions are made.

**Acceptance Criteria:**
- [ ] /.repo/policy/CONSTITUTION.md created
- [ ] All 8 articles documented with clear descriptions
- [ ] Authority hierarchy clearly established
- [ ] Solo founder authority documented (Article 1)
- [ ] UNKNOWN handling documented (Article 3)
- [ ] HITL for external systems documented (Article 8)

**Tasks:**
- [ ] **T-P1.1.1**: Create /.repo/policy/CONSTITUTION.md
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `test -f /.repo/policy/CONSTITUTION.md && wc -l /.repo/policy/CONSTITUTION.md`
  - Evidence: File exists with complete structure

- [ ] **T-P1.1.2**: Document Article 1: Final Authority (solo founder)
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 1" /.repo/policy/CONSTITUTION.md`
  - Evidence: Solo founder authority documented

- [ ] **T-P1.1.3**: Document Article 2: Verifiable over Persuasive
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 2" /.repo/policy/CONSTITUTION.md`
  - Evidence: Evidence-based decision making documented

- [ ] **T-P1.1.4**: Document Article 3: No Guessing (UNKNOWN handling)
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 3" /.repo/policy/CONSTITUTION.md`
  - Evidence: UNKNOWN as first-class state documented

- [ ] **T-P1.1.5**: Document Article 4: Incremental Delivery
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 4" /.repo/policy/CONSTITUTION.md`
  - Evidence: Small increments workflow documented

- [ ] **T-P1.1.6**: Document Article 5: Strict Traceability
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 5" /.repo/policy/CONSTITUTION.md`
  - Evidence: Traceability requirements documented

- [ ] **T-P1.1.7**: Document Article 6: Safety Before Speed
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 6" /.repo/policy/CONSTITUTION.md`
  - Evidence: Safety-first approach documented

- [ ] **T-P1.1.8**: Document Article 7: Per-Repo Variation Allowed
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 7" /.repo/policy/CONSTITUTION.md`
  - Evidence: Repository-specific variation rules documented

- [ ] **T-P1.1.9**: Document Article 8: HITL for External Systems
  - Files: `/.repo/policy/CONSTITUTION.md`
  - Commands: `grep -A10 "Article 8" /.repo/policy/CONSTITUTION.md`
  - Evidence: External system HITL requirement documented

**Out of Scope for This Work Package:**
- Implementation of constitutional principles (ongoing)
- Enforcement automation (P6)

**Notes:**
- Constitution is highest authority after solo founder
- Articles should be clear, concise, and actionable
- Use plain English throughout

---

### WP-P1.2: Principles Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Technical Lead  
**Effort**: L (16-40 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.2, WP-P1.1
- Blocks: WP-P1.3, WP-P1.4, WP-P1.5, WP-P1.6

**Description:**
Create comprehensive documentation for all 25 principles (P3-P25) with plain English descriptions, rationale, examples, and verification methods.

**Acceptance Criteria:**
- [ ] /.repo/policy/PRINCIPLES.md created
- [ ] Global rule documented: filepaths required everywhere
- [ ] All 25 principles documented with structure: name, description, rationale, examples, verification
- [ ] Cross-references to related policies included

**Tasks:**
- [ ] **T-P1.2.1**: Create /.repo/policy/PRINCIPLES.md with structure
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `test -f /.repo/policy/PRINCIPLES.md && wc -l /.repo/policy/PRINCIPLES.md`
  - Evidence: File exists with template structure

- [ ] **T-P1.2.2**: Document global rule: filepaths required everywhere
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -i "filepath.*required" /.repo/policy/PRINCIPLES.md`
  - Evidence: Global filepath rule documented with examples

- [ ] **T-P1.2.3**: Document all 25 principles (P3-P25) with plain English descriptions
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -c "^### P[0-9]" /.repo/policy/PRINCIPLES.md` (should be 23)
  - Evidence: All 23 principles documented (P3-P25)

**Out of Scope for This Work Package:**
- Principle enforcement automation (P6)
- Agent training materials (P3)

**Notes:**
- Each principle needs: Name, Description (plain English), Rationale (why), Examples (good/bad), Verification (how to check)
- Link to P0 implementation for cross-reference
- Use consistent format for all principles

---

### WP-P1.3: Quality Gates Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Quality Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.3, WP-P1.1
- Blocks: None

**Description:**
Create comprehensive quality gates documentation including merge policy, hard gates, waiverable gates, coverage strategy, performance budgets, warnings policy, and required checks.

**Acceptance Criteria:**
- [ ] /.repo/policy/QUALITY_GATES.md created
- [ ] Merge policy documented (soft_block_with_auto_generated_waivers)
- [ ] Hard gates (non-waiverable) documented
- [ ] Waiverable gates documented
- [ ] Coverage strategy documented (gradual_ratchet)
- [ ] Performance budgets documented (strict_with_fallback_to_default)
- [ ] Warnings policy documented (zero warnings)
- [ ] PR size policy documented
- [ ] Required checks documented

**Tasks:**
- [ ] **T-P1.3.1**: Create /.repo/policy/QUALITY_GATES.md
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `test -f /.repo/policy/QUALITY_GATES.md && wc -l /.repo/policy/QUALITY_GATES.md`
  - Evidence: File exists with complete structure

- [ ] **T-P1.3.2**: Document merge policy
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A5 "Merge Policy" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Soft block with auto-waivers documented

- [ ] **T-P1.3.3**: Document hard gates (non-waiverable)
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A10 "Hard Gates" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Non-waiverable gates listed (security, secrets)

- [ ] **T-P1.3.4**: Document waiverable gates
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A10 "Waiverable Gates" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Waiverable gates listed (coverage, performance)

- [ ] **T-P1.3.5**: Document coverage strategy
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A5 "Coverage" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Gradual ratchet strategy documented

- [ ] **T-P1.3.6**: Document performance budgets
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A5 "Performance" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Strict with fallback strategy documented

- [ ] **T-P1.3.7**: Document warnings policy
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A5 "Warnings" /.repo/policy/QUALITY_GATES.md`
  - Evidence: Zero warnings policy documented

- [ ] **T-P1.3.8**: Document PR size policy
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A5 "PR Size" /.repo/policy/QUALITY_GATES.md`
  - Evidence: PR size limits documented

- [ ] **T-P1.3.9**: Document required checks
  - Files: `/.repo/policy/QUALITY_GATES.md`
  - Commands: `grep -A10 "Required Checks" /.repo/policy/QUALITY_GATES.md`
  - Evidence: All required checks listed (build, test, lint, security, governance)

**Out of Scope for This Work Package:**
- Implementation of quality gate automation (P6)
- CI/CD configuration (P6)

**Notes:**
- Hard gates cannot be waived (security, secrets)
- Waiverable gates require documented waiver
- Gradual ratchet: coverage never decreases

---

### WP-P1.4: Security Baseline Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Security Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🔴 High

**Dependencies:**
- Requires: WP-P0.5, WP-P1.1
- Blocks: None

**Description:**
Create comprehensive security baseline documentation including absolute prohibitions, dependency vulnerability handling, security check frequency, security review triggers, forbidden patterns, mandatory HITL actions, and evidence requirements.

**Acceptance Criteria:**
- [ ] /.repo/policy/SECURITY_BASELINE.md created
- [ ] Absolute prohibitions documented (secrets/tokens/keys)
- [ ] Dependency vulnerability handling documented (always_hitl)
- [ ] Security check frequency documented (every_pr)
- [ ] Security review triggers documented with meanings [1,2,4,5,6,8,9,10]
- [ ] Forbidden patterns documented [A-H]
- [ ] Mandatory HITL actions documented with meanings [1-8]
- [ ] Evidence requirements documented

**Tasks:**
- [ ] **T-P1.4.1**: Create /.repo/policy/SECURITY_BASELINE.md
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `test -f /.repo/policy/SECURITY_BASELINE.md && wc -l /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: File exists with complete structure

- [ ] **T-P1.4.2**: Document absolute prohibitions (secrets/tokens/keys)
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -A5 "Absolute Prohibition" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Secrets prohibition documented clearly

- [ ] **T-P1.4.3**: Document dependency vulnerability handling
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -A5 "Dependency" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Always_hitl policy documented

- [ ] **T-P1.4.4**: Document security check frequency
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -A3 "Frequency" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Every_pr frequency documented

- [ ] **T-P1.4.5**: Document security review triggers with meanings
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -c "Trigger [0-9]:" /.repo/policy/SECURITY_BASELINE.md` (should be 8)
  - Evidence: All 8 triggers documented with meanings

- [ ] **T-P1.4.6**: Document forbidden patterns
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -c "Pattern [A-Z]:" /.repo/policy/SECURITY_BASELINE.md` (should be 8)
  - Evidence: All 8 forbidden patterns documented

- [ ] **T-P1.4.7**: Document mandatory HITL actions with meanings
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -c "HITL Action [0-9]:" /.repo/policy/SECURITY_BASELINE.md` (should be 8)
  - Evidence: All 8 HITL actions documented with meanings

- [ ] **T-P1.4.8**: Document evidence requirements
  - Files: `/.repo/policy/SECURITY_BASELINE.md`
  - Commands: `grep -A10 "Evidence" /.repo/policy/SECURITY_BASELINE.md`
  - Evidence: Evidence requirements documented

**Out of Scope for This Work Package:**
- Implementation of security scanning (P6)
- Security automation scripts (P6)

**Notes:**
- Security baseline is non-negotiable
- All security triggers require HITL review
- Forbidden patterns must be checked every PR
- Reference P0 configuration for trigger/pattern IDs

---

### WP-P1.5: Boundaries Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Architect  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.6, WP-P1.1
- Blocks: None

**Description:**
Create comprehensive boundaries documentation including the hybrid_domain_feature_layer model, directory pattern, allowed import direction, cross-feature rule, enforcement method, exception process, violation severity, and practical examples.

**Acceptance Criteria:**
- [ ] /.repo/policy/BOUNDARIES.md created
- [ ] hybrid_domain_feature_layer model documented
- [ ] Directory pattern documented: src/<domain>/<feature>/<layer>/
- [ ] Allowed import direction documented with examples
- [ ] Cross-feature rule documented (ADR required)
- [ ] Enforcement method documented (hybrid_static_checker_plus_manifest)
- [ ] Exception process documented (small vs large)
- [ ] Violation severity documented (waiver_plus_auto_task)
- [ ] Boundary visibility requirements documented
- [ ] Practical examples provided (allowed/forbidden patterns)

**Tasks:**
- [ ] **T-P1.5.1**: Create /.repo/policy/BOUNDARIES.md
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `test -f /.repo/policy/BOUNDARIES.md && wc -l /.repo/policy/BOUNDARIES.md`
  - Evidence: File exists with complete structure

- [ ] **T-P1.5.2**: Document hybrid_domain_feature_layer model
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A10 "Hybrid Model" /.repo/policy/BOUNDARIES.md`
  - Evidence: Model documented with rationale

- [ ] **T-P1.5.3**: Document directory pattern: src/<domain>/<feature>/<layer>/
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A5 "Directory Pattern" /.repo/policy/BOUNDARIES.md`
  - Evidence: Pattern documented with examples

- [ ] **T-P1.5.4**: Document allowed import direction with examples
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A10 "Import Direction" /.repo/policy/BOUNDARIES.md`
  - Evidence: ui → domain → data → shared_platform documented

- [ ] **T-P1.5.5**: Document cross-feature rule
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A5 "Cross-Feature" /.repo/policy/BOUNDARIES.md`
  - Evidence: ADR requirement documented

- [ ] **T-P1.5.6**: Document enforcement method
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A5 "Enforcement" /.repo/policy/BOUNDARIES.md`
  - Evidence: Hybrid static checker + manifest documented

- [ ] **T-P1.5.7**: Document exception process (small vs large)
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A10 "Exception" /.repo/policy/BOUNDARIES.md`
  - Evidence: Exception process documented with thresholds

- [ ] **T-P1.5.8**: Document violation severity
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A5 "Violation" /.repo/policy/BOUNDARIES.md`
  - Evidence: Waiver + auto-task severity documented

- [ ] **T-P1.5.9**: Document boundary visibility requirements
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -A5 "Visibility" /.repo/policy/BOUNDARIES.md`
  - Evidence: Visibility requirements documented

- [ ] **T-P1.5.10**: Provide practical examples (allowed/forbidden patterns)
  - Files: `/.repo/policy/BOUNDARIES.md`
  - Commands: `grep -c "Example:" /.repo/policy/BOUNDARIES.md` (should be ≥6)
  - Evidence: At least 6 examples (3 allowed, 3 forbidden)

**Out of Scope for This Work Package:**
- Implementation of boundary checker (P6)
- Migration of existing code (future)

**Notes:**
- Include code examples for clarity
- Show both correct and incorrect import patterns
- Reference src/platform/ for shared code

---

### WP-P1.6: HITL System Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Process Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.8, WP-P1.1
- Blocks: None

**Description:**
Create comprehensive HITL documentation including storage model, minimal effort rule, categories, statuses, merge blocking rule, role permissions, external systems detection, file format, index tables, and archiving process.

**Acceptance Criteria:**
- [ ] /.repo/policy/HITL.md created with comprehensive documentation
- [ ] Storage model documented (split, same folder)
- [ ] Minimal human effort rule documented
- [ ] Categories documented (External Integration, Clarification, Risk, Feedback, Vendor)
- [ ] Statuses documented (Pending, In Progress, Blocked, Completed, Superseded)
- [ ] Merge blocking rule documented
- [ ] Role permissions documented (agents vs human)
- [ ] External systems detection methods documented
- [ ] HITL item file format documented (required fields)
- [ ] Index tables created (Active/Archived)
- [ ] Archiving process documented

**Tasks:**
- [ ] **T-P1.6.1**: Create /.repo/policy/HITL.md
  - Files: `/.repo/policy/HITL.md`
  - Commands: `test -f /.repo/policy/HITL.md && wc -l /.repo/policy/HITL.md`
  - Evidence: File exists with complete structure

- [ ] **T-P1.6.2**: Document storage model (split, same folder)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A5 "Storage Model" /.repo/policy/HITL.md`
  - Evidence: Split model documented (/.repo/policy/HITL.md + /.repo/hitl/)

- [ ] **T-P1.6.3**: Document minimal human effort rule
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A3 "Minimal.*Effort" /.repo/policy/HITL.md`
  - Evidence: Efficiency rule documented

- [ ] **T-P1.6.4**: Document categories (External Integration, Clarification, Risk, Feedback, Vendor)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -c "Category:" /.repo/policy/HITL.md` (should be 5)
  - Evidence: All 5 categories documented with descriptions

- [ ] **T-P1.6.5**: Document statuses (Pending, In Progress, Blocked, Completed, Superseded)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -c "Status:" /.repo/policy/HITL.md` (should be 5)
  - Evidence: All 5 statuses documented with meanings

- [ ] **T-P1.6.6**: Document merge blocking rule
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A3 "Merge.*Block" /.repo/policy/HITL.md`
  - Evidence: Blocking rule documented (Pending/In Progress block merge)

- [ ] **T-P1.6.7**: Document role permissions (agents vs human)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A10 "Role.*Permission" /.repo/policy/HITL.md`
  - Evidence: Agent vs human permissions documented

- [ ] **T-P1.6.8**: Document external systems detection methods
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A5 "Detection" /.repo/policy/HITL.md`
  - Evidence: Keywords + manifest + change type documented

- [ ] **T-P1.6.9**: Document HITL item file format (required fields)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A15 "File Format" /.repo/policy/HITL.md`
  - Evidence: Required fields documented (ID, category, status, question, context, resolution)

- [ ] **T-P1.6.10**: Create index tables (Active/Archived)
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -c "| ID |" /.repo/policy/HITL.md` (should be 2)
  - Evidence: Active and Archived tables exist

- [ ] **T-P1.6.11**: Document archiving process
  - Files: `/.repo/policy/HITL.md`
  - Commands: `grep -A5 "Archiving" /.repo/policy/HITL.md`
  - Evidence: Archiving process documented

**Out of Scope for This Work Package:**
- HITL template creation (P5)
- HITL automation (P6)

**Notes:**
- HITL is critical for handling unknowns
- External system changes always require HITL
- Keep HITL overhead minimal

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Policy documents too verbose, not token-optimized | High | Medium | Use concise language, bullet points, examples. Review word count. |
| Policies conflict with each other | Medium | High | Cross-reference all policies, resolve conflicts during review |
| Security triggers too broad, create HITL bottleneck | Medium | Medium | Start with strict triggers, relax based on experience |
| Boundaries too complex to follow | Medium | Medium | Provide clear examples, visual diagrams, practical guidance |
| HITL categories not comprehensive enough | Low | Medium | Add "Other" category as catch-all, iterate based on usage |
| Plain English requirement not met | Medium | Low | Peer review by non-technical stakeholder |

## Definition of Done

- [ ] All WP-P1.1 through WP-P1.6 work packages marked complete
- [ ] All 6 policy documents created and committed
- [ ] Peer review completed on all policy documents
- [ ] Plain English review by non-technical stakeholder
- [ ] All cross-references validated
- [ ] No conflicts between policy documents
- [ ] Documentation follows token-optimized format
- [ ] Stakeholder sign-off obtained

## Notes & References

- **Related ADRs**: None yet (policies are foundational)
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: None
- **Key Decisions**:
  - Token-optimized format: concise, scannable, actionable
  - Plain English throughout for non-coder accessibility
  - Examples included for all complex concepts
  - HITL as safety mechanism for unknowns

## Next Phase

After completing P1, proceed to:
- **Phase 2 (P2)**: Manifest + Command Resolution - fillable manifest with actual commands
