# Priority Task List

This document contains prioritized tasks derived from the phase documents (phase1.md - phase9.md).

## Phase 1: Master Handoff Skeleton + Locked Decisions

### Core Infrastructure
- [ ] Create /.repo directory structure
- [ ] Establish authority chain: Manifest > Agents > Policy > Standards > Product
- [ ] Implement non-coder plain English requirement across all documentation
- [ ] Set up filepath requirement everywhere (PRs, Task Packets, logs, ADRs, waivers, commentary)
- [ ] Establish deliver small increments workflow

### Principles Implementation
- [ ] Implement P3: One Change Type Per PR
- [ ] Implement P4: Make It Shippable
- [ ] Implement P5: Don't Break Surprises
- [ ] Implement P6: Evidence Over Vibes
- [ ] Implement P7: UNKNOWN Is a First-Class State
- [ ] Implement P8: Read Repo First
- [ ] Implement P9: Assumptions Must Be Declared
- [ ] Implement P10: Risk Triggers a Stop
- [ ] Implement P11: Prefer Guardrails Over Heroics
- [ ] Implement P12: Rollback Thinking
- [ ] Implement P13: Respect Boundaries by Default
- [ ] Implement P14: Localize Complexity (Option B)
- [ ] Implement P15: Consistency Beats Novelty
- [ ] Implement P16: Decisions Written Down (Token-Optimized)
- [ ] Implement P17: PR Narration
- [ ] Implement P18: No Silent Scope Creep
- [ ] Implement P19: Docs Age With Code
- [ ] Implement P20: Examples Are Contracts
- [ ] Implement P21: Naming Matters
- [ ] Implement P22: Waivers Rare + Temporary
- [ ] Implement P23: ADR Required When Triggered
- [ ] Implement P24: Logs Required for Non-Docs
- [ ] Implement P25: Token-Optimized TODO Discipline

### Quality Gates Setup
- [ ] Configure merge policy: soft_block_with_auto_generated_waivers
- [ ] Set up coverage strategy: gradual_ratchet
- [ ] Configure performance budgets: strict_with_fallback_to_default
- [ ] Enforce zero warnings policy
- [ ] Configure governance_verify_checks to run all checks

### Waivers System
- [ ] Set up auto-generate waivers for all failures
- [ ] Implement full_history lifecycle tracking
- [ ] Create /waivers/historical/ directory structure

### Security Baseline
- [ ] Configure dependency vulnerability checks (always_hitl)
- [ ] Implement secrets handling: absolute_prohibition
- [ ] Set up security review triggers [1,2,4,5,6,8,9,10]
- [ ] Define and enforce forbidden patterns [A-H]
- [ ] Configure security_check_frequency: every_pr
- [ ] Implement mandatory HITL actions [1-8]

### Boundaries Configuration
- [ ] Set up hybrid_domain_feature_layer model
- [ ] Implement allowed import direction: ui → domain → data → shared_platform
- [ ] Enforce cross-feature rule: ADR required
- [ ] Create src/platform/ shared platform directory
- [ ] Implement structure pattern: src/<domain>/<feature>/<layer>/
- [ ] Configure hybrid_static_checker_plus_manifest enforcement
- [ ] Set up violation severity: waiver_plus_auto_task

### Enhancements
- [ ] Implement location anchors (file headers, filepaths in PRs/tasks/ADRs/waivers)
- [ ] Add code anchors (region comments, critical code excerpts, named function anchors)
- [ ] Create navigation aids (domain/feature index files, directory READMEs, full path imports)
- [ ] Add safety heuristics (impact summary, explicit unknowns, rollback plan)
- [ ] Set up iteration accelerators (pattern reference, verification commands, file touch reason, TODO archive references)

### HITL System
- [ ] Create /.repo/policy/HITL.md index
- [ ] Create /.repo/hitl/ items directory
- [ ] Implement auto_sync_pr_and_hitl model
- [ ] Set up external system detection (keywords + manifest + change type)

## Phase 2: Policy Corpus (Authoritative Rules)

