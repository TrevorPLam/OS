#!/bin/bash
# verify-repo.sh — Repository Health Check
# Purpose: Validate repository structure and configuration

set -e

echo "=== ConsultantPro Repository Verification ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((FAIL++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/ exists"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1/ missing"
        ((FAIL++))
    fi
}

echo "--- Root Files ---"
check_file "README.md"
check_file "CONTRIBUTING.md"
check_file "CHANGELOG.md"
check_file "TODO.md"
check_file "SECURITY.md"
check_file "Makefile"
check_file "pyproject.toml"
check_file "requirements.txt"
check_file "docker-compose.yml"
check_file "Dockerfile"
check_file ".env.example"

echo ""
echo "--- Source Structure ---"
check_dir "src"
check_file "src/manage.py"
check_dir "src/config"
check_file "src/config/settings.py"
check_dir "src/modules"
check_dir "src/frontend"

echo ""
echo "--- Documentation ---"
check_dir "docs"
check_file "docs/README.md"
check_file "docs/REPO_MAP.md"

echo ""
echo "--- Scripts ---"
check_dir "scripts"

echo ""
echo "--- CI/CD ---"
check_dir ".github/workflows"

echo ""
echo "=== Summary ==="
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}Repository structure is valid!${NC}"
    exit 0
else
    echo -e "${RED}Repository structure has issues.${NC}"
    exit 1
fi
