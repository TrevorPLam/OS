#!/bin/bash
# check-expired-waivers.sh
# Checks for expired waivers and reports them
#
# Usage: ./scripts/check-expired-waivers.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WAIVER_INDEX=".repo/policy/WAIVERS.md"
WAIVER_DIR=".repo/waivers"
TODAY=$(date +%Y-%m-%d)

if [[ ! -f "$WAIVER_INDEX" ]]; then
    echo "No waivers file found: $WAIVER_INDEX"
    exit 0
fi

EXPIRED_COUNT=0
EXPIRING_SOON_COUNT=0
EXPIRING_SOON_DAYS=7

echo "Checking for expired waivers..."
echo "Today: $TODAY"
echo ""

# Parse active waivers table
while IFS='|' read -r id what owner expires status filepath; do
    # Skip header and separator lines
    [[ "$id" =~ "ID" ]] && continue
    [[ "$id" =~ "---" ]] && continue
    [[ -z "$id" ]] && continue

    id=$(echo "$id" | xargs)
    expires=$(echo "$expires" | xargs)

    if [[ -z "$expires" ]] || [[ "$expires" == "[SET EXPIRATION DATE]" ]]; then
        echo -e "${YELLOW}⚠ Waiver $id has no expiration date set${NC}"
        continue
    fi

    # Compare dates
    if [[ "$expires" < "$TODAY" ]]; then
        echo -e "${RED}✗ EXPIRED: $id (expired on $expires)${NC}"
        EXPIRED_COUNT=$((EXPIRED_COUNT + 1))
    elif [[ "$expires" == "$TODAY" ]]; then
        echo -e "${YELLOW}⚠ EXPIRES TODAY: $id${NC}"
        EXPIRING_SOON_COUNT=$((EXPIRING_SOON_COUNT + 1))
    else
        # Calculate days until expiration
        EXPIRES_EPOCH=$(date -d "$expires" +%s 2>/dev/null || echo "0")
        TODAY_EPOCH=$(date -d "$TODAY" +%s 2>/dev/null || echo "0")

        if [[ $EXPIRES_EPOCH -gt 0 ]] && [[ $TODAY_EPOCH -gt 0 ]]; then
            DAYS_LEFT=$(( (EXPIRES_EPOCH - TODAY_EPOCH) / 86400 ))
            if [[ $DAYS_LEFT -le $EXPIRING_SOON_DAYS ]] && [[ $DAYS_LEFT -gt 0 ]]; then
                echo -e "${YELLOW}⚠ Expires soon: $id (expires in $DAYS_LEFT days on $expires)${NC}"
                EXPIRING_SOON_COUNT=$((EXPIRING_SOON_COUNT + 1))
            fi
        fi
    fi
done < <(grep -A 1000 "## Active Waivers" "$WAIVER_INDEX" | grep "^|" | head -100)

echo ""
if [[ $EXPIRED_COUNT -gt 0 ]]; then
    echo -e "${RED}Found $EXPIRED_COUNT expired waiver(s)${NC}"
    echo "Expired waivers should be archived or renewed."
    exit 1
elif [[ $EXPIRING_SOON_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}Found $EXPIRING_SOON_COUNT waiver(s) expiring soon${NC}"
    exit 0
else
    echo -e "${GREEN}✓ No expired waivers found${NC}"
    exit 0
fi
