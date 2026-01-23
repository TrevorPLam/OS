#!/usr/bin/env python3
"""
Sync HITL items status to PR description.

This script reads HITL items from .repo/policy/HITL.md and .repo/hitl/
and updates the PR description with current status.

Usage:
    python scripts/sync-hitl-to-pr.py [PR_NUMBER]

    If PR_NUMBER is not provided, tries to detect from git context.

Environment variables:
    GITHUB_TOKEN: GitHub API token (required for API updates)
    GITHUB_REPOSITORY: Repository in format owner/repo (auto-detected in CI)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    if __name__ == "__main__":
        print("Warning: 'requests' not installed. Install with: pip install requests", file=sys.stderr)
        print("Script will work but cannot update PRs via API.", file=sys.stderr)

REPO_ROOT = Path(__file__).parent.parent
HITL_INDEX = REPO_ROOT / ".repo" / "policy" / "HITL.md"
HITL_DIR = REPO_ROOT / ".repo" / "hitl"


def parse_hitl_index() -> List[Dict[str, str]]:
    """Parse HITL index file and return list of active items."""
    if not HITL_INDEX.exists():
        return []

    items = []
    in_active_table = False

    with open(HITL_INDEX, 'r', encoding='utf-8') as f:
        for line in f:
            # Detect active table
            if "### Active" in line:
                in_active_table = True
                continue
            if "### Archived" in line:
                in_active_table = False
                continue

            if not in_active_table:
                continue

            # Parse table row: |ID|Category|Status|Summary|Filepath|
            match = re.match(r'^\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|', line)
            if match and not match.group(1).strip().startswith('ID'):
                items.append({
                    'id': match.group(1).strip(),
                    'category': match.group(2).strip(),
                    'status': match.group(3).strip(),
                    'summary': match.group(4).strip(),
                    'filepath': match.group(5).strip(),
                })

    return items


def read_hitl_item(item_id: str) -> Optional[Dict[str, str]]:
    """Read HITL item file and return details."""
    item_file = HITL_DIR / f"{item_id}.md"
    if not item_file.exists():
        return None

    details = {'id': item_id}
    with open(item_file, 'r', encoding='utf-8') as f:
        content = f.read()

        # Extract key fields
        for field in ['Category', 'Status', 'Summary', 'Owner', 'Date Required', 'Date Completed']:
            match = re.search(rf'\*\*{field}:\*\*\s*(.+)', content)
            if match:
                details[field.lower().replace(' ', '_')] = match.group(1).strip()

    return details


def generate_hitl_section(items: List[Dict[str, str]]) -> str:
    """Generate HITL section for PR description."""
    if not items:
        return "## HITL Items\n\n✅ No active HITL items."

    section = "## HITL Items\n\n"
    section += "| ID | Category | Status | Summary |\n"
    section += "|----|----------|--------|----------|\n"

    for item in items:
        status_emoji = {
            'Completed': '✅',
            'Superseded': '✅',
            'Pending': '⏳',
            'In Progress': '🔄',
            'Blocked': '🚫'
        }.get(item['status'], '❓')
        section += f"| {item['id']} | {item['category']} | {status_emoji} {item['status']} | {item['summary']} |\n"

    # Check for blocking items
    blocking = [i for i in items if i['status'] not in ['Completed', 'Superseded']]
    if blocking:
        section += f"\n⚠️ **Warning**: {len(blocking)} HITL item(s) not Completed. PR merge may be blocked per `.repo/policy/QUALITY_GATES.md`.\n"
        section += "\n**Blocking items:**\n"
        for item in blocking:
            section += f"- {item['id']}: {item['summary']} ({item['status']})\n"

    return section


def update_pr_via_api(pr_number: str, section: str, repo: str, token: str) -> bool:
    """Update PR description via GitHub API."""
    if not HAS_REQUESTS:
        return False

    owner, repo_name = repo.split('/')
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"

    # Get current PR body
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pr_data = response.json()
        current_body = pr_data.get("body", "")

        # Check if HITL section already exists
        if "## HITL Items" in current_body:
            # Replace existing section
            pattern = r"## HITL Items.*?(?=\n## |\Z)"
            new_body = re.sub(pattern, section, current_body, flags=re.DOTALL)
        else:
            # Append section
            new_body = f"{current_body}\n\n{section}" if current_body else section

        # Update PR
        update_response = requests.patch(
            url,
            headers=headers,
            json={"body": new_body}
        )
        update_response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error updating PR via API: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    items = parse_hitl_index()

    if not items:
        print("No active HITL items found.")
        return 0

    section = generate_hitl_section(items)
    print(section)

    # Try to update PR if number provided
    if len(sys.argv) > 1:
        pr_number = sys.argv[1]
        token = os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")

        if token and repo:
            print(f"\nUpdating PR #{pr_number} via GitHub API...")
            if update_pr_via_api(pr_number, section, repo, token):
                print(f"✅ Successfully updated PR #{pr_number}")
                return 0
            else:
                print(f"⚠️  Failed to update PR via API, falling back to manual method")

        # Fallback: GitHub CLI or manual
        print(f"\nTo update PR #{pr_number} manually:")
        print(f"  gh pr edit {pr_number} --body-file <(echo '{section}')")
        print(f"\nOr copy the section above and paste into PR description.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
