# Document Cleanup Plan

**Date:** 2026-01-23
**Status:** Ready to Execute

---

## 🗑️ Files to DELETE (14 files)

### Analysis/Assessment Documents (12 files)

These were one-time analysis documents from the design/implementation phase. All issues identified have been resolved.

1. `.repo/QUALITY_ASSURANCE_REVIEW.md` - QA review (issues fixed)
2. `.repo/FIXES_NEEDED.md` - Action items (all implemented)
3. `.repo/EXECUTIVE_SUMMARY_ASSESSMENT.md` - One-time assessment
4. `.repo/CURRENT_STATUS_ASSESSMENT.md` - Status snapshot (outdated)
5. `.repo/ANALYSIS_AGENTIC_FRAMEWORK.md` - Original analysis (gaps filled)
6. `.repo/COMPREHENSIVE_AGENTIC_FRAMEWORK_ASSESSMENT.md` - Comprehensive assessment
7. `.repo/ENHANCEMENTS_COMPLETE.md` - Enhancement summary (historical)
8. `.repo/FINAL_IMPLEMENTATION_SUMMARY.md` - Implementation summary
9. `.repo/IMPLEMENTATION_SUMMARY.md` - Another implementation summary
10. `.repo/ENTRY_POINT_ANALYSIS.md` - Entry point design analysis (implemented)
11. `.repo/COMMAND_SYSTEM.md` - Command system design doc (implemented)
12. `.repo/JSON_FORMAT_ANALYSIS.md` - JSON format analysis (implemented)

### Redundant Documentation (2 files)

13. `.repo/AGENT_PROMPT_TEMPLATE.md` - Prompt templates (superseded by `AGENTS.json`/`AGENTS.md` entry point)
14. `.repo/DOCUMENT_CLEANUP_ANALYSIS.md` - This analysis file (delete after cleanup)

---

## ⚠️ Files to REVIEW (2 files)

### Potentially Keep (Review First)

1. **`.repo/agents/AGENTS.md`**
   - **Status:** Contains framework rules, trace log info, agent log info
   - **Decision:** KEEP - Has unique content not in root `AGENTS.md`
   - **Action:** Update references to clarify it's framework docs, not entry point

2. **`.repo/INTEGRATION_SUMMARY.md`**
   - **Status:** Integration details for CI/CD
   - **Decision:** REVIEW - Keep if contains operational info, delete if just historical
   - **Action:** Review content, decide

---

## ✅ Files to KEEP (Essential)

### Core Governance
- `GOVERNANCE.md`
- `repo.manifest.yaml`
- `AGENT.md`
- `INDEX.md`
- `DOCUMENT_MAP.md`

### Policy Files
- All files in `policy/`

### Agent Framework
- `agents/rules.json`
- `agents/QUICK_REFERENCE.md`
- `agents/AGENTS.md` (framework docs - KEEP)
- `agents/capabilities.md`
- `agents/roles/`
- `agents/checklists/`
- `agents/FORMATS.md`
- `agents/rules-compact.md`

### Templates
- All files in `templates/`

### Documentation
- `docs/`
- `CHANGELOG.md` (historical record)
- `TOKEN_OPTIMIZATION_STRATEGY.md` (strategy reference)

---

## 📋 Execution Steps

1. **Delete analysis/assessment documents** (12 files)
2. **Delete redundant documentation** (2 files)
3. **Review and decide on** `.repo/INTEGRATION_SUMMARY.md`
4. **Update references** in `INDEX.md` and `DOCUMENT_MAP.md` if needed
5. **Verify** no broken references after cleanup

---

## 🔍 Reference Check

After deletion, verify these files don't reference deleted docs:
- `INDEX.md`
- `DOCUMENT_MAP.md`
- `GOVERNANCE.md`
- Any policy files

---

**Total files to delete: 14**
**Total files to review: 2**
**Total files to keep: ~30+**