### Constitution
- [ ] Create /.repo/policy/CONSTITUTION.md
- [ ] Document Article 1: Final Authority (solo founder)
- [ ] Document Article 2: Verifiable over Persuasive
- [ ] Document Article 3: No Guessing (UNKNOWN handling)
- [ ] Document Article 4: Incremental Delivery
- [ ] Document Article 5: Strict Traceability
- [ ] Document Article 6: Safety Before Speed
- [ ] Document Article 7: Per-Repo Variation Allowed
- [ ] Document Article 8: HITL for External Systems

### Principles Documentation
- [ ] Create /.repo/policy/PRINCIPLES.md
- [ ] Document global rule: filepaths required everywhere
- [ ] Document all 25 principles (P3-P25) with plain English descriptions

### Quality Gates Documentation
- [ ] Create /.repo/policy/QUALITY_GATES.md
- [ ] Document merge policy
- [ ] Document hard gates (non-waiverable)
- [ ] Document waiverable gates
- [ ] Document coverage strategy
- [ ] Document performance budgets
- [ ] Document warnings policy
- [ ] Document PR size policy
- [ ] Document required checks

### Security Baseline Documentation
- [ ] Create /.repo/policy/SECURITY_BASELINE.md
- [ ] Document absolute prohibitions (secrets/tokens/keys)
- [ ] Document dependency vulnerability handling
- [ ] Document security check frequency
- [ ] Document security review triggers with meanings
- [ ] Document forbidden patterns
- [ ] Document mandatory HITL actions with meanings
- [ ] Document evidence requirements

### Boundaries Documentation
- [ ] Create /.repo/policy/BOUNDARIES.md
- [ ] Document hybrid_domain_feature_layer model
- [ ] Document directory pattern: src/<domain>/<feature>/<layer>/
- [ ] Document allowed import direction with examples
- [ ] Document cross-feature rule
- [ ] Document enforcement method
- [ ] Document exception process (small vs large)
- [ ] Document violation severity
- [ ] Document boundary visibility requirements
- [ ] Provide practical examples (allowed/forbidden patterns)

### HITL Documentation
- [ ] Create /.repo/policy/HITL.md
- [ ] Document storage model (split, same folder)
- [ ] Document minimal human effort rule
- [ ] Document categories (External Integration, Clarification, Risk, Feedback, Vendor)
- [ ] Document statuses (Pending, In Progress, Blocked, Completed, Superseded)
- [ ] Document merge blocking rule
- [ ] Document role permissions (agents vs human)
- [ ] Document external systems detection methods
- [ ] Document HITL item file format (required fields)
- [ ] Create index tables (Active/Archived)
- [ ] Document archiving process

## Phase 3: Manifest (Fillable) + Command Resolution Standard

### Manifest Creation
- [ ] Create /.repo/repo.manifest.yaml
- [ ] Configure repo metadata (ships, ship_kind, release_protects)
- [ ] Configure prerequisites (package_manager, runtime_pinned, platform_tools)
- [ ] Define canonical commands (install, check:quick, check:ci, check:release, check:governance, check:boundaries, check:security)
- [ ] Configure verify_profiles (quick, ci, release, governance)
- [ ] Configure tests (required_level: unit+integration)
- [ ] Configure budgets (mode, enforcement, fallback_to_default)
- [ ] Configure security settings (every_pr, release_includes_security, dependency_vulns_always_hitl)
- [ ] Configure boundaries (enforcement, edges_model, edges array)

### Command Resolution
- [ ] Replace <FILL_FROM_REPO> placeholders with actual commands from package.json/Makefile/CI
- [ ] Verify install command
- [ ] Verify check:quick command (must include fast build)
- [ ] Verify check:ci command (quick + tests + full build)
- [ ] Verify check:release command (ci + security + budgets)
- [ ] Verify check:governance command (governance-verify)
- [ ] Verify check:boundaries command (boundary checker)
- [ ] Verify check:security command (dep scan + secrets scan + forbidden patterns)

