#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned


def extract_anchors(markdown: str) -> set[str]:
    anchors = set()
    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            anchors.add(slugify(match.group(2)))
    return anchors


def normalize_target(raw: str) -> str:
    target = raw.strip()
    if " " in target:
        target = target.split()[0]
    return target


def is_external(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme in {"http", "https"}


def is_localhost(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.hostname in {"localhost", "127.0.0.1"}


def check_external(url: str, timeout: float) -> str | None:
    try:
        request = Request(url, headers={"User-Agent": "docs-link-check"})
        with urlopen(request, timeout=timeout) as response:
            if 200 <= response.status < 400:
                return None
            return f"HTTP {response.status}"
    except HTTPError as exc:
        return f"HTTP {exc.code}"
    except URLError as exc:
        return str(exc.reason)
    except Exception as exc:  # pragma: no cover - fallback safety
        return str(exc)


def iter_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.suffix == ".md":
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=[], help="Files or directories to scan")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout for external links")
    parser.add_argument("--skip-external", action="store_true", help="Skip external link checks")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    targets = [Path(p) for p in args.paths] if args.paths else [repo_root / "README.md", repo_root / "docs"]

    errors: list[str] = []
    markdown_files = iter_markdown_files(targets)

    for md_file in markdown_files:
        content = md_file.read_text(encoding="utf-8")
        anchors = extract_anchors(content)
        for match in LINK_RE.finditer(content):
            target = normalize_target(match.group(1))
            if not target or target.startswith("mailto:") or target.startswith("tel:"):
                continue

            if target.startswith("#"):
                fragment = target[1:]
                if fragment and fragment not in anchors:
                    errors.append(f"{md_file}: missing anchor '#{fragment}'")
                continue

            if is_external(target):
                if is_localhost(target):
                    continue
                if args.skip_external:
                    continue
                error = check_external(target, args.timeout)
                if error:
                    errors.append(f"{md_file}: external link {target} failed ({error})")
                continue

            parsed = urlparse(target)
            path = parsed.path
            fragment = parsed.fragment

            if path.startswith("/"):
                resolved = repo_root / path.lstrip("/")
            else:
                resolved = (md_file.parent / path).resolve()

            if not resolved.exists():
                errors.append(f"{md_file}: missing file '{path}'")
                continue

            if fragment:
                try:
                    target_content = resolved.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                target_anchors = extract_anchors(target_content)
                if fragment not in target_anchors:
                    errors.append(f"{md_file}: missing anchor '#{fragment}' in {path}")

    if errors:
        print("Markdown link check failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Markdown link check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
