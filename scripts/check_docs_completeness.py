#!/usr/bin/env python3
"""
Documentation completeness checker for ConsultantPro.

Verifies that required documentation files exist and that the docs index
links to all required sections.

Evidence: Implements Constitution Section 15 - Minimal Enforcement Plan
(CI check: fails if required directories/docs are missing).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Required core documentation files
REQUIRED_CORE_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "TODO.md",
    "docs/README.md",
    "docs/codingconstitution.md",
    "docs/REPO_MAP.md",
    "docs/OPERATIONS.md",
    "docs/TROUBLESHOOTING.md",
    "docs/STYLE_GUIDE.md",
    "docs/GLOSSARY.md",
]

# Required Diátaxis directories (evidence: scripts/validate_docs_structure.py:7-15)
REQUIRED_DIRS = [
    "docs/01-tutorials",
    "docs/02-how-to",
    "docs/03-reference",
    "docs/04-explanation",
    "docs/05-decisions",
    "docs/06-user-guides",
    "docs/07-api-client",
    "docs/runbooks",
    "docs/compliance",
    "docs/ARCHIVE",
]

# Required README files in each Diátaxis directory
REQUIRED_READMES = [
    "docs/01-tutorials/README.md",
    "docs/02-how-to/README.md",
    "docs/03-reference/README.md",
    "docs/04-explanation/README.md",
    "docs/05-decisions/README.md",
    "docs/06-user-guides/README.md",
    "docs/07-api-client/README.md",
    "docs/runbooks/README.md",
    "docs/ARCHIVE/README.md",
]

# Keywords that should appear in docs/README.md (evidence-based index)
REQUIRED_INDEX_KEYWORDS = [
    "01-tutorials",
    "02-how-to",
    "03-reference",
    "04-explanation",
    "05-decisions",
    "runbooks",
]


def main() -> int:
    """
    Check documentation completeness.

    Returns:
        0 if all checks pass, 1 if any check fails
    """
    repo_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    # Check 1: Required core documentation files
    print("Checking required core documentation files...")
    for doc_path in REQUIRED_CORE_DOCS:
        full_path = repo_root / doc_path
        if not full_path.exists():
            errors.append(f"Missing required doc: {doc_path}")
        else:
            print(f"  ✓ {doc_path}")

    # Check 2: Required directories
    print("\nChecking required directories...")
    for dir_path in REQUIRED_DIRS:
        full_path = repo_root / dir_path
        if not full_path.exists():
            errors.append(f"Missing required directory: {dir_path}")
        else:
            print(f"  ✓ {dir_path}/")

    # Check 3: Required README files in each directory
    print("\nChecking directory README files...")
    for readme_path in REQUIRED_READMES:
        full_path = repo_root / readme_path
        if not full_path.exists():
            errors.append(f"Missing README: {readme_path}")
        else:
            print(f"  ✓ {readme_path}")

    # Check 4: docs/README.md index completeness
    print("\nChecking docs index completeness...")
    docs_readme = repo_root / "docs/README.md"
    if docs_readme.exists():
        content = docs_readme.read_text(encoding="utf-8")
        for keyword in REQUIRED_INDEX_KEYWORDS:
            if keyword not in content:
                errors.append(
                    f"docs/README.md missing reference to '{keyword}' "
                    f"(index should link to all documentation sections)"
                )
            else:
                print(f"  ✓ docs/README.md references {keyword}")
    else:
        errors.append("docs/README.md is missing (cannot check index)")

    # Check 5: Constitution exists (critical)
    print("\nChecking constitution...")
    constitution = repo_root / "docs/codingconstitution.md"
    if constitution.exists():
        # Check it's not a stub
        content = constitution.read_text(encoding="utf-8")
        if len(content) < 1000:
            errors.append(
                "docs/codingconstitution.md appears to be a stub "
                f"({len(content)} chars, expected > 1000)"
            )
        else:
            print(f"  ✓ Constitution exists and appears complete ({len(content)} chars)")
    else:
        errors.append("CRITICAL: docs/codingconstitution.md is missing")

    # Report results
    print("\n" + "=" * 60)
    if errors:
        print("❌ Documentation completeness check FAILED:")
        for error in errors:
            print(f"  - {error}")
        print("\nTo fix:")
        print("  1. Create missing files/directories")
        print("  2. Update docs/README.md to reference all sections")
        print("  3. Run this check again: python scripts/check_docs_completeness.py")
        return 1
    else:
        print("✅ Documentation completeness check PASSED")
        print(f"  - {len(REQUIRED_CORE_DOCS)} core docs exist")
        print(f"  - {len(REQUIRED_DIRS)} required directories exist")
        print(f"  - {len(REQUIRED_READMES)} directory READMEs exist")
        print(f"  - docs index references {len(REQUIRED_INDEX_KEYWORDS)} sections")
        return 0


if __name__ == "__main__":
    sys.exit(main())
