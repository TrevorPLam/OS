# Phase 6: Automation Stubs

## Phase Metadata

- **Phase**: P6
- **Priority**: High (P1)
- **Overall Status**: Not Started
- **Owner**: DevOps Lead
- **Dependencies**: P0 (Master Handoff Skeleton), P2 (Manifest), P5 (Templates)
- **Target Completion**: Sprint 4-5

## Scope

### In Scope:
- Create CI configuration for governance verification
- Create automation scripts for governance-verify
- Implement structure enforcement checking
- Implement required artifacts checking
- Implement logs validation
- Implement trace schema validation
- Implement HITL/waivers checking
- Create trace validation script

### Out of Scope:
- Full CI/CD pipeline implementation (separate project)
- Boundary checker tool (complex, needs separate phase)
- Security scanner tool (complex, needs separate phase)
- Performance budgets enforcement (future)
- Coverage ratcheting automation (future)

## Success Criteria

- [ ] governance-verify.yml CI configuration created
- [ ] governance-verify.js script created and functional
- [ ] Structure enforcement checks implemented
- [ ] Required artifacts checks implemented
- [ ] Logs validation implemented
- [ ] Trace schema validation implemented
- [ ] HITL/waivers checks implemented
- [ ] validate-agent-trace.js script created and functional
- [ ] All checks run successfully on sample data

## Work Packages

### WP-P6.1: CI Configuration

