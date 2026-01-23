# Phase 7: Docs Glue

## Phase Metadata

- **Phase**: P7
- **Priority**: Medium (P2)
- **Overall Status**: Not Started
- **Owner**: Technical Writer
- **Dependencies**: P0 (Master Handoff Skeleton), P1 (Policy Corpus), P5 (Templates)
- **Target Completion**: Sprint 4-5

## Scope

### In Scope:
- Create comprehensive documentation index (DOCS_INDEX.md)
- Create standards documentation (documentation.md, adr.md, api.md, style.md)
- Create ADR scaffold with README and example ADR
- Link all governance, policy, and standards documents
- Establish documentation navigation structure

### Out of Scope:
- Comprehensive API documentation (ongoing)
- Feature-specific documentation (ongoing)
- Migration guides (future)
- Video tutorials (future)

## Success Criteria

- [ ] DOCS_INDEX.md created with links to all governance/policy/standards
- [ ] All 4 standards documents created (documentation, adr, api, style)
- [ ] ADR scaffold created with README and example
- [ ] All cross-references validated
- [ ] Documentation is discoverable and navigable

## Work Packages

### WP-P7.1: Documentation Index

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P1.1, WP-P1.2, WP-P1.3, WP-P1.4, WP-P1.5, WP-P1.6
- Blocks: WP-P7.2, WP-P7.3

**Description:**
Create comprehensive documentation index that links to all governance documents, policy documents, standards, and ADR history. This is the entry point for all documentation.

**Acceptance Criteria:**
- [ ] /.repo/docs/DOCS_INDEX.md created
- [ ] Links to all governance documents (GOVERNANCE.md)
- [ ] Links to all policy documents (CONSTITUTION.md, PRINCIPLES.md, QUALITY_GATES.md, SECURITY_BASELINE.md, BOUNDARIES.md, HITL.md)
- [ ] Links to all standards (documentation.md, adr.md, api.md, style.md, manifest.md)
- [ ] Links to ADR history (/.repo/docs/adr/README.md)
- [ ] Links to templates directory
- [ ] Links to agents documentation
- [ ] All links validated

**Tasks:**
- [ ] **T-P7.1.1**: Create /.repo/docs/DOCS_INDEX.md with structure
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `test -f /.repo/docs/DOCS_INDEX.md && wc -l /.repo/docs/DOCS_INDEX.md`
  - Evidence: File exists with complete structure

- [ ] **T-P7.1.2**: Link to all governance documents
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `grep "GOVERNANCE.md" /.repo/docs/DOCS_INDEX.md`
  - Evidence: GOVERNANCE.md linked

- [ ] **T-P7.1.3**: Link to all policy documents
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `grep -c "/.repo/policy/" /.repo/docs/DOCS_INDEX.md` (should be ≥6)
  - Evidence: All 6 policy documents linked (CONSTITUTION, PRINCIPLES, QUALITY_GATES, SECURITY_BASELINE, BOUNDARIES, HITL)

- [ ] **T-P7.1.4**: Link to all standards documents
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `grep -c "/.repo/docs/standards/" /.repo/docs/DOCS_INDEX.md` (should be ≥5)
  - Evidence: All standards linked (documentation, adr, api, style, manifest)

- [ ] **T-P7.1.5**: Link to ADR history
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `grep "adr/README.md" /.repo/docs/DOCS_INDEX.md`
  - Evidence: ADR README linked

- [ ] **T-P7.1.6**: Link to templates and agents documentation
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `grep -E "templates|agents" /.repo/docs/DOCS_INDEX.md`
  - Evidence: Templates and agents sections linked

- [ ] **T-P7.1.7**: Validate all links
  - Files: `/.repo/docs/DOCS_INDEX.md`
  - Commands: `markdown-link-check /.repo/docs/DOCS_INDEX.md || manual validation`
  - Evidence: All links valid (files exist)

**Out of Scope for This Work Package:**
- Standards content creation (WP-P7.2)
- ADR scaffold (WP-P7.3)

**Notes:**
- DOCS_INDEX.md is the entry point for all documentation
- Keep index scannable and organized
- Group related documents together

---

