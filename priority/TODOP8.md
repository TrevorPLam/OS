# Phase 8: Root Scaffolds

## Phase Metadata

- **Phase**: P8
- **Priority**: Medium (P2)
- **Overall Status**: Not Started
- **Owner**: Project Lead
- **Dependencies**: P0 (Master Handoff Skeleton), P7 (Docs Glue)
- **Target Completion**: Sprint 5

## Scope

### In Scope:
- Update /README.md to link to /.repo/DOCS_INDEX.md
- Create or update /SECURITY.md to reference security baseline
- Create or update /CODEOWNERS file
- Verify /LICENSE exists
- Create or verify TODO system (P0TODO.md, P1TODO.md, P2TODO.md, COMPLETEDTODO.md)
- Create archive directory for TODO snapshots

### Out of Scope:
- Comprehensive README content (ongoing)
- Detailed security procedures (P1 covered this)
- CODEOWNERS automation (future)
- TODO automation (future)

## Success Criteria

- [ ] README.md updated with link to DOCS_INDEX.md
- [ ] SECURITY.md created/updated with reference to security baseline
- [ ] CODEOWNERS file created/updated
- [ ] LICENSE file verified to exist
- [ ] TODO system created (4 files: P0TODO.md, P1TODO.md, P2TODO.md, COMPLETEDTODO.md)
- [ ] TODO archive directory created
- [ ] All root files follow repository conventions

## Work Packages

### WP-P8.1: Root Documentation Updates

**Block**: Documentation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: Project Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.1, WP-P7.1
- Blocks: None

**Description:**
Update root documentation files (README.md, SECURITY.md) to integrate with the governance system. These are the first files people see when visiting the repository.

**Acceptance Criteria:**
- [ ] /README.md updated with link to /.repo/DOCS_INDEX.md
- [ ] /SECURITY.md created or updated to reference /.repo/policy/SECURITY_BASELINE.md
- [ ] Both files follow repository conventions
- [ ] Links validated

**Tasks:**
- [ ] **T-P8.1.1**: Update /README.md to link to /.repo/DOCS_INDEX.md
  - Files: `/README.md`
  - Commands: `grep "DOCS_INDEX.md" /README.md`
  - Evidence: README contains link to documentation index

- [ ] **T-P8.1.2**: Add governance section to README
  - Files: `/README.md`
  - Commands: `grep -i "governance" /README.md`
  - Evidence: Governance section added with link to /.repo/GOVERNANCE.md

- [ ] **T-P8.1.3**: Create or update /SECURITY.md
  - Files: `/SECURITY.md`
  - Commands: `test -f /SECURITY.md && wc -l /SECURITY.md`
  - Evidence: SECURITY.md exists

- [ ] **T-P8.1.4**: Reference /.repo/policy/SECURITY_BASELINE.md in SECURITY.md
  - Files: `/SECURITY.md`
  - Commands: `grep "SECURITY_BASELINE.md" /SECURITY.md`
  - Evidence: Security baseline referenced

- [ ] **T-P8.1.5**: Add vulnerability reporting section to SECURITY.md
  - Files: `/SECURITY.md`
  - Commands: `grep -i "reporting" /SECURITY.md`
  - Evidence: Reporting procedures documented

- [ ] **T-P8.1.6**: Validate all links in root docs
  - Files: `/README.md`, `/SECURITY.md`
  - Commands: `markdown-link-check /README.md || manual validation`
  - Evidence: All links valid

**Out of Scope for This Work Package:**
- Comprehensive README rewrite (incremental)
- Detailed security procedures (already in P1)

**Notes:**
- Keep README concise and scannable
- Security baseline is authoritative, SECURITY.md is pointer
- Link to governance early and prominently

---

### WP-P8.2: CODEOWNERS and LICENSE

