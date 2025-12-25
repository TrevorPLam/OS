#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_PATHS = ["/src/", "/src/frontend/", "/docs/"]
PR_REQUIRED_TEXT = [
    "OpenAPI regenerated and committed",
    "docs/03-reference/api/api-guide.md",
    "docs/CHANGELOG.md",
]

LICENSE_PATTERNS = [
    re.compile(r"permission is hereby granted", re.IGNORECASE),
    re.compile(r"apache license", re.IGNORECASE),
    re.compile(r"gnu general public license", re.IGNORECASE),
    re.compile(r"mozilla public license", re.IGNORECASE),
    re.compile(r"copyright", re.IGNORECASE),
]


def find_codeowners(repo_root: Path) -> Path | None:
    for candidate in [repo_root / "CODEOWNERS", repo_root / ".github" / "CODEOWNERS", repo_root / "docs" / "CODEOWNERS"]:
        if candidate.exists():
            return candidate
    return None


def check_security(repo_root: Path, errors: list[str]) -> None:
    security = repo_root / "SECURITY.md"
    if not security.exists():
        errors.append("SECURITY.md is missing")
        return
    content = security.read_text(encoding="utf-8")
    if not re.search(r"[\w.+-]+@[\w.-]+\.[\w-]+", content) and not re.search(r"https?://", content):
        errors.append("SECURITY.md must include a contact email or URL")


def check_license(repo_root: Path, errors: list[str]) -> None:
    license_files = list(repo_root.glob("LICENSE*"))
    if not license_files:
        errors.append("LICENSE file is missing")
        return
    has_valid = False
    for license_file in license_files:
        content = license_file.read_text(encoding="utf-8").strip()
        if len(content) < 100:
            continue
        if any(pattern.search(content) for pattern in LICENSE_PATTERNS):
            has_valid = True
            break
    if not has_valid:
        errors.append("LICENSE file appears empty or missing standard license text")


def check_codeowners(repo_root: Path, errors: list[str]) -> None:
    codeowners = find_codeowners(repo_root)
    if not codeowners:
        errors.append("CODEOWNERS file is missing")
        return
    lines = [line.strip() for line in codeowners.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
    coverage = {path: False for path in REQUIRED_PATHS}
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        path = parts[0]
        for required in REQUIRED_PATHS:
            if path == required:
                coverage[required] = True
    missing = [path for path, covered in coverage.items() if not covered]
    if missing:
        errors.append(f"CODEOWNERS missing owners for: {', '.join(missing)}")


def check_pr_template(repo_root: Path, errors: list[str]) -> None:
    template = repo_root / ".github" / "PULL_REQUEST_TEMPLATE.md"
    if not template.exists():
        errors.append(".github/PULL_REQUEST_TEMPLATE.md is missing")
        return
    content = template.read_text(encoding="utf-8")
    for required in PR_REQUIRED_TEXT:
        if required not in content:
            errors.append(f"PR template missing required text: {required}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    check_security(repo_root, errors)
    check_license(repo_root, errors)
    check_codeowners(repo_root, errors)
    check_pr_template(repo_root, errors)

    if errors:
        print("Repository policy validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Repository policy validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
