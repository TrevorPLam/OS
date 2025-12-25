#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_DIRS = [
    "01-tutorials",
    "02-how-to",
    "03-reference",
    "04-explanation",
    "05-decisions",
    "06-user-guides",
    "07-api-client",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    docs_dir = repo_root / "docs"
    missing = []

    readme = docs_dir / "README.md"
    changelog = docs_dir / "CHANGELOG.md"

    if not readme.exists():
        missing.append(str(readme))
    if not changelog.exists():
        missing.append(str(changelog))

    for required in REQUIRED_DIRS:
        path = docs_dir / required
        if not path.exists():
            missing.append(str(path))

    if missing:
        print("Docs structure validation failed. Missing:")
        for item in missing:
            print(f" - {item}")
        return 1

    print("Docs structure validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
