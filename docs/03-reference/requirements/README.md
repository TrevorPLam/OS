# Requirements Specifications (DOC-1 through DOC-35)

**Canonical requirements that define platform capabilities and contracts.**

These specifications were originally numbered 1-35 in `docs/` root and represent the authoritative requirements for the ConsultantPro platform.

## Requirements Index

| DOC | Title | Status | Evidence |
|-----|-------|--------|----------|
| DOC-01 | UNKNOWN | ⚠️ | docs/1 (needs migration) |
| DOC-02 | UNKNOWN | ⚠️ | docs/2 (needs migration) |
| DOC-03 | UNKNOWN | ⚠️ | docs/3 (needs migration) |
| DOC-04 | UNKNOWN | ⚠️ | docs/4 (needs migration) |
| DOC-05 | UNKNOWN | ⚠️ | docs/5 (needs migration) |
| DOC-06 | UNKNOWN | ⚠️ | docs/6 (needs migration) |
| DOC-07 | UNKNOWN | ⚠️ | docs/7 (needs migration) |
| DOC-08 | UNKNOWN | ⚠️ | docs/8 (needs migration) |
| DOC-09 | UNKNOWN | ⚠️ | docs/9 (needs migration) |
| DOC-10 | UNKNOWN | ⚠️ | docs/10 (needs migration) |
| DOC-11 | UNKNOWN | ⚠️ | docs/11 (needs migration) |
| DOC-12 | UNKNOWN | ⚠️ | docs/12 (needs migration) |
| DOC-13 | UNKNOWN | ⚠️ | docs/13 (needs migration) |
| DOC-14 | UNKNOWN | ⚠️ | docs/14 (needs migration) |
| DOC-15 | UNKNOWN | ⚠️ | docs/15 (needs migration) |
| DOC-16 | UNKNOWN | ⚠️ | docs/16 (needs migration) |
| DOC-17 | UNKNOWN | ⚠️ | docs/17 (needs migration) |
| DOC-18 | UNKNOWN | ⚠️ | docs/18 (needs migration) |
| DOC-19 | UNKNOWN | ⚠️ | docs/19 (needs migration) |
| DOC-20 | UNKNOWN | ⚠️ | docs/20 (needs migration) |
| DOC-21 | UNKNOWN | ⚠️ | docs/21 (needs migration) |
| DOC-22 | UNKNOWN | ⚠️ | docs/22 (needs migration) |
| DOC-23 | UNKNOWN | ⚠️ | docs/23 (needs migration) |
| DOC-24 | UNKNOWN | ⚠️ | docs/24 (needs migration) |
| DOC-25 | UNKNOWN | ⚠️ | docs/25 (needs migration) |
| DOC-26 | UNKNOWN | ⚠️ | docs/26 (needs migration) |
| DOC-27 | UNKNOWN | ⚠️ | docs/27 (needs migration) |
| DOC-28 | UNKNOWN | ⚠️ | docs/28 (needs migration) |
| DOC-29 | UNKNOWN | ⚠️ | docs/29 (needs migration) |
| DOC-30 | UNKNOWN | ⚠️ | docs/30 (needs migration) |
| DOC-31 | UNKNOWN | ⚠️ | docs/31 (needs migration) |
| DOC-32 | UNKNOWN | ⚠️ | docs/32 (needs migration) |
| DOC-33 | UNKNOWN | ⚠️ | docs/33 (needs migration) |
| DOC-34 | UNKNOWN | ⚠️ | docs/34 (needs migration) |
| DOC-35 | UNKNOWN | ⚠️ | docs/35 (needs migration) |

## Migration Status

**Current Location:** `docs/1` through `docs/35` (files without `.md` extension)
**Target Location:** `docs/03-reference/requirements/spec-01.md` through `spec-35.md`

**Evidence:** Files found via `Glob **/*.md` and directory listing of `/home/user/OS/docs/`.

**Migration Plan:**
1. Rename each file: `docs/N` → `docs/03-reference/requirements/spec-{N:02d}.md`
2. Update all internal references in implementation docs
3. Update TODO.md references to point to new locations

## Relationship to Other Specs

These requirements are distinct from:
- **System Invariants**: `/spec/SYSTEM_INVARIANTS.md` - Core system rules
- **Domain Specs**: `/spec/billing/`, `/spec/contracts/`, etc. - Frozen implementation contracts

## Usage

Reference these specs when:
- Planning new features
- Verifying implementation alignment
- Resolving requirements questions

Per Constitution Section 3.2 (No Undocumented Behavior): These specs are the authoritative source for platform requirements.
