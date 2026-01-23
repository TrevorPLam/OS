#!/bin/bash
# archive-hitl-items.sh
# Archives completed or superseded HITL items from Active to Archived table
#
# Usage: ./scripts/archive-hitl-items.sh [--dry-run]
#   --dry-run: Show what would be archived without making changes

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}DRY RUN MODE: No changes will be made${NC}\n"
fi

HITL_INDEX=".repo/policy/HITL.md"
HITL_DIR=".repo/hitl"
TODAY=$(date +%Y-%m-%d)

if [[ ! -f "$HITL_INDEX" ]]; then
    echo -e "${RED}Error:${NC} HITL index not found: $HITL_INDEX"
    exit 1
fi

ARCHIVED_COUNT=0

# Parse active HITL items and find completed/superseded ones
echo "Checking for HITL items to archive..."

# Read HITL.md and process
TEMP_FILE=$(mktemp)
IN_ACTIVE_TABLE=false
IN_ARCHIVED_TABLE=false
ARCHIVED_ITEMS=()

while IFS= read -r line; do
    # Detect table sections
    if [[ "$line" =~ "### Active" ]]; then
        IN_ACTIVE_TABLE=true
        IN_ARCHIVED_TABLE=false
        echo "$line" >> "$TEMP_FILE"
        # Print header
        read -r header_line
        echo "$header_line" >> "$TEMP_FILE"
        read -r separator_line
        echo "$separator_line" >> "$TEMP_FILE"
        continue
    fi

    if [[ "$line" =~ "### Archived" ]]; then
        IN_ACTIVE_TABLE=false
        IN_ARCHIVED_TABLE=true
        echo "$line" >> "$TEMP_FILE"
        # Print header
        read -r header_line
        echo "$header_line" >> "$TEMP_FILE"
        read -r separator_line
        echo "$separator_line" >> "$TEMP_FILE"
        continue
    fi

    # Process active table rows
    if [[ "$IN_ACTIVE_TABLE" == true ]] && [[ "$line" =~ ^\| ]]; then
        # Skip header/separator
        if [[ "$line" =~ "^\|.*ID\|" ]] || [[ "$line" =~ "^\|.*---\|" ]]; then
            echo "$line" >> "$TEMP_FILE"
            continue
        fi

        # Parse row: |ID|Category|Status|Summary|Filepath|
        IFS='|' read -r -a fields <<< "$line"
        if [[ ${#fields[@]} -ge 4 ]]; then
            HITL_ID=$(echo "${fields[1]}" | xargs)
            STATUS=$(echo "${fields[3]}" | xargs)

            # Check if item should be archived
            if [[ "$STATUS" == "Completed" ]] || [[ "$STATUS" == "Superseded" ]]; then
                ARCHIVED_ITEMS+=("$line")
                ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))

                # Update HITL item file
                HITL_FILE="$HITL_DIR/$HITL_ID.md"
                if [[ -f "$HITL_FILE" ]]; then
                    if [[ "$DRY_RUN" == false ]]; then
                        # Add Archived On date if not present
                        if ! grep -q "^\*\*Archived On:\*\*" "$HITL_FILE"; then
                            sed -i "/^## Notes/a\\
\\
**Archived On:** $TODAY" "$HITL_FILE"
                        fi
                    fi
                    echo -e "${GREEN}✓${NC} Would archive: $HITL_ID ($STATUS)"
                fi
            else
                # Keep in active table
                echo "$line" >> "$TEMP_FILE"
            fi
        else
            echo "$line" >> "$TEMP_FILE"
        fi
    # Process archived table - append new items
    elif [[ "$IN_ARCHIVED_TABLE" == true ]] && [[ "$line" =~ ^\| ]]; then
        echo "$line" >> "$TEMP_FILE"
        # Append archived items after existing archived items
        if [[ ${#ARCHIVED_ITEMS[@]} -gt 0 ]] && [[ ! "$line" =~ "^\|.*ID\|" ]] && [[ ! "$line" =~ "^\|.*---\|" ]]; then
            # Check if this is the last archived item
            # (Simple heuristic: if next line is not a table row, we're at the end)
            for archived_line in "${ARCHIVED_ITEMS[@]}"; do
                echo "$archived_line" >> "$TEMP_FILE"
            done
            ARCHIVED_ITEMS=()  # Clear so we don't duplicate
        fi
    else
        echo "$line" >> "$TEMP_FILE"
    fi
done < "$HITL_INDEX"

# Append any remaining archived items at the end of archived table
if [[ ${#ARCHIVED_ITEMS[@]} -gt 0 ]]; then
    # Find where archived table ends and append
    sed -i '/^### Archived/,/^## / {
        /^## /{
            i\
'"$(printf '%s\n' "${ARCHIVED_ITEMS[@]}")"
        }
    }' "$TEMP_FILE" 2>/dev/null || {
        # Fallback: append at end of file
        for archived_line in "${ARCHIVED_ITEMS[@]}"; do
            echo "$archived_line" >> "$TEMP_FILE"
        done
    }
fi

# Summary
echo ""
if [[ $ARCHIVED_COUNT -gt 0 ]]; then
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${YELLOW}Would archive $ARCHIVED_COUNT HITL item(s)${NC}"
        echo "Run without --dry-run to apply changes"
    else
        # Replace original file
        mv "$TEMP_FILE" "$HITL_INDEX"
        echo -e "${GREEN}✓ Archived $ARCHIVED_COUNT HITL item(s)${NC}"
        echo "Updated: $HITL_INDEX"
    fi
else
    rm "$TEMP_FILE"
    echo -e "${GREEN}✓ No HITL items to archive${NC}"
fi

exit 0