**Block**: Configuration  
**Priority**: P1  
**Status**: Not Started  
**Owner**: Project Lead  
**Effort**: XS (1-2 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: None
- Blocks: None

**Description:**
Create or update CODEOWNERS file and verify LICENSE exists. CODEOWNERS enforces review requirements, LICENSE protects the project.

**Acceptance Criteria:**
- [ ] /CODEOWNERS created or updated
- [ ] Default owner configured (* @owner)
- [ ] /.repo/ ownership configured if different
- [ ] /LICENSE verified to exist
- [ ] LICENSE type documented in README

**Tasks:**
- [ ] **T-P8.2.1**: Create or update /CODEOWNERS
  - Files: `/CODEOWNERS`
  - Commands: `test -f /CODEOWNERS && cat /CODEOWNERS`
  - Evidence: CODEOWNERS file exists

- [ ] **T-P8.2.2**: Configure default owner (* @owner)
  - Files: `/CODEOWNERS`
  - Commands: `grep "^\* " /CODEOWNERS`
  - Evidence: Default owner configured

- [ ] **T-P8.2.3**: Configure /.repo/ ownership (governance)
  - Files: `/CODEOWNERS`
  - Commands: `grep "/.repo/" /CODEOWNERS`
  - Evidence: Governance files have specific owner

- [ ] **T-P8.2.4**: Verify /LICENSE exists
  - Files: `/LICENSE`
  - Commands: `test -f /LICENSE && head -5 /LICENSE`
  - Evidence: LICENSE file exists with valid content

- [ ] **T-P8.2.5**: Document license type in README
  - Files: `/README.md`
  - Commands: `grep -i "license" /README.md`
  - Evidence: License type mentioned in README

**Out of Scope for This Work Package:**
- Complex CODEOWNERS rules (add as needed)
- License change (not governance task)

**Notes:**
- CODEOWNERS enforces human review for governance files
- Solo founder likely owns everything initially
- Can add granular rules later as team grows

---

### WP-P8.3: TODO System

**Block**: Documentation  
**Priority**: P1  
**Status**: Not Started  
**Owner**: Project Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P0.2 (P25: Token-Optimized TODO Discipline)
- Blocks: None

**Description:**
Create or verify TODO system with priority-based files (P0TODO.md, P1TODO.md, P2TODO.md, COMPLETEDTODO.md) and archive directory. This enforces P25 (Token-Optimized TODO Discipline).

**Acceptance Criteria:**
- [ ] /P0TODO.md created or verified (highest priority)
- [ ] /P1TODO.md created or verified (high priority)
- [ ] /P2TODO.md created or verified (medium priority)
- [ ] /COMPLETEDTODO.md created or verified (archive)
- [ ] /.repo/archive/todo/README.md created
- [ ] All TODO files follow token-optimized format
- [ ] TODO system documented in GOVERNANCE.md or PRINCIPLES.md

**Tasks:**
- [ ] **T-P8.3.1**: Create or verify /P0TODO.md (highest priority)
  - Files: `/P0TODO.md`
  - Commands: `test -f /P0TODO.md && wc -l /P0TODO.md`
  - Evidence: P0 TODO file exists

- [ ] **T-P8.3.2**: Create or verify /P1TODO.md (high priority)
  - Files: `/P1TODO.md`
  - Commands: `test -f /P1TODO.md && wc -l /P1TODO.md`
  - Evidence: P1 TODO file exists

- [ ] **T-P8.3.3**: Create or verify /P2TODO.md (medium priority)
  - Files: `/P2TODO.md`
  - Commands: `test -f /P2TODO.md && wc -l /P2TODO.md`
  - Evidence: P2 TODO file exists

- [ ] **T-P8.3.4**: Create or verify /COMPLETEDTODO.md (archive)
  - Files: `/COMPLETEDTODO.md`
  - Commands: `test -f /COMPLETEDTODO.md && wc -l /COMPLETEDTODO.md`
  - Evidence: Completed TODO file exists

- [ ] **T-P8.3.5**: Create /.repo/archive/todo/README.md
  - Files: `/.repo/archive/todo/README.md`
  - Commands: `test -f /.repo/archive/todo/README.md`
  - Evidence: Archive directory and README exist

- [ ] **T-P8.3.6**: Document TODO system in PRINCIPLES.md (P25)
  - Files: `/.repo/policy/PRINCIPLES.md`
  - Commands: `grep -A10 "P25" /.repo/policy/PRINCIPLES.md`
  - Evidence: P25 TODO discipline documented with file locations

- [ ] **T-P8.3.7**: Add TODO system section to GOVERNANCE.md
  - Files: `/.repo/GOVERNANCE.md`
  - Commands: `grep -i "TODO" /.repo/GOVERNANCE.md`
  - Evidence: TODO system documented in governance

**Out of Scope for This Work Package:**
- TODO automation (future)
- TODO priority enforcement (future)
- Migration of existing TODOs (separate task)

**Notes:**
- P0 = critical path, P1 = high priority, P2 = nice to have
- COMPLETEDTODO.md is for recently completed items
- Archive directory for long-term TODO snapshots
- Token-optimized format: concise, actionable, traceable

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| README becomes too long and unreadable | Medium | Medium | Keep brief, link to detailed docs, iterative refinement |
| CODEOWNERS too restrictive, blocks progress | Low | Medium | Start minimal, add rules as team grows |
| TODO files not used consistently | Medium | Medium | Document clearly, make easy to use, lead by example |
| LICENSE missing or incorrect | Low | High | Verify early, document in README |
| Links in root docs break over time | Medium | Medium | Validate regularly, include in CI |
| TODO system too complex | Low | Medium | Start simple (3 priority levels), iterate |

## Definition of Done

- [ ] All WP-P8.1 through WP-P8.3 work packages marked complete
- [ ] README.md updated with governance links
- [ ] SECURITY.md created/updated
- [ ] CODEOWNERS created/updated
- [ ] LICENSE verified to exist
- [ ] All TODO files created/verified
- [ ] TODO archive directory created
- [ ] Peer review completed
- [ ] All links validated
- [ ] No blockers for deployment

## Notes & References

- **Related ADRs**: None
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: GitHub (for CODEOWNERS integration)
- **Key Decisions**:
  - README links prominently to governance
  - SECURITY.md is pointer to authoritative security baseline
  - TODO system uses 3 priority levels (P0, P1, P2)
  - COMPLETEDTODO.md for recent completions, archive for long-term

## Next Phase

After completing P8, all phases are complete! The governance system is fully operational.

**Post-Implementation:**
- Monitor system usage and effectiveness
- Iterate on documentation based on feedback
- Implement additional automation as needed
- Train team on governance system
- Establish feedback loop for continuous improvement
