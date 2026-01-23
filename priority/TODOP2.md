# Phase 2: Manifest + Command Resolution

## Phase Metadata

- **Phase**: P2
- **Priority**: Critical (P0)
- **Overall Status**: Not Started
- **Owner**: DevOps Lead
- **Dependencies**: P0 (Master Handoff Skeleton)
- **Target Completion**: Sprint 2

## Scope

### In Scope:
- Create /.repo/repo.manifest.yaml with comprehensive configuration
- Configure repo metadata (ships, ship_kind, release_protects)
- Define canonical commands (install, check:quick, check:ci, check:release, check:governance, check:boundaries, check:security)
- Configure verify_profiles (quick, ci, release, governance)
- Configure tests, budgets, security, and boundaries
- Resolve all <FILL_FROM_REPO> placeholders with actual commands
- Create /.repo/docs/standards/manifest.md documentation

### Out of Scope:
- Implementation of governance-verify tool (P6)
- Implementation of boundary checker tool (P6)
- Implementation of security scanner tool (P6)
- CI/CD automation setup (P6)

## Success Criteria

- [ ] repo.manifest.yaml created with all required sections
- [ ] All canonical commands defined and verified
- [ ] All <FILL_FROM_REPO> placeholders resolved with actual commands
- [ ] Verify profiles configured (quick, ci, release, governance)
- [ ] Tests, budgets, security, and boundaries configured
- [ ] manifest.md standards documentation created
- [ ] All commands execute successfully

## Work Packages

### WP-P2.1: Manifest Creation and Structure

**Block**: Configuration  
**Priority**: P0  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1, WP-P0.3, WP-P0.5, WP-P0.6
- Blocks: WP-P2.2, WP-P2.3

**Description:**
Create the repo.manifest.yaml file with comprehensive configuration for metadata, prerequisites, canonical commands, verify profiles, tests, budgets, security, and boundaries.

**Acceptance Criteria:**
- [ ] /.repo/repo.manifest.yaml created with valid YAML structure
- [ ] Repo metadata section complete
- [ ] Prerequisites section complete
- [ ] Canonical commands section complete
- [ ] Verify_profiles section complete
- [ ] Tests section complete
- [ ] Budgets section complete
- [ ] Security section complete
- [ ] Boundaries section complete

**Tasks:**
- [ ] **T-P2.1.1**: Create /.repo/repo.manifest.yaml with base structure
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yamllint /.repo/repo.manifest.yaml`
  - Evidence: Valid YAML file created

- [ ] **T-P2.1.2**: Configure repo metadata (ships, ship_kind, release_protects)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.repo' /.repo/repo.manifest.yaml`
  - Evidence: Metadata section complete with ships: true, ship_kind, release_protects

- [ ] **T-P2.1.3**: Configure prerequisites (package_manager, runtime_pinned, platform_tools)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.prerequisites' /.repo/repo.manifest.yaml`
  - Evidence: Prerequisites section complete

- [ ] **T-P2.1.4**: Define canonical commands structure
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.canonical_commands' /.repo/repo.manifest.yaml`
  - Evidence: All 7 canonical commands defined (install, check:quick, check:ci, check:release, check:governance, check:boundaries, check:security)

- [ ] **T-P2.1.5**: Configure verify_profiles (quick, ci, release, governance)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.verify_profiles' /.repo/repo.manifest.yaml`
  - Evidence: All 4 profiles configured

- [ ] **T-P2.1.6**: Configure tests (required_level: unit+integration)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.tests' /.repo/repo.manifest.yaml`
  - Evidence: Tests section configured

- [ ] **T-P2.1.7**: Configure budgets (mode, enforcement, fallback_to_default)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.budgets' /.repo/repo.manifest.yaml`
  - Evidence: Budgets section configured with strict + fallback

- [ ] **T-P2.1.8**: Configure security settings (every_pr, release_includes_security, dependency_vulns_always_hitl)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.security' /.repo/repo.manifest.yaml`
  - Evidence: Security section configured

- [ ] **T-P2.1.9**: Configure boundaries (enforcement, edges_model, edges array)
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.boundaries' /.repo/repo.manifest.yaml`
  - Evidence: Boundaries section configured with hybrid model

