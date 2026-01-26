# 🎯 Current Task

> **Single Active Task** — Only ONE task should be in this file at any time.

---

### [TASK-021] Increase Frontend Test Coverage to 60%
- **Priority:** P2
- **Status:** In Progress
- **Created:** 2026-01-23
- **Context:** Per ANALYSIS.md Section 1.4, 11.9, test coverage is <15% but vite.config.ts sets 60% thresholds. Only 8 test files exist for ~96 source files.

#### Acceptance Criteria
- [ ] Add tests for all API functions in `frontend/src/api/` (currently 0% coverage)
- [ ] Add tests for all page components (currently <15% coverage)
- [ ] Add tests for React Query hooks
- [ ] Add integration tests for data fetching flows
- [ ] Achieve 60%+ coverage (lines, functions, branches, statements)
- [ ] Add coverage reporting to CI
- [ ] Update coverage thresholds in vite.config.ts if needed

#### Notes
- Per ANALYSIS.md Section 1.4: 8 test files for 96 source files
- Per Section 11.9: API layer 0% coverage, pages <15%
- Critical paths not tested: Client CRUD, Deal pipeline, Proposal workflow
- Estimated: 20-30 hours
- Files: New test files in `frontend/src/**/__tests__/`
---
## P2 — Medium
