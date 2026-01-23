# AGENT.md (Folder-Level Guide)

## Purpose of this folder

This folder (`.repo/`) contains the governance framework for the repository. It includes policy files, agent framework, HITL tracking, and documentation standards.

## What agents may do here

- Read all policy files and documentation
- Reference governance rules when making decisions
- Create HITL items when uncertain (see `.repo/policy/HITL.md`)
- Update manifest commands when build/test processes change (with verification)
- Create task packets and trace logs

## What agents may NOT do

- Modify policy files without explicit approval (CONSTITUTION.md is immutable)
- Create waivers without reviewer approval
- Skip HITL process when required
- Guess commands - must use manifest or create HITL
- Modify governance structure without approval

## Required links

- Refer to higher-level policy: `.repo/policy/CONSTITUTION.md`
- See `.repo/policy/PRINCIPLES.md` for operating principles
- See `.repo/policy/BOUNDARIES.md` for architectural rules
- See `.repo/GOVERNANCE.md` for framework overview
- See `.repo/repo.manifest.yaml` for command definitions
