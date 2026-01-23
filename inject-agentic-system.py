#!/usr/bin/env python4
"""
Agentic System Injection Script
Injects all files from AGENTIC_SYSTEM_COMPLETE_FILE_MAPPING_WITH_CONTENT.json into target repository
Designed for zero-friction agent execution
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import shutil


class AgenticSystemInjector:
    """Handles injection of agentic system files into a target repository."""

    def __init__(self, mapping_file: str, target_root: str, dry_run: bool = False):
        self.mapping_file = Path(mapping_file)
        self.target_root = Path(target_root)
        self.dry_run = dry_run
        self.mapping_data = None
        self.injection_order = []
        self.errors = []
        self.warnings = []
        self.created_files = []
        self.skipped_files = []

    def load_mapping(self) -> bool:
        """Load the mapping JSON file."""
        try:
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                self.mapping_data = json.load(f)
            print(f"[OK] Loaded mapping file: {self.mapping_file}")
            return True
        except Exception as e:
            self.errors.append(f"Failed to load mapping file: {e}")
            return False

    def normalize_path(self, path: str) -> str:
        """Normalize file paths (remove leading /, handle relative paths)."""
        # Remove leading slash if present
        if path.startswith("/"):
            path = path[1:]
        return path

    def determine_injection_order(self) -> List[Dict]:
        """Determine optimal injection order based on dependencies."""
        if not self.mapping_data:
            self.errors.append("Mapping data not loaded")
            return []

        # Priority order: policies first, then entry points, then everything else
        priority_categories = [
            "policy_governance",
            "root_entry_points",
            "agent_framework",
            "task_management",
            "templates_schemas",
            "automation_scripts",
            "shell_scripts",
            "context_files",
            "folder_guides",
            "cicd_integration",
            "supporting_documentation",
        ]

        ordered_files = []
        processed_paths = set()

        categories = self.mapping_data.get("categories", {})

        # Process by priority categories
        for category in priority_categories:
            if category in categories:
                files = categories[category].get("files", [])
                for file_info in files:
                    if file_info.get("content") is not None:
                        path = self.normalize_path(file_info["path"])
                        if path not in processed_paths:
                            ordered_files.append({"path": path, "category": category, "file_info": file_info})
                            processed_paths.add(path)

        # Add any remaining files
        for category, category_data in categories.items():
            if category not in priority_categories:
                files = category_data.get("files", [])
                for file_info in files:
                    if file_info.get("content") is not None:
                        path = self.normalize_path(file_info["path"])
                        if path not in processed_paths:
                            ordered_files.append({"path": path, "category": category, "file_info": file_info})
                            processed_paths.add(path)

        self.injection_order = ordered_files
        print(f"[OK] Determined injection order: {len(ordered_files)} files")
        return ordered_files

    def create_directory(self, dir_path: Path) -> bool:
        """Create directory if it doesn't exist."""
        try:
            if not dir_path.exists():
                if not self.dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[OK] Created directory: {dir_path}")
            return True
        except Exception as e:
            self.errors.append(f"Failed to create directory {dir_path}: {e}")
            return False

    def should_skip_file(self, file_info: Dict, target_path: Path) -> tuple[bool, Optional[str]]:
        """Determine if file should be skipped and why."""
        # Skip if content is None (directory or missing file)
        if file_info.get("content") is None:
            return True, "No content (directory or missing file)"

        # Skip if file already exists and is identical
        if target_path.exists() and target_path.is_file():
            try:
                existing_content = target_path.read_text(encoding="utf-8")
                if existing_content == file_info["content"]:
                    return True, "File exists and is identical"
            except:
                pass  # If we can't read it, we'll overwrite it

        return False, None

    def inject_file(self, file_info: Dict, target_path: Path) -> bool:
        """Inject a single file."""
        # Check if should skip
        should_skip, reason = self.should_skip_file(file_info, target_path)
        if should_skip:
            self.skipped_files.append({"path": str(target_path), "reason": reason})
            print(f"[SKIP] {target_path}: {reason}")
            return True

        # Create parent directory
        parent_dir = target_path.parent
        if not self.create_directory(parent_dir):
            return False

        # Write file
        try:
            if not self.dry_run:
                target_path.write_text(file_info["content"], encoding="utf-8")
            self.created_files.append(str(target_path))
            print(f"[OK] Injected: {target_path}")
            return True
        except Exception as e:
            self.errors.append(f"Failed to inject {target_path}: {e}")
            return False

    def make_executable(self, file_path: Path) -> bool:
        """Make script files executable (Unix-like systems)."""
        if sys.platform == "win32":
            return True  # Windows doesn't use executable bits

        try:
            if file_path.exists() and file_path.is_file():
                file_path.chmod(0o755)
                return True
        except Exception as e:
            self.warnings.append(f"Could not make {file_path} executable: {e}")
        return False

    def inject_all(self) -> bool:
        """Inject all files in the determined order."""
        if not self.load_mapping():
            return False

        self.determine_injection_order()

        print(f"\n{'[DRY RUN] ' if self.dry_run else ''}Injecting {len(self.injection_order)} files...\n")

        for item in self.injection_order:
            file_info = item["file_info"]
            path = item["path"]
            target_path = self.target_root / path

            # Inject file
            if not self.inject_file(file_info, target_path):
                continue

            # Make scripts executable
            if path.endswith((".sh", ".py")) and "scripts" in path:
                self.make_executable(target_path)

        return len(self.errors) == 0

    def generate_report(self) -> str:
        """Generate injection report."""
        report = []
        report.append("\n" + "=" * 60)
        report.append("AGENTIC SYSTEM INJECTION REPORT")
        report.append("=" * 60)
        report.append(f"\nTarget Repository: {self.target_root}")
        report.append(f"Mapping File: {self.mapping_file}")
        report.append(f"Dry Run: {self.dry_run}")
        report.append(f"\nFiles Processed: {len(self.injection_order)}")
        report.append(f"Files Created: {len(self.created_files)}")
        report.append(f"Files Skipped: {len(self.skipped_files)}")
        report.append(f"Errors: {len(self.errors)}")
        report.append(f"Warnings: {len(self.warnings)}")

        if self.created_files:
            report.append(f"\n[OK] Created Files ({len(self.created_files)}):")
            for f in self.created_files[:20]:  # Show first 20
                report.append(f"   - {f}")
            if len(self.created_files) > 20:
                report.append(f"   ... and {len(self.created_files) - 20} more")

        if self.skipped_files:
            report.append(f"\n[SKIP] Skipped Files ({len(self.skipped_files)}):")
            for f in self.skipped_files[:10]:  # Show first 10
                report.append(f"   - {f['path']}: {f['reason']}")
            if len(self.skipped_files) > 10:
                report.append(f"   ... and {len(self.skipped_files) - 10} more")

        if self.errors:
            report.append(f"\n[ERROR] Errors ({len(self.errors)}):")
            for e in self.errors:
                report.append(f"   - {e}")

        if self.warnings:
            report.append(f"\n[WARN] Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                report.append(f"   - {w}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Inject agentic system files into target repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (test without making changes)
  python inject-agentic-system.py --dry-run

  # Inject into current directory
  python inject-agentic-system.py

  # Inject into specific directory
  python inject-agentic-system.py --target /path/to/repo

  # Use custom mapping file
  python inject-agentic-system.py --mapping custom-mapping.json
        """,
    )

    parser.add_argument(
        "--mapping",
        default="AGENTIC_SYSTEM_COMPLETE_FILE_MAPPING_WITH_CONTENT.json",
        help="Path to mapping JSON file (default: AGENTIC_SYSTEM_COMPLETE_FILE_MAPPING_WITH_CONTENT.json)",
    )
    parser.add_argument("--target", default=".", help="Target repository root directory (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Test injection without making changes")
    parser.add_argument("--report", help="Save report to file")

    args = parser.parse_args()

    # Validate inputs
    mapping_path = Path(args.mapping)
    if not mapping_path.exists():
        print(f"❌ Error: Mapping file not found: {mapping_path}")
        sys.exit(1)

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"❌ Error: Target directory does not exist: {target_path}")
        sys.exit(1)

    # Create injector and run
    injector = AgenticSystemInjector(mapping_file=str(mapping_path), target_root=str(target_path), dry_run=args.dry_run)

    success = injector.inject_all()

    # Generate and print report
    report = injector.generate_report()
    try:
        print(report)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        print(report.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))

    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        report_path.write_text(report, encoding="utf-8")
        print(f"\n[REPORT] Report saved to: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
