# audits/templates/AUDIT_REPORT_TEMPLATE.md
> Standardized audit report format.
> Required for all audit executions before marking any task COMPLETE.

---

## Audit Metadata
- **Task ID(s):**
- **Task Type:** (bug fix / feature / dependency change / release / docs / agent health)
- **Audit Set Run:** (list audit file paths)
- **Date:**
- **Agent / Executor:**

---

## Scope & Context
- **Files Inspected:**  
  (explicit list of paths; do not say “entire repo” unless actually inspected)
- **Out-of-Scope Items (if any):**  
  (and why)

---

## Audit Results Summary
| Audit | Pass/Fail | Avg Score | Critical 0s | Notes |
|------|-----------|-----------|-------------|-------|
| CORRECTNESSAUDIT |  |  |  |  |
| CHANGEAUDIT |  |  |  |  |
| DESIGNAUDIT |  |  |  |  |
| TESTQUALITYAUDIT |  |  |  |  |
| DOCSAUDIT |  |  |  |  |
| DEPENDENCYAUDIT |  |  |  |  |
| SECURITYAUDIT |  |  |  |  |
| RELEASEAUDIT |  |  |  |  |
| AGENTAUDIT |  |  |  |  |

> Remove rows for audits not run.

---

## Detailed Findings
### Findings by Audit
Use the structure below for **each audit executed**.

#### <AUDIT_NAME>
- **Checklist Item:**  
  - Score: 0 / 1 / 2  
  - Evidence: (file path, line numbers, commands, or explanation)
- **Checklist Item:**  
  - Score: 0 / 1 / 2  
  - Evidence:

> If any item is UNKNOWN, score **0**, explain why, and create a TODO task.

---

## Verification
- **Commands Run:**  
  (from repo.manifest.yaml or task-specific instructions)
- **Results:**  
  - Pass / Fail / Blocked
  - Relevant output summary
- **If Blocked:**  
  - Reason:
  - TODO task created: (ID)

---

## Files Changed
- `path/to/file1`
- `path/to/file2`

> Changes must be minimal and directly tied to the task.

---

## Documentation Updates
- Docs updated:
  - `READMEAI.md` (if applicable)
  - Other docs:
- Docs intentionally not updated:
  - (and why)

---

## TODO.md Updates
- Tasks marked COMPLETE:
- Tasks created:
  - ID:
  - Reason:

---

## Final Gate Decision
- **Meets Perfect Codebase Standard:** YES / NO
- **If NO:**  
  - Blocking issues:
  - Required follow-up actions:

---

## Notes (Optional)
- Risks
- Trade-offs accepted
- Deferred improvements (must be captured as TODOs if relevant)

---
> End of report