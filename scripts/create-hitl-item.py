#!/usr/bin/env python3
"""
Create HITL Item

Generates a new HITL item from template and adds it to the HITL index.

Usage:
    python3 .repo/automation/scripts/create-hitl-item.py \
        --category <category> \
        --summary <summary> \
        --required-for <change-types> \
        --owner <owner> \
        [--reviewer <reviewer>] \
        [--related-pr <pr-number>] \
        [--related-adr <adr-path>]

Exit codes:
    0 - Success
    1 - Error
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_next_hitl_id(hitl_index_path: Path) -> str:
    """Get the next available HITL ID."""
    if not hitl_index_path.exists():
        return "HITL-0001"
    
    content = hitl_index_path.read_text(encoding="utf-8")
    
    # Find all HITL IDs in the file
    ids = re.findall(r"HITL-(\d+)", content)
    if not ids:
        return "HITL-0001"
    
    # Get the highest number
    max_num = max(int(id) for id in ids)
    next_num = max_num + 1
    
    return f"HITL-{next_num:04d}"


def create_hitl_item(
    hitl_id: str,
    category: str,
    summary: str,
    required_for: str,
    owner: str,
    reviewer: Optional[str] = None,
    related_pr: Optional[str] = None,
    related_adr: Optional[str] = None,
    related_waiver: Optional[str] = None,
    related_task: Optional[str] = None
) -> str:
    """Create HITL item content from template."""
    
    today = datetime.now().strftime("%Y-%m-%d")
    reviewer_line = f"**Reviewer**: {reviewer}\n" if reviewer else ""
    related_artifacts = []
    
    if related_pr:
        related_artifacts.append(f"- **PR**: #{related_pr}")
    if related_adr:
        related_artifacts.append(f"- **ADR**: {related_adr}")
    if related_waiver:
        related_artifacts.append(f"- **Waiver**: {related_waiver}")
    if related_task:
        related_artifacts.append(f"- **Task**: {related_task}")
    
    related_section = "\n".join(related_artifacts) if related_artifacts else "None"
    
    content = f"""# {hitl_id}: {summary}

**ID**: {hitl_id}  
**Category**: {category}  
**Required For**: {required_for}  
**Owner**: {owner}  
{reviewer_line}**Status**: Pending  
**Date Required**: {today}  
**Date Completed**:  

## Summary

{summary}

## Required Human Action

1. Review the change and assess risk
2. Approve or request modifications
3. Mark as Completed when satisfied

## Evidence of Completion

- [ ] Review completed
- [ ] Risk assessment approved
- [ ] Evidence verified (filepaths: _add filepaths here_)

## Related Artifacts

{related_section}
"""
    return content


def add_to_index(hitl_index_path: Path, hitl_id: str, category: str, summary: str, filepath: str):
    """Add HITL item to the Active table in index."""
    if not hitl_index_path.exists():
        # Create new index file
        content = f"""# /.repo/policy/HITL.md
HITL = Human-In-The-Loop. This is the single binding place for human-required actions.

## Index tables
### Active
|ID|Category|Status|Summary|Filepath|
|---|---|---|---|---|
|{hitl_id}|{category}|Pending|{summary}|{filepath}|

### Archived
|ID|Category|Status|Summary|Filepath|
|---|---|---|---|---|
"""
        hitl_index_path.write_text(content, encoding="utf-8")
        return
    
    content = hitl_index_path.read_text(encoding="utf-8")
    
    # Find the Active table
    active_table_pattern = r"(### Active\s*\n\|[^\n]+\n\|[^\n]+\n)((?:\|[^\n]+\n?)*)"
    match = re.search(active_table_pattern, content)
    
    if match:
        table_header = match.group(1)
        table_rows = match.group(2)
        
        # Add new row
        new_row = f"|{hitl_id}|{category}|Pending|{summary}|{filepath}|\n"
        new_table = table_header + table_rows + new_row
        
        # Replace the table
        content = re.sub(active_table_pattern, new_table, content)
    else:
        # Table doesn't exist, add it
        active_section = f"""
### Active
|ID|Category|Status|Summary|Filepath|
|---|---|---|---|---|
|{hitl_id}|{category}|Pending|{summary}|{filepath}|
"""
        content += active_section
    
    hitl_index_path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Create a new HITL item")
    parser.add_argument("--category", type=str, required=True, 
                       choices=["External Integration", "Clarification", "Risk", "Feedback", "Vendor"],
                       help="HITL category")
    parser.add_argument("--summary", type=str, required=True, help="Brief summary of the HITL item")
    parser.add_argument("--required-for", type=str, required=True, 
                       help="Change types that require this HITL (e.g., 'security, release')")
    parser.add_argument("--owner", type=str, required=True, help="Human owner name")
    parser.add_argument("--reviewer", type=str, help="Human reviewer name")
    parser.add_argument("--related-pr", type=str, help="Related PR number")
    parser.add_argument("--related-adr", type=str, help="Related ADR filepath")
    parser.add_argument("--related-waiver", type=str, help="Related waiver filepath")
    parser.add_argument("--related-task", type=str, help="Related task ID")
    parser.add_argument("--hitl-index", type=str, default=".repo/policy/HITL.md", 
                       help="Path to HITL index file")
    parser.add_argument("--hitl-dir", type=str, default=".repo/hitl", 
                       help="Directory for HITL item files")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no file changes)")
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent.parent.parent
    hitl_index_path = repo_root / args.hitl_index
    hitl_dir = repo_root / args.hitl_dir
    
    # Get next HITL ID
    hitl_id = get_next_hitl_id(hitl_index_path)
    
    # Create HITL item content
    item_content = create_hitl_item(
        hitl_id,
        args.category,
        args.summary,
        args.required_for,
        args.owner,
        args.reviewer,
        args.related_pr,
        args.related_adr,
        args.related_waiver,
        args.related_task
    )
    
    # Create HITL item file
    item_filepath = hitl_dir / f"{hitl_id}.md"
    item_relative_path = f".repo/hitl/{hitl_id}.md"
    
    if not args.dry_run:
        hitl_dir.mkdir(parents=True, exist_ok=True)
        item_filepath.write_text(item_content, encoding="utf-8")
        print(f"✅ Created HITL item: {item_filepath}")
        
        # Add to index
        add_to_index(hitl_index_path, hitl_id, args.category, args.summary, item_relative_path)
        print(f"✅ Added {hitl_id} to HITL index")
    else:
        print("DRY RUN: Would create HITL item:")
        print(f"  ID: {hitl_id}")
        print(f"  File: {item_filepath}")
        print("\nContent:")
        print(item_content)
    
    print(f"\nHITL Item ID: {hitl_id}")
    sys.exit(0)


if __name__ == "__main__":
    main()
