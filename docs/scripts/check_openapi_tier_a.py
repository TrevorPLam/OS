#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import yaml


def load_tier_a(path: Path) -> list[str]:
    entries: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-"):
            stripped = stripped.lstrip("- ")
        entries.append(stripped)
    return entries


def build_operation_set(openapi: dict) -> set[str]:
    operations: set[str] = set()
    paths = openapi.get("paths", {})
    for path, methods in paths.items():
        for method, info in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            operation_id = info.get("operationId")
            if operation_id:
                operations.add(operation_id)
            operations.add(f"{method.upper()} {path}")
    return operations


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    openapi_path = repo_root / "docs" / "03-reference" / "api" / "openapi.yaml"
    tier_a_path = repo_root / "docs" / "03-reference" / "api" / "tier-a-endpoints.yml"
    api_guide_path = repo_root / "docs" / "03-reference" / "api" / "api-guide.md"

    if not openapi_path.exists() or not tier_a_path.exists() or not api_guide_path.exists():
        print("Required OpenAPI artifacts or Tier A list are missing.")
        return 1

    openapi = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
    operation_set = build_operation_set(openapi)
    tier_a_entries = load_tier_a(tier_a_path)
    api_guide = api_guide_path.read_text(encoding="utf-8")

    missing_in_openapi = [entry for entry in tier_a_entries if entry not in operation_set]
    missing_in_guide = [entry for entry in tier_a_entries if entry not in api_guide]

    if missing_in_openapi or missing_in_guide:
        print("Tier A endpoint coverage warnings:")
        if missing_in_openapi:
            print(" - Missing from OpenAPI:")
            for entry in missing_in_openapi:
                print(f"   - {entry}")
        if missing_in_guide:
            print(" - Missing from api-guide.md:")
            for entry in missing_in_guide:
                print(f"   - {entry}")
        return 1

    print("Tier A endpoint coverage passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
