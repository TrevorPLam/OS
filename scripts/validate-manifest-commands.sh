#!/bin/bash
# validate-manifest-commands.sh
# Validates that commands in repo.manifest.yaml match actual Makefile/package.json commands
#
# Usage: ./scripts/validate-manifest-commands.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

MANIFEST=".repo/repo.manifest.yaml"
MAKEFILE="Makefile"
PACKAGE_JSON="frontend/package.json"

ERRORS=0
WARNINGS=0

echo "Validating manifest commands against actual sources..."

# Check if files exist
if [[ ! -f "$MANIFEST" ]]; then
    echo -e "${RED}Error:${NC} Manifest not found: $MANIFEST"
    exit 1
fi

# Extract commands from manifest
if ! command -v yq &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Warning:${NC} yq or python3 required for YAML parsing. Using basic grep."
    # Basic validation - check if manifest references make commands
    if grep -q "make setup" "$MANIFEST"; then
        if [[ -f "$MAKEFILE" ]] && grep -q "^setup:" "$MAKEFILE"; then
            echo -e "${GREEN}✓${NC} 'make setup' exists in Makefile"
        else
            echo -e "${RED}✗${NC} 'make setup' in manifest but not found in Makefile"
            ERRORS=$((ERRORS + 1))
        fi
    fi

    if grep -q "make lint" "$MANIFEST"; then
        if [[ -f "$MAKEFILE" ]] && grep -q "^lint:" "$MAKEFILE"; then
            echo -e "${GREEN}✓${NC} 'make lint' exists in Makefile"
        else
            echo -e "${YELLOW}⚠${NC} 'make lint' in manifest but not found in Makefile"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi

    if grep -q "make verify" "$MANIFEST"; then
        if [[ -f "$MAKEFILE" ]] && grep -q "^verify:" "$MAKEFILE"; then
            echo -e "${GREEN}✓${NC} 'make verify' exists in Makefile"
        else
            echo -e "${YELLOW}⚠${NC} 'make verify' in manifest but not found in Makefile"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
else
    # Use Python for YAML parsing if available
    if command -v python3 &> /dev/null; then
        python3 <<EOF
import yaml
import sys
import re
from pathlib import Path

repo_root = Path("$REPO_ROOT")
manifest_path = repo_root / ".repo" / "repo.manifest.yaml"
makefile_path = repo_root / "Makefile"
package_json_path = repo_root / "package.json"

errors = 0
warnings = 0

# Load manifest
with open(manifest_path) as f:
    manifest = yaml.safe_load(f)

commands = manifest.get('commands', {})

# Check Makefile targets
if makefile_path.exists():
    with open(makefile_path) as f:
        makefile_content = f.read()

    # Check each manifest command
    for cmd_name, cmd_value in commands.items():
        if not cmd_value or cmd_value == "<UNKNOWN>":
            continue

        # Extract make targets
        make_matches = re.findall(r'make (\w+)', cmd_value)
        for target in make_matches:
            # Check if target exists in Makefile
            if re.search(rf'^{target}:', makefile_content, re.MULTILINE):
                print(f"✓ '{cmd_name}' -> 'make {target}' exists in Makefile")
            else:
                print(f"⚠ '{cmd_name}' -> 'make {target}' not found in Makefile")
                warnings += 1

# Check package.json scripts
if package_json_path.exists():
    import json
    with open(package_json_path) as f:
        package_data = json.load(f)

    scripts = package_data.get('scripts', {})

    for cmd_name, cmd_value in commands.items():
        if not cmd_value:
            continue

        # Check for npm scripts
        npm_matches = re.findall(r'npm run (\w+)', cmd_value)
        for script in npm_matches:
            if script in scripts:
                print(f"✓ '{cmd_name}' -> 'npm run {script}' exists in package.json")
            else:
                print(f"⚠ '{cmd_name}' -> 'npm run {script}' not found in package.json")
                warnings += 1

sys.exit(0 if errors == 0 and warnings == 0 else 1)
EOF
        EXIT_CODE=$?
        if [[ $EXIT_CODE -ne 0 ]]; then
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
fi

# Summary
echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}✗ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Validation passed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${GREEN}✓ All manifest commands validated${NC}"
    exit 0
fi
