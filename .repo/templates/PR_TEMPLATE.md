# /.repo/templates/PR_TEMPLATE.md

**Required:** All PRs must declare a change type. See `.repo/agents/QUICK_REFERENCE.md` for change type determination.

```json
{
  "title": "",
  "change_type": "feature | api_change | security | cross_module | non_doc_change",
  "task_packet": "",
  "changes": [],
  "evidence": [],
  "verification_commands_run": [],
  "hitl": [],
  "waivers": [],
  "notes": "Strict structure. No secrets."
}
```

**Change Type Decision Tree:**
- **security**: Security/auth/money/external systems changes
- **api_change**: API contract/endpoint changes (requires ADR + OpenAPI update)
- **cross_module**: Crosses module/feature boundaries (requires ADR)
- **feature**: New functionality/features
- **non_doc_change**: Bug fixes, refactoring, config changes (not doc-only)

**See:** `.repo/agents/QUICK_REFERENCE.md` section "🎯 Change Type Determination" for full decision tree.
