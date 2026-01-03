# File Organization Status

**Date:** December 2025  
**Status:** Phase 2 In Progress

## Overview

This document tracks the file organization progress as part of the documentation consolidation effort.

## Completed Moves

### Policy Documents → `docs/03-reference/policies/`

✅ **Moved:**
- `API_VERSIONING_POLICY.md` → `docs/03-reference/policies/api-versioning.md`
- `API_DEPRECATION_POLICY.md` → `docs/03-reference/policies/api-deprecation.md`
- `DEFINITION_OF_DONE.md` → `docs/03-reference/policies/definition-of-done.md`

**Status:** Files created in new location. Old files still exist (to be removed after reference updates).

## Pending Moves

### Implementation Documents → `docs/04-explanation/implementations/`

**To Move:**
- `GDPR_DATA_EXPORT_IMPLEMENTATION.md` → `gdpr-data-export.md`
- `DATA_RETENTION_IMPLEMENTATION.md` → `data-retention.md`
- All other `*_IMPLEMENTATION.md` files (~23 more)

### Security Documents → `docs/04-explanation/security/`

**To Move:**
- `THREAT_MODEL.md` → `threat-model.md`
- `BOUNDARY_RULES.md` → `boundary-rules.md`
- `SECURITY_COMPLIANCE.md` → `security-compliance.md`

### Reference Documents → `docs/03-reference/`

**To Move:**
- `HIDDEN_ASSUMPTIONS.md` → `assumptions.md`
- `REPO_MAP.md` → `repo-map.md`
- `GLOSSARY.md` → `glossary.md`
- `STYLE_GUIDE.md` → `style-guide.md`

### Operations Documents → `docs/02-how-to/`

**To Move:**
- `OPERATIONS.md` → `operations.md` (or keep as-is if comprehensive)
- `TROUBLESHOOTING.md` → `troubleshooting.md`

## Reference Updates Needed

After files are moved, the following references need to be updated:

1. **README.md** - Update all links to moved files
2. **Cross-references in moved files** - Update "See Also" sections
3. **IMPLEMENTATION_SUMMARY.md** - Update file paths
4. **DOCUMENTATION_ANALYSIS.md** - Update example paths
5. **Any code comments** - Update references to documentation

## Strategy

Given the large number of files, we have two options:

### Option 1: Complete Move (Recommended)
- Move all files to new locations
- Update all references in one pass
- Remove old files
- Test all links

### Option 2: Incremental Move
- Move files in batches by category
- Update references after each batch
- Test after each batch

**Current Approach:** Option 1 - Complete move for consistency

## Next Steps

1. ✅ Create new directory structure
2. ✅ Move policy documents
3. ⏳ Move implementation documents
4. ⏳ Move security documents
5. ⏳ Move reference documents
6. ⏳ Update all references
7. ⏳ Remove old files
8. ⏳ Test all links

## Notes

- Old files will be kept until all references are updated
- All file moves maintain content integrity
- Path updates in cross-references are critical
- README.md is the primary navigation point and must be updated last
