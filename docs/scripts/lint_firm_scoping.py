#!/usr/bin/env python3
"""
TIER 0 Linting: Forbid Model.objects.all() on firm-scoped models.

This script checks for violations of firm scoping rules:
1. Direct use of Model.objects.all() on firm-scoped models
2. Direct use of Model.objects.filter() without firm parameter

Usage:
    python scripts/lint_firm_scoping.py
    python scripts/lint_firm_scoping.py --fix  # Auto-fix where possible
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Models that MUST be firm-scoped (have firm FK)
FIRM_SCOPED_MODELS = [
    # CRM models
    'Lead', 'Prospect', 'Campaign', 'Proposal', 'Contract',
    # Client models
    'Client',
    # Project models
    'Project',
    # Finance models
    'Invoice', 'Bill', 'LedgerEntry',
    # Document models
    'Folder', 'Document', 'Version',
    # Asset models
    'Asset', 'MaintenanceLog',
]

# Files to check (relative to project root)
FILES_TO_CHECK = [
    'src/modules/*/views.py',
    'src/api/*/views.py',
    'src/modules/*/serializers.py',
    'src/api/*/serializers.py',
]

# Patterns to detect violations
VIOLATION_PATTERNS = [
    # Model.objects.all()
    (r'({models})\.objects\.all\(\)', 'Model.objects.all() forbidden on firm-scoped models. Use Model.firm_scoped.for_firm(firm) instead.'),
    # Model.objects.filter() without firm= or firm__ or client__firm
    (r'({models})\.objects\.filter\((?![^)]*\b(?:firm|client__firm))[^)]*\)', 'Model.objects.filter() without firm parameter. Use firm_scoped.for_firm(firm) or include firm= in filter.'),
    # Model.objects.get() without firm= or firm__ or client__firm
    (r'({models})\.objects\.get\((?![^)]*\b(?:firm|client__firm))[^)]*\)', 'Model.objects.get() without firm parameter. Use firm_scoped.for_firm(firm).get() or include firm= in get.'),
]


def find_violations(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Find firm scoping violations in a file.

    Returns:
        List of (line_number, line_content, violation_message)
    """
    violations = []

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return violations

    # Build regex pattern with all firm-scoped models
    models_pattern = '|'.join(FIRM_SCOPED_MODELS)

    for line_num, line in enumerate(lines, start=1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Check if current line or previous line has exemption comment
        prev_line = lines[line_num - 2] if line_num > 1 else ''
        if '# noqa: firm-scoping' in line or '# TIER 0: verified' in line:
            continue
        if '# noqa: firm-scoping' in prev_line or '# TIER 0: verified' in prev_line:
            continue

        # Check each violation pattern
        for pattern_template, message in VIOLATION_PATTERNS:
            pattern = pattern_template.format(models=models_pattern)
            if re.search(pattern, line):
                violations.append((line_num, line.rstrip(), message))

    return violations


def check_all_files(fix: bool = False) -> int:
    """
    Check all files for firm scoping violations.

    Returns:
        Number of violations found
    """
    project_root = Path(__file__).parent.parent
    total_violations = 0

    print("=" * 80)
    print("TIER 0 Firm Scoping Linter")
    print("=" * 80)
    print()

    # Find all files matching patterns
    files_to_check = []
    for pattern in FILES_TO_CHECK:
        files_to_check.extend(project_root.glob(pattern))

    if not files_to_check:
        print("⚠️  No files found to check.")
        return 0

    print(f"Checking {len(files_to_check)} files...\n")

    for file_path in sorted(files_to_check):
        violations = find_violations(file_path)

        if violations:
            total_violations += len(violations)
            rel_path = file_path.relative_to(project_root)
            print(f"❌ {rel_path}")
            print("-" * 80)

            for line_num, line, message in violations:
                print(f"  Line {line_num}: {message}")
                print(f"    {line}")
                print()

    print("=" * 80)
    if total_violations == 0:
        print("✅ No firm scoping violations found!")
        print("=" * 80)
        return 0
    else:
        print(f"❌ Found {total_violations} firm scoping violation(s).")
        print()
        print("TIER 0 REQUIREMENT: All queries on firm-scoped models MUST include firm context.")
        print()
        print("Fix suggestions:")
        print("  - Use Model.firm_scoped.for_firm(firm) for firm-scoped queries")
        print("  - Use FirmScopedMixin in ViewSets (handles get_queryset automatically)")
        print("  - Include firm= parameter in Model.objects.filter() calls")
        print("=" * 80)
        return total_violations


def main():
    """Main entry point."""
    fix = '--fix' in sys.argv

    violations = check_all_files(fix=fix)

    # Exit with error code if violations found
    sys.exit(1 if violations > 0 else 0)


if __name__ == '__main__':
    main()