**Out of Scope for This Work Package:**
- Actual command resolution (WP-P2.2)
- Standards documentation (WP-P2.3)

**Notes:**
- Start with placeholders (<FILL_FROM_REPO>) for commands
- Validate YAML structure before proceeding
- Reference P0 configuration for settings

---

### WP-P2.2: Command Resolution

**Block**: Configuration  
**Priority**: P0  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: L (16-40 hours)  
**Risk**: 🔴 High

**Dependencies:**
- Requires: WP-P2.1
- Blocks: None

**Description:**
Resolve all <FILL_FROM_REPO> placeholders with actual commands from package.json, Makefile, or CI configuration. Verify each command works as expected.

**Acceptance Criteria:**
- [ ] All <FILL_FROM_REPO> placeholders replaced
- [ ] Install command verified (runs successfully)
- [ ] check:quick verified (fast build, < 5 minutes)
- [ ] check:ci verified (quick + tests + full build)
- [ ] check:release verified (ci + security + budgets)
- [ ] check:governance verified (runs governance checks)
- [ ] check:boundaries verified (runs boundary checks)
- [ ] check:security verified (dep scan + secrets scan + forbidden patterns)
- [ ] No <UNKNOWN> placeholders remain

**Tasks:**
- [ ] **T-P2.2.1**: Identify actual commands from package.json/Makefile/CI
  - Files: `package.json`, `Makefile`, `.github/workflows/`
  - Commands: `cat package.json | jq '.scripts'`, `make -n`, `cat .github/workflows/*.yml`
  - Evidence: List of available commands documented

- [ ] **T-P2.2.2**: Replace <FILL_FROM_REPO> for install command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `yq '.canonical_commands.install' /.repo/repo.manifest.yaml`
  - Evidence: Real install command (e.g., npm install, pip install -r requirements.txt)

- [ ] **T-P2.2.3**: Replace <FILL_FROM_REPO> and verify check:quick command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: Command from manifest (should complete in < 5 min)
  - Evidence: Quick check runs successfully and fast

- [ ] **T-P2.2.4**: Replace <FILL_FROM_REPO> and verify check:ci command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: Command from manifest
  - Evidence: CI check runs successfully (includes quick + tests + full build)

- [ ] **T-P2.2.5**: Replace <FILL_FROM_REPO> and verify check:release command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: Command from manifest
  - Evidence: Release check runs successfully (includes ci + security + budgets)

- [ ] **T-P2.2.6**: Replace <FILL_FROM_REPO> and verify check:governance command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: Command from manifest (or mark <UNKNOWN> if not implemented)
  - Evidence: Governance check command defined (may be stub for P6)

- [ ] **T-P2.2.7**: Replace <FILL_FROM_REPO> and verify check:boundaries command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: Command from manifest (or mark <UNKNOWN> if not implemented)
  - Evidence: Boundary check command defined (may be stub for P6)

- [ ] **T-P2.2.8**: Replace <FILL_FROM_REPO> and verify check:security command
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: Command from manifest
  - Evidence: Security check runs (dep scan + secrets scan + forbidden patterns)

- [ ] **T-P2.2.9**: Validate no <UNKNOWN> or <FILL_FROM_REPO> remain
  - Files: `/.repo/repo.manifest.yaml`
  - Commands: `grep -E "<UNKNOWN>|<FILL_FROM_REPO>" /.repo/repo.manifest.yaml`
  - Evidence: No placeholders found (exit code 1)

**Out of Scope for This Work Package:**
- Implementation of missing tools (mark as <UNKNOWN> and create HITL)
- CI/CD automation (P6)

**Notes:**
- If command doesn't exist, mark as <UNKNOWN> and create HITL item
- Don't guess commands - verify they exist and work
- Test each command before committing
- Document any assumptions in notes

---

### WP-P2.3: Manifest Standards Documentation

**Block**: Documentation  
**Priority**: P1  
**Status**: Not Started  
**Owner**: Technical Writer  
**Effort**: M (8-16 hours)  
**Risk**: 🟢 Low

**Dependencies:**
- Requires: WP-P2.1, WP-P2.2
- Blocks: None