**Block**: Configuration  
**Priority**: P0  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: S (2-8 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P0.1, WP-P2.1, WP-P2.2
- Blocks: WP-P6.2

**Description:**
Create CI configuration for governance verification. This workflow runs on every PR to enforce governance rules.

**Acceptance Criteria:**
- [ ] /.repo/automation/ci/governance-verify.yml created
- [ ] Workflow triggers on pull_request events
- [ ] Install command resolved from manifest
- [ ] Governance command resolved from manifest
- [ ] Workflow fails if governance checks fail

**Tasks:**
- [ ] **T-P6.1.1**: Create /.repo/automation/ci/governance-verify.yml
  - Files: `/.repo/automation/ci/governance-verify.yml`
  - Commands: `yamllint /.repo/automation/ci/governance-verify.yml`
  - Evidence: Valid YAML workflow file created

- [ ] **T-P6.1.2**: Configure workflow triggers
  - Files: `/.repo/automation/ci/governance-verify.yml`
  - Commands: `yq '.on' /.repo/automation/ci/governance-verify.yml`
  - Evidence: Triggers on pull_request events

- [ ] **T-P6.1.3**: Replace <FILL_FROM_REPO_INSTALL> with actual install command
  - Files: `/.repo/automation/ci/governance-verify.yml`
  - Commands: `grep "install" /.repo/automation/ci/governance-verify.yml`
  - Evidence: Real install command from manifest (no placeholders)

- [ ] **T-P6.1.4**: Replace <FILL_FROM_REPO_GOVERNANCE> with actual governance command
  - Files: `/.repo/automation/ci/governance-verify.yml`
  - Commands: `grep "governance" /.repo/automation/ci/governance-verify.yml`
  - Evidence: Real governance command from manifest (no placeholders)

- [ ] **T-P6.1.5**: Configure failure handling
  - Files: `/.repo/automation/ci/governance-verify.yml`
  - Commands: `grep "fail" /.repo/automation/ci/governance-verify.yml`
  - Evidence: Workflow fails if checks fail

**Out of Scope for This Work Package:**
- Full CI/CD pipeline (separate project)
- Notification configuration (future)
- Deployment steps (not governance)

**Notes:**
- Reference manifest for commands (P2)
- Keep workflow simple and fast
- Fail fast on governance violations

---

### WP-P6.2: Governance Verify Script

**Block**: Automation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: L (16-40 hours)  
**Risk**: 🔴 High

**Dependencies:**
- Requires: WP-P0.1, WP-P5.2, WP-P6.1
- Blocks: WP-P6.3

**Description:**
Create governance-verify.js script that checks structure enforcement, required artifacts, logs validation, trace schema validation, and HITL/waivers. This is the core automation script.

**Acceptance Criteria:**
- [ ] /.repo/automation/scripts/governance-verify.js created
- [ ] Structure enforcement implemented (/.repo/ directories exist)
- [ ] Required artifacts checking implemented (manifest, policies)
- [ ] Logs validation implemented (logs exist for non-docs PRs)
- [ ] Trace schema validation implemented (traces valid JSON)
- [ ] HITL/waivers checking implemented (no blocking HITL items)
- [ ] Exit code 0 on success, non-zero on failure
- [ ] Clear error messages on failure

**Tasks:**
- [ ] **T-P6.2.1**: Create /.repo/automation/scripts/governance-verify.js with base structure
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --help`
  - Evidence: Script runs and shows help

- [ ] **T-P6.2.2**: Implement structure enforcement
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --check=structure`
  - Evidence: Checks /.repo/ directories exist (policy, agents, docs, templates, automation, hitl, archive)

- [ ] **T-P6.2.3**: Implement required artifacts checking
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --check=artifacts`
  - Evidence: Checks manifest, policies, templates exist

- [ ] **T-P6.2.4**: Implement logs validation
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --check=logs`
  - Evidence: Checks logs exist for non-docs PRs (P24)

- [ ] **T-P6.2.5**: Implement trace schema validation (call validate-agent-trace.js)
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --check=traces`
  - Evidence: Validates traces against JSON schema

- [ ] **T-P6.2.6**: Implement HITL/waivers checking
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --check=hitl`
  - Evidence: Checks no blocking HITL items (Pending/In Progress)

- [ ] **T-P6.2.7**: Implement exit codes and error messages
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js || echo "Failed as expected"`
  - Evidence: Clear error messages, proper exit codes

- [ ] **T-P6.2.8**: Add --all flag to run all checks
  - Files: `/.repo/automation/scripts/governance-verify.js`
  - Commands: `node /.repo/automation/scripts/governance-verify.js --all`
  - Evidence: Runs all checks in sequence

**Out of Scope for This Work Package:**
- Boundary checker implementation (complex, separate phase)
- Security scanner implementation (complex, separate phase)
- Performance monitoring (future)

**Notes:**
- Use Node.js for consistency with typical repos
- Keep checks fast (< 30 seconds total)
- Fail fast with clear error messages
- Reference P24 (Logs Required), P5 templates

---

### WP-P6.3: Trace Validation Script

**Block**: Automation  
**Priority**: P0  
**Status**: Not Started  
**Owner**: DevOps Lead  
**Effort**: M (8-16 hours)  
**Risk**: 🟡 Medium

**Dependencies:**
- Requires: WP-P5.2, WP-P6.2
- Blocks: None

**Description:**
Create validate-agent-trace.js script that validates trace JSON files against the AGENT_TRACE_SCHEMA.json schema. This ensures all traces are machine-readable and complete.

**Acceptance Criteria:**
- [ ] /.repo/automation/scripts/validate-agent-trace.js created
- [ ] Script validates JSON against AGENT_TRACE_SCHEMA.json
- [ ] Script accepts file path or directory as input
- [ ] Script outputs clear validation errors
- [ ] Exit code 0 on valid, non-zero on invalid
- [ ] All required fields validated (intent, files, commands, evidence, hitl, unknowns)

**Tasks:**
- [ ] **T-P6.3.1**: Create /.repo/automation/scripts/validate-agent-trace.js
  - Files: `/.repo/automation/scripts/validate-agent-trace.js`
  - Commands: `node /.repo/automation/scripts/validate-agent-trace.js --help`
  - Evidence: Script runs and shows help

- [ ] **T-P6.3.2**: Implement JSON schema validation
  - Files: `/.repo/automation/scripts/validate-agent-trace.js`
  - Commands: `node /.repo/automation/scripts/validate-agent-trace.js <trace-file.json>`
  - Evidence: Validates against AGENT_TRACE_SCHEMA.json

- [ ] **T-P6.3.3**: Support file path input
  - Files: `/.repo/automation/scripts/validate-agent-trace.js`
  - Commands: `node /.repo/automation/scripts/validate-agent-trace.js ./trace.json`
  - Evidence: Validates single file

- [ ] **T-P6.3.4**: Support directory input
  - Files: `/.repo/automation/scripts/validate-agent-trace.js`
  - Commands: `node /.repo/automation/scripts/validate-agent-trace.js ./traces/`
  - Evidence: Validates all JSON files in directory

- [ ] **T-P6.3.5**: Implement clear error messages
  - Files: `/.repo/automation/scripts/validate-agent-trace.js`
  - Commands: `node /.repo/automation/scripts/validate-agent-trace.js <invalid-trace.json>`
  - Evidence: Shows which fields are missing/invalid

- [ ] **T-P6.3.6**: Validate all required fields
  - Files: `/.repo/automation/scripts/validate-agent-trace.js`
  - Commands: `node /.repo/automation/scripts/validate-agent-trace.js <valid-trace.json>`
  - Evidence: Checks intent, files, commands, evidence, hitl, unknowns

**Out of Scope for This Work Package:**
- Trace content analysis (future)
- Trace aggregation/reporting (future)

**Notes:**
- Use ajv or similar for JSON schema validation
- Keep validation fast
- Support both file and directory inputs for flexibility

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scripts fail on edge cases | High | High | Comprehensive testing, graceful error handling |
| CI workflow too slow, blocks PRs | Medium | High | Optimize checks, run in parallel where possible |
| Schema validation too strict | Medium | Medium | Include flexibility in schema, iterate based on usage |
| Scripts require dependencies not in repo | Low | Medium | Minimize dependencies, document requirements |
| Governance checks create false positives | Medium | High | Test thoroughly, allow waivers for edge cases |
| Scripts not portable across environments | Low | Medium | Use standard Node.js, document requirements |

## Definition of Done

- [ ] All WP-P6.1 through WP-P6.3 work packages marked complete
- [ ] CI configuration created and committed
- [ ] governance-verify.js created and functional
- [ ] validate-agent-trace.js created and functional
- [ ] All scripts tested with sample data
- [ ] Scripts pass on current repo state
- [ ] Documentation updated with script usage
- [ ] Peer review completed
- [ ] No blockers for Phase 7 (P7)

## Notes & References

- **Related ADRs**: None yet
- **Related PRs**: Will be created as implementation proceeds
- **External Dependencies**: Node.js, ajv (for JSON schema validation)
- **Key Decisions**:
  - Using Node.js for consistency with typical repos
  - Fail fast with clear error messages
  - Keep checks fast (< 30 seconds)
  - Support both CLI and CI usage
  - Boundary/security checkers deferred (complex, separate phase)

## Next Phase

After completing P6, proceed to:
- **Phase 7 (P7)**: Docs Glue - documentation indexes, standards, ADR scaffold
