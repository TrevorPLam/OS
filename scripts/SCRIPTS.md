# SCRIPTS.md (Folder-Level Guide)

## Purpose of this folder

This folder (`scripts/`) contains automation and utility scripts for development, deployment, and maintenance tasks.

## What agents may do here

- Add new utility scripts
- Modify existing scripts to improve functionality
- Create automation for common tasks
- Add helper scripts for development workflow

## What agents may NOT do

- Break existing script interfaces without migration plan
- Add production code (scripts only)
- Create scripts that modify production without safeguards
- Remove scripts that are in active use
- Create scripts that bypass governance checks

## Required links

- Refer to higher-level policy: `.repo/policy/PRINCIPLES.md` (Principle 11: Prefer Guardrails Over Heroics)
- See `.repo/policy/SECURITY_BASELINE.md` for security requirements
- See `scripts/governance-verify.sh` for governance enforcement script

## Script Standards

- Scripts should be executable and well-documented
- Scripts should follow bash best practices
- Scripts should include error handling
- Scripts should not contain secrets or sensitive data
- Scripts should be idempotent where possible
