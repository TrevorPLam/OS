# Documentation Archive

This directory contains outdated or superseded documentation that is retained for historical reference.

**Archival Policy** (per Constitution Section 2.1 - Supremacy):
- Documents are archived when they conflict with current docs or are superseded by newer versions
- Each archived document includes a header explaining why it was archived and what replaced it
- Archives are organized by date and category

## Archive Contents

### Analysis Documents (2025-12-30)

**Location:** `analysis-2025-12-30/`

**Reason for Archive:** These were point-in-time assessments created during codebase audits. The findings have been addressed or incorporated into TODO.md and the coding constitution compliance tracking.

**Archived Files:**
- `CONSTITUTION_ANALYSIS.md` - Constitution compliance analysis (superseded by constitution compliance completion on 2025-12-30)
- `TODO_ANALYSIS.md` - Analysis of in-code TODOs (findings incorporated into TODO.md)
- `FORENSIC_ANALYSIS.md` - Codebase forensic analysis (findings incorporated into assessment documents)
- `ANALYSIS_SUMMARY.md` - Summary of analyses (superseded by constitution compliance completion)
- `ChatGPT_CODEBASE_ASSESMENT` - External audit report (449KB, findings tracked in TODO.md)

**What Replaced Them:**
- Active constitution compliance: See TODO.md "PRIORITY #1: Coding Constitution Compliance" section
- Active assessment remediation: See TODO.md "PRIORITY #2: ChatGPT Codebase Assessment Remediation" section

---

### Legacy Roadmap Documents (2025-12-30)

**Location:** `roadmap-legacy-2025-12-30/`

**Reason for Archive:** Multiple overlapping roadmap/status documents caused confusion about source of truth. Per TODO.md line 295: "The sections below are preserved for historical context only."

**Archived Files:**
- `STRATEGIC_IMPLEMENTATION_PLAN.md` - 10-week execution plan (incorporated into TODO.md)
- `IMPLEMENTATION_ASSESSMENT.md` - Assessment of missing features (incorporated into TODO.md)
- `MISSINGFEATURES.md` - Missing features checklist (incorporated into TODO.md)
- `QUICK_WINS_IMPLEMENTATION.md` - Quick wins tracker (incorporated into TODO.md)
- `IMPLEMENTATION_SUMMARY.md` - Implementation summary (incorporated into TODO.md)

**What Replaced Them:**
- Single source of truth: `TODO.md` - "Current Work & Roadmap"
- Canonical requirements: `docs/03-reference/requirements/` (DOC-1 through DOC-35)

---

## How to Use Archived Docs

1. **Don't use archived docs for current work** - They're out of date
2. **Reference archives for historical context** - Understanding past decisions
3. **Check replacement docs first** - The current source of truth is always more accurate

## Archival Process

When archiving a document:

1. Create a dated subdirectory in `ARCHIVE/` (format: `category-YYYY-MM-DD/`)
2. Move the file(s) to the subdirectory
3. Update this README with:
   - Archive location
   - Reason for archive
   - What replaced the archived doc
   - Date archived
4. Add a header to the archived file itself:
   ```markdown
   > **ARCHIVED:** [Date]
   > **REASON:** [Brief explanation]
   > **REPLACED BY:** [Link to current doc]
   ```

## Constitution Compliance

This archive structure fulfills Constitution Section 3.2 requirements:
- Documentation is traceable (archived with reason)
- Source of truth is clear (replaced-by links)
- No information is lost (archives retained)

---

**Last Updated:** 2026-01-02

## Recent Archive Additions (2026-01-02)

### Checklist Documents (2026-01-02)

**Location:** `checklists/`

**Reason for Archive:** Historical development checklists that are no longer actively used. Tasks have been migrated to TODO.md or TODO_COMPLETED.md.

**Archived Files:**
- `CHECKLIST.md` through `CHECKLIST6.md` - Six iterations of development checklists

**What Replaced Them:**
- `TODO.md` - Current development roadmap with prioritized tasks
- `TODO_COMPLETED.md` - Archive of completed tasks

### Analysis Documents (2026-01-02)

**Location:** `analysis/`

**Reason for Archive:** Historical analysis documents from various development phases. Findings have been incorporated into the current TODO.md.

**Archived Files:**
- `CHECKLIST2_ANALYSIS_SUMMARY.md` through `CHECKLIST6_ANALYSIS_SUMMARY.md`
- `CHECKLIST_ANALYSIS.md`, `checklist_analysis_summary.md`

**What Replaced Them:**
- Current task prioritization in `TODO.md`
- Active documentation in `docs/` directory

### Implementation Summaries (2026-01-02)

**Location:** `summaries/`

**Reason for Archive:** Point-in-time implementation summaries that have been superseded by TODO_COMPLETED.md.

**Archived Files:**
- `WORK_COMPLETED_SUMMARY.md` - General work completion summary
- `WORK_SUMMARY_DEAL_3-6.md` - Deal feature implementation summary (kept for detailed reference)
- `IMPLEMENTATION_SUMMARY_2.7-2.10.md` - Tasks 2.7-2.10 implementation
- `ASSESS-S6.2-FINDINGS.md` - Security assessment findings

**What Replaced Them:**
- `TODO_COMPLETED.md` - Comprehensive archive of all completed work
- Individual feature documentation in `docs/` directory

### PDF Reference Documents (2026-01-02)

**Location:** `pdfs/`

**Reason for Archive:** Legacy PDF documents moved out of root directory for better organization.

**Archived Files:**
- `AC.pdf`, `AC2.pdf`, `C.pdf`, `C2.pdf`, `K.pdf`, `K2.pdf`, `HS.pdf`, `HS2.pdf`, `SF.pdf`, `SF2.pdf`

**What Replaced Them:**
- Active documentation in markdown format in `docs/` directory
- PDFs retained for reference if needed

---

**Last Updated:** 2026-01-02
