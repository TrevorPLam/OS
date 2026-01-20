#!/usr/bin/env python3
"""
Inventory API endpoint coverage for modules.

Checks for urls.py/views.py in src/modules/<module> and src/api/<module>,
then outputs a Markdown table for documentation updates.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def resolve_repo_root(repo_root: str | None) -> Path:
    root = Path(repo_root).expanduser().resolve() if repo_root else Path(__file__).resolve().parents[2]
    if not root.exists():
        raise FileNotFoundError(f"Repository root not found: {root}")
    return root


def require_directory(root: Path, relative_path: str) -> Path:
    directory = root / relative_path
    if not directory.exists():
        raise FileNotFoundError(f"Missing required directory: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Expected directory but found file: {directory}")
    return directory


def optional_directory(root: Path, relative_path: str) -> Path | None:
    directory = root / relative_path
    return directory if directory.exists() and directory.is_dir() else None


def list_module_names(modules_dir: Path) -> list[str]:
    module_names = [
        path.name
        for path in modules_dir.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    ]
    return sorted(module_names)


def has_endpoint_file(directory: Path | None, filename: str) -> bool:
    if directory is None:
        return False
    return (directory / filename).exists()


def build_inventory(repo_root: Path) -> list[dict[str, object]]:
    modules_dir = require_directory(repo_root, "src/modules")
    api_dir = optional_directory(repo_root, "src/api")
    inventory: list[dict[str, object]] = []

    for module_name in list_module_names(modules_dir):
        module_dir = modules_dir / module_name
        api_module_dir = api_dir / module_name if api_dir else None
        module_urls = has_endpoint_file(module_dir, "urls.py")
        module_views = has_endpoint_file(module_dir, "views.py")
        api_urls = has_endpoint_file(api_module_dir, "urls.py")
        api_views = has_endpoint_file(api_module_dir, "views.py")

        inventory.append(
            {
                "module": module_name,
                "module_urls": module_urls,
                "module_views": module_views,
                "api_urls": api_urls,
                "api_views": api_views,
            }
        )

    return inventory


def coverage_status(entry: dict[str, object]) -> str:
    module_complete = entry["module_urls"] and entry["module_views"]
    api_complete = entry["api_urls"] and entry["api_views"]
    if module_complete:
        return "module"
    if api_complete:
        return "api"
    if entry["module_urls"] or entry["module_views"] or entry["api_urls"] or entry["api_views"]:
        return "partial"
    return "missing"


def render_markdown_table(inventory: list[dict[str, object]]) -> str:
    header = (
        "| Module | Module URLs | Module Views | API URLs | API Views | Coverage |\n"
        "| --- | --- | --- | --- | --- | --- |"
    )
    rows = []
    for entry in inventory:
        rows.append(
            "| {module} | {module_urls} | {module_views} | {api_urls} | {api_views} | {coverage} |".format(
                module=entry["module"],
                module_urls="✅" if entry["module_urls"] else "—",
                module_views="✅" if entry["module_views"] else "—",
                api_urls="✅" if entry["api_urls"] else "—",
                api_views="✅" if entry["api_views"] else "—",
                coverage=coverage_status(entry),
            )
        )
    return "\n".join([header, *rows])


def write_output(path: Path, content: str) -> None:
    try:
        path.write_text(content + "\n", encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Unable to write output to {path}: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory API endpoint coverage for modules.")
    parser.add_argument(
        "--repo-root",
        help="Path to repo root (defaults to repository containing this script).",
    )
    parser.add_argument(
        "--output",
        help="Optional output path for Markdown table (prints to stdout if omitted).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = resolve_repo_root(args.repo_root)
        inventory = build_inventory(repo_root)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    table = render_markdown_table(inventory)
    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        try:
            write_output(output_path, table)
        except OSError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 3
    else:
        print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
