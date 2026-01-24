# .repo/AGENTS.md

**Directory structure and agent entry point:** See `.repo/STRUCTURE.json`

**Quick start:** Read `.repo/STRUCTURE.json` for complete agent framework structure and workflow.

## Token Optimization Tips

- Use `read_file` with `offset` and `limit` parameters for large files
- Read multiple files in parallel when possible
- Use `glob_file_search` for file finding instead of broad searches
- Use INDEX.json files to find major functions/classes/relevant sections
- Specify `target_directories` parameter in searches to limit scope
- Use grep to find relevant sections before reading entire files