### Standards Documentation
- [ ] Create /.repo/docs/standards/manifest.md
- [ ] Document non-negotiable rule (no guessing)
- [ ] Document command resolution process (5-step process)
- [ ] Document what each command must accomplish
- [ ] Document placeholder meanings (<FILL_FROM_REPO>, <UNKNOWN>)
- [ ] Document merge blocking conditions
- [ ] Document minimal acceptance check

## Phase 4: Agents Framework + Folder-Level Guides

### Agents Framework
- [ ] Create /.repo/agents/AGENTS.md
- [ ] Document core rules (no guessing, filepaths required, three-pass code generation)
- [ ] Document log requirements (/.repo/templates/AGENT_LOG_TEMPLATE.md)
- [ ] Document trace log requirements (/.repo/templates/AGENT_TRACE_SCHEMA.json)
- [ ] Document cross-feature import rule (ADR required)
- [ ] Document boundary model enforcement

### Capabilities
- [ ] Create /.repo/agents/capabilities.md
- [ ] List all capabilities (create_feature, modify_existing, add_dependency, change_api_contract, change_schema, update_security, update_release_process, apply_waiver, create_adr, create_task_packet, run_verification_profiles)

### Agent Roles
- [ ] Create /.repo/agents/roles/primary.md (full capabilities except apply_waiver and update_release_process)
- [ ] Create /.repo/agents/roles/secondary.md (modify_existing, refactor/port within boundaries)
- [ ] Create /.repo/agents/roles/reviewer.md (human, controls waivers + enforcement)
- [ ] Create /.repo/agents/roles/release.md (human, controls update_release_process and deploy)

### Folder-Level Guides
- [ ] Create /.repo/AGENT.md (purpose, allowed operations, forbidden patterns, required links)
- [ ] Create /src/AGENT.md
- [ ] Create /src/platform/AGENT.md
- [ ] Create /tests/AGENT.md
- [ ] Create /docs/AGENT.md
- [ ] Create /scripts/AGENT.md

## Phase 5: PR Operating System

### Task Packet Prompt
- [ ] Create /.repo/agents/prompts/task_packet.md
- [ ] Define template structure (goal, non_goals, acceptance_criteria, approach, files_touched, verification_plan, risks, rollback_plan, hitl_requirements, notes)

### PR Template Prompt
- [ ] Create /.repo/agents/prompts/pr_template.md
- [ ] Define template structure (change_type, summary, task_packet, filepath_changes, verification_commands_run, evidence, risks, rollback, hitl, notes)

### Checklists
- [ ] Create /.repo/agents/checklists/change-plan.md
- [ ] Create /.repo/agents/checklists/pr-review.md
- [ ] Create /.repo/agents/checklists/incident.md

### PR Template
- [ ] Create /.repo/templates/PR_TEMPLATE.md
- [ ] Define template structure (title, change_type, task_packet, changes, evidence, verification_commands_run, hitl, waivers, notes)

## Phase 6: Logging + Trace + Waiver + ADR Templates

### Agent Log Template
- [ ] Create /.repo/templates/AGENT_LOG_TEMPLATE.md
- [ ] Define template structure (intent, plan, actions, evidence, decisions, risks, follow_ups, reasoning_summary, notes)

### Agent Trace Schema
- [ ] Create /.repo/templates/AGENT_TRACE_SCHEMA.json
- [ ] Define JSON schema with required fields (intent, files, commands, evidence, hitl, unknowns)

### Waiver Template
- [ ] Create /.repo/templates/WAIVER_TEMPLATE.md
- [ ] Define template structure (waives, why, scope, owner, expiration, remediation_plan, link, notes)

### ADR Template
- [ ] Create /.repo/templates/ADR_TEMPLATE.md
- [ ] Define template structure (context, decision_drivers, options, decision, consequences, modules, commands, migration, boundary_impact, hitl)

### Runbook Template
- [ ] Create /.repo/templates/RUNBOOK_TEMPLATE.md
- [ ] Define template structure (title, summary, steps, rollback, verification, notes)