**Description:**
Create comprehensive documentation for the manifest standard including non-negotiable rules, command resolution process, command requirements, placeholder meanings, merge blocking conditions, and minimal acceptance check.

**Acceptance Criteria:**
- [ ] /.repo/docs/standards/manifest.md created
- [ ] Non-negotiable rule documented (no guessing)
- [ ] Command resolution process documented (5-step process)
- [ ] Each canonical command's purpose documented
- [ ] Placeholder meanings documented (<FILL_FROM_REPO>, <UNKNOWN>)
- [ ] Merge blocking conditions documented
- [ ] Minimal acceptance check documented

**Tasks:**
- [ ] **T-P2.3.1**: Create /.repo/docs/standards/manifest.md
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `test -f /.repo/docs/standards/manifest.md && wc -l /.repo/docs/standards/manifest.md`
  - Evidence: File exists with structure

- [ ] **T-P2.3.2**: Document non-negotiable rule (no guessing)
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `grep -i "non-negotiable" /.repo/docs/standards/manifest.md`
  - Evidence: No guessing rule documented clearly

- [ ] **T-P2.3.3**: Document command resolution process (5-step process)
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `grep -c "Step [0-9]:" /.repo/docs/standards/manifest.md` (should be 5)
  - Evidence: 5-step process documented

- [ ] **T-P2.3.4**: Document what each command must accomplish
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `grep -c "check:" /.repo/docs/standards/manifest.md` (should be ≥6)
  - Evidence: All canonical commands documented with purpose

- [ ] **T-P2.3.5**: Document placeholder meanings (<FILL_FROM_REPO>, <UNKNOWN>)
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `grep -E "FILL_FROM_REPO|UNKNOWN" /.repo/docs/standards/manifest.md`
  - Evidence: Both placeholders documented with meanings

- [ ] **T-P2.3.6**: Document merge blocking conditions
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `grep -A5 "blocking" /.repo/docs/standards/manifest.md`
  - Evidence: <UNKNOWN> blocks merge, <FILL_FROM_REPO> documented

- [ ] **T-P2.3.7**: Document minimal acceptance check
  - Files: `/.repo/docs/standards/manifest.md`
  - Commands: `grep -A3 "acceptance" /.repo/docs/standards/manifest.md`
  - Evidence: Minimal check documented (YAML valid, no <UNKNOWN>)

**Out of Scope for This Work Package:**
- Automation of manifest validation (P6)
- Manifest template for other repos (future)

**Notes:**
- Reference P0 principles (P7: UNKNOWN is first-class)
- Include examples of good/bad manifest entries
- Cross-reference with GOVERNANCE.md

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Commands don't exist in current repo | High | High | Use <UNKNOWN> placeholder, create HITL items, implement in P6 |
| Commands have different names across repos | Medium | Medium | Document naming conventions, provide aliases |
| Commands take too long (check:quick > 5 min) | Medium | Medium | Optimize or split into faster subset |
| YAML syntax errors | Low | Medium | Use yamllint, validate before committing |
| Security/governance commands not yet implemented | High | High | Mark as <UNKNOWN>, implement stubs in P6 |
| Boundaries edges not yet defined | Medium | Medium | Start with empty array, populate as boundaries are defined |

## Definition of Done

- [ ] All WP-P2.1 through WP-P2.3 work packages marked complete
- [ ] repo.manifest.yaml created and committed
- [ ] All commands verified to work (or marked <UNKNOWN> with HITL)
- [ ] No <FILL_FROM_REPO> placeholders remain
- [ ] YAML passes validation (yamllint)
- [ ] Standards documentation complete
- [ ] Peer review completed
- [ ] No blockers for Phase 3 (P3)

## Notes & References

- **Related ADRs**: None yet
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: Existing build/test/lint commands in repo
- **Key Decisions**:
  - <UNKNOWN> is acceptable and blocks merge (forces HITL)
  - <FILL_FROM_REPO> is temporary, must be resolved before merge
  - Don't guess commands - verify they work
  - Canonical commands are the contract between agents and CI

## Next Phase

After completing P2, proceed to:
- **Phase 3 (P3)**: Agents Framework - agent rules, capabilities, roles, and folder-level guides