### WP-P7.2: Standards Documentation

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: L (16-40 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.2, WP-P1.2, WP-P2.3
- Blocks: None

**Description:**
Create comprehensive standards documentation for documentation, ADR, API, and style. Standards provide guidelines for consistent practices across the codebase.

**Acceptance Criteria:**
- [ ] All 4 standards documents created
- [ ] documentation.md: docs update with code, filepaths required, examples are contracts
- [ ] adr.md: ADR triggers, template reference, numbering
- [ ] api.md: API documentation requirements, api-contract change type
- [ ] style.md: naming, no duplication, functions do one thing, comments explain WHY
- [ ] Each standard includes rationale, examples, and verification

**Tasks:**
- [ ] **T-P7.2.1**: Create /.repo/docs/standards/documentation.md
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `test -f /.repo/docs/standards/documentation.md && wc -l /.repo/docs/standards/documentation.md`
  - Evidence: File exists with complete content

- [ ] **T-P7.2.2**: Document P19 (Docs Age With Code) requirements
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `grep -i "age.*with.*code" /.repo/docs/standards/documentation.md`
  - Evidence: P19 requirements documented

- [ ] **T-P7.2.3**: Document filepaths requirement
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `grep -i "filepath" /.repo/docs/standards/documentation.md`
  - Evidence: Filepaths requirement documented

- [ ] **T-P7.2.4**: Document P20 (Examples Are Contracts) requirements
  - Files: `/.repo/docs/standards/documentation.md`
  - Commands: `grep -i "examples.*contract" /.repo/docs/standards/documentation.md`
  - Evidence: P20 requirements documented

- [ ] **T-P7.2.5**: Create /.repo/docs/standards/adr.md
  - Files: `/.repo/docs/standards/adr.md`
  - Commands: `test -f /.repo/docs/standards/adr.md && wc -l /.repo/docs/standards/adr.md`
  - Evidence: File exists with complete content

- [ ] **T-P7.2.6**: Document ADR triggers (P23)
  - Files: `/.repo/docs/standards/adr.md`
  - Commands: `grep -A10 "trigger" /.repo/docs/standards/adr.md`
  - Evidence: All ADR triggers documented (cross-feature, API, schema, etc.)

- [ ] **T-P7.2.7**: Document ADR template reference and numbering
  - Files: `/.repo/docs/standards/adr.md`
  - Commands: `grep -i "template\|numbering" /.repo/docs/standards/adr.md`
  - Evidence: Template reference and sequential numbering documented

- [ ] **T-P7.2.8**: Create /.repo/docs/standards/api.md
  - Files: `/.repo/docs/standards/api.md`
  - Commands: `test -f /.repo/docs/standards/api.md && wc -l /.repo/docs/standards/api.md`
  - Evidence: File exists with complete content

- [ ] **T-P7.2.9**: Document API documentation requirements
  - Files: `/.repo/docs/standards/api.md`
  - Commands: `grep -i "requirement" /.repo/docs/standards/api.md`
  - Evidence: API doc requirements listed (params, returns, errors, examples)

- [ ] **T-P7.2.10**: Document api-contract change type
  - Files: `/.repo/docs/standards/api.md`
  - Commands: `grep -i "api-contract" /.repo/docs/standards/api.md`
  - Evidence: api-contract change type documented (requires ADR)

- [ ] **T-P7.2.11**: Create /.repo/docs/standards/style.md
  - Files: `/.repo/docs/standards/style.md`
  - Commands: `test -f /.repo/docs/standards/style.md && wc -l /.repo/docs/standards/style.md`
  - Evidence: File exists with complete content

- [ ] **T-P7.2.12**: Document naming conventions (P21)
  - Files: `/.repo/docs/standards/style.md`
  - Commands: `grep -A5 "naming" /.repo/docs/standards/style.md`
  - Evidence: Naming standards documented

- [ ] **T-P7.2.13**: Document no duplication principle
  - Files: `/.repo/docs/standards/style.md`
  - Commands: `grep -i "duplication\|DRY" /.repo/docs/standards/style.md`
  - Evidence: DRY principle documented

- [ ] **T-P7.2.14**: Document single responsibility (functions do one thing)
  - Files: `/.repo/docs/standards/style.md`
  - Commands: `grep -i "one thing\|single" /.repo/docs/standards/style.md`
  - Evidence: Single responsibility documented

- [ ] **T-P7.2.15**: Document comment guidelines (explain WHY not WHAT)
  - Files: `/.repo/docs/standards/style.md`
  - Commands: `grep -i "comment.*why" /.repo/docs/standards/style.md`
  - Evidence: Comment guidelines documented

**Out of Scope for This Work Package:**
- Language-specific style guides (future)
- Automated style checking (future)

**Notes:**
- Standards should be prescriptive but not dogmatic
- Include examples for all guidelines
- Reference P0 principles where applicable
- Keep standards token-optimized

---

### WP-P7.3: ADR Scaffold

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Architect  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P5.4, WP-P7.2
- Blocks: None

**Description:**
Create ADR scaffold with README and example ADR. This establishes the ADR system and provides a reference implementation.

**Acceptance Criteria:**
- [ ] /.repo/docs/adr/README.md created
- [ ] README documents ADR purpose, numbering, and index
- [ ] /.repo/docs/adr/0001-example.md created using template
- [ ] Example ADR is complete and realistic
- [ ] Sequential numbering documented (0001, 0002, etc.)

**Tasks:**
- [ ] **T-P7.3.1**: Create /.repo/docs/adr/README.md
  - Files: `/.repo/docs/adr/README.md`
  - Commands: `test -f /.repo/docs/adr/README.md && wc -l /.repo/docs/adr/README.md`
  - Evidence: ADR README exists

- [ ] **T-P7.3.2**: Document ADR purpose and usage
  - Files: `/.repo/docs/adr/README.md`
  - Commands: `grep -i "purpose" /.repo/docs/adr/README.md`
  - Evidence: ADR purpose documented

- [ ] **T-P7.3.3**: Document sequential numbering (0001, 0002, etc.)
  - Files: `/.repo/docs/adr/README.md`
  - Commands: `grep -i "numbering\|sequential" /.repo/docs/adr/README.md`
  - Evidence: Sequential numbering documented

- [ ] **T-P7.3.4**: Create ADR index table
  - Files: `/.repo/docs/adr/README.md`
  - Commands: `grep "| Number |" /.repo/docs/adr/README.md`
  - Evidence: Index table exists with columns (Number, Title, Status, Date)

- [ ] **T-P7.3.5**: Create /.repo/docs/adr/0001-example.md using template
  - Files: `/.repo/docs/adr/0001-example.md`
  - Commands: `test -f /.repo/docs/adr/0001-example.md && wc -l /.repo/docs/adr/0001-example.md`
  - Evidence: Example ADR exists

- [ ] **T-P7.3.6**: Populate example ADR with realistic content
  - Files: `/.repo/docs/adr/0001-example.md`
  - Commands: `grep -c "^## " /.repo/docs/adr/0001-example.md` (should be ≥8)
  - Evidence: All ADR sections populated with example content

- [ ] **T-P7.3.7**: Add example ADR to index
  - Files: `/.repo/docs/adr/README.md`
  - Commands: `grep "0001" /.repo/docs/adr/README.md`
  - Evidence: Example ADR listed in index

**Out of Scope for This Work Package:**
- Real ADRs for the system (created as needed)
- ADR automation (future)

**Notes:**
- Example ADR should be realistic and complete
- Use sequential numbering (0001, 0002, 0003, etc.)
- Keep index table in README for quick reference
- Reference P23 (ADR Required When Triggered)

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Documentation index becomes stale | High | Medium | Automate link checking, include in CI |
| Standards too prescriptive, stifle creativity | Low | Medium | Balance prescription with pragmatism, iterate |
| ADR example not realistic enough | Medium | Low | Review with team, use real scenario |
| Links break as structure changes | Medium | High | Use relative links, validate regularly |
| Standards conflict with external guides | Low | Medium | Reference external guides, note differences |
| Documentation not discoverable | Medium | High | Link from README.md, include in onboarding |

## Definition of Done

- [ ] All WP-P7.1 through WP-P7.3 work packages marked complete
- [ ] DOCS_INDEX.md created and all links validated
- [ ] All 4 standards documents created and complete
- [ ] ADR scaffold created with README and example
- [ ] Peer review completed on all documentation
- [ ] Documentation follows token-optimized format
- [ ] No blockers for Phase 8 (P8)

## Notes & References

- **Related ADRs**: 0001-example.md (example)
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: None
- **Key Decisions**:
  - DOCS_INDEX.md is single entry point for all documentation
  - Standards are prescriptive but pragmatic
  - ADR numbering is sequential (0001, 0002, etc.)
  - All documentation token-optimized for efficiency

## Next Phase

After completing P7, proceed to:
- **Phase 8 (P8)**: Root Scaffolds - root documentation updates, TODO system