### RFC Template
- [ ] Create /.repo/templates/RFC_TEMPLATE.md
- [ ] Define template structure (title, problem, proposed_solution, alternatives, impact, risks, notes)

## Phase 7: Automation Stubs

### CI Configuration
- [ ] Create /.repo/automation/ci/governance-verify.yml
- [ ] Replace <FILL_FROM_REPO_INSTALL> with actual install command
- [ ] Replace <FILL_FROM_REPO_GOVERNANCE> with actual governance command

### Automation Scripts
- [ ] Create /.repo/automation/scripts/governance-verify.js
- [ ] Implement structure enforcement
- [ ] Implement required artifacts checking
- [ ] Implement logs validation
- [ ] Implement trace schema validation
- [ ] Implement HITL/waivers checking

### Trace Validation
- [ ] Create /.repo/automation/scripts/validate-agent-trace.js
- [ ] Implement JSON schema validation against AGENT_TRACE_SCHEMA.json

## Phase 8: Docs Glue (Indexes + Standards + ADR Scaffold)

### Documentation Index
- [ ] Create /.repo/docs/DOCS_INDEX.md
- [ ] Link to all governance documents (GOVERNANCE.md, CONSTITUTION.md, PRINCIPLES.md, QUALITY_GATES.md, SECURITY_BASELINE.md, BOUNDARIES.md, HITL.md)
- [ ] Link to all standards (documentation.md, adr.md, api.md, style.md, manifest.md)
- [ ] Link to ADR history (/.repo/docs/adr/README.md)

### Standards Documentation
- [ ] Create /.repo/docs/standards/documentation.md (docs update with code, filepaths required, examples are contracts)
- [ ] Create /.repo/docs/standards/adr.md (ADR triggers, template reference)
- [ ] Create /.repo/docs/standards/api.md (API documentation requirements, api-contract change type)
- [ ] Create /.repo/docs/standards/style.md (naming, no duplication, functions do one thing, comments explain WHY)

### ADR Scaffold
- [ ] Create /.repo/docs/adr/README.md (contains all ADRs, use sequential numbering)
- [ ] Create /.repo/docs/adr/0001-example.md (example ADR using template)

## Phase 9: Root Scaffolds

### Root Documentation
- [ ] Update /README.md to link to /.repo/DOCS_INDEX.md
- [ ] Create/Update /SECURITY.md to reference /.repo/policy/SECURITY_BASELINE.md
- [ ] Create/Update /CODEOWNERS (* @owner)
- [ ] Verify /LICENSE exists

### TODO System
- [ ] Create or verify /P0TODO.md (highest priority)
- [ ] Create or verify /P1TODO.md (high priority)
- [ ] Create or verify /P2TODO.md (medium priority)
- [ ] Create or verify /COMPLETEDTODO.md (archive)
- [ ] Create /.repo/archive/todo/README.md (archived TODO snapshots)

## Meta Tasks

### Integration & Verification
- [ ] Verify all file paths are correct and consistent
- [ ] Verify all references between documents are valid
- [ ] Test command resolution process
- [ ] Verify all templates are valid JSON/YAML
- [ ] Run governance-verify (once implemented)
- [ ] Test boundary checker (once implemented)
- [ ] Test security checks (once implemented)

### Documentation Review
- [ ] Review all policy documents for clarity
- [ ] Review all templates for completeness
- [ ] Review all standards for consistency
- [ ] Ensure all plain English requirements are met

### Adoption & Rollout
- [ ] Create adoption plan for existing codebase
- [ ] Document migration path
- [ ] Create training materials for agents
- [ ] Set up monitoring and reporting
- [ ] Establish feedback loop for improvements

---

## Notes

- All tasks should follow the principles defined in Phase 1
- UNKNOWN is allowed and must route to HITL when encountered
- Filepaths must be included everywhere
- Evidence over vibes - document decisions and show proof
- Safety before speed - pause for risky changes
- All changes must be incremental and shippable
