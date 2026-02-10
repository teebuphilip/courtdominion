#!/bin/bash
# run_all_seasons.sh
#
# Collects all 30 seasons of NBA data (1995-2025)
# Run one season per day to respect rate limits
#
# Usage:
#   ./run_all_seasons.sh                    # Collect all seasons
#   ./run_all_seasons.sh --start 2020       # Start from 2020-21 season
#   ./run_all_seasons.sh --dry-run          # Show what would be collected

set -e

OUTPUT_DIR="raw_data"
PROGRESS_FILE=".collection_progress.json"
DRY_RUN=false
START_YEAR=1995
END_YEAR=2024

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --start)
            START_YEAR="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
    echo '{"completed": [], "failed": [], "last_run": null}' > "$PROGRESS_FILE"
fi

# Function to check if season is already collected
is_completed() {
    local season=$1
    grep -q "\"$season\"" "$PROGRESS_FILE"
}

# Function to mark season as completed
mark_completed() {
    local season=$1
    local status=$2
    
    # Update progress file (simple approach, could use jq for robustness)
    python3 -c "
import json
with open('$PROGRESS_FILE', 'r') as f:
    data = json.load(f)
if '$status' == 'completed':
    if '$season' not in data['completed']:
        data['completed'].append('$season')
else:
    if '$season' not in data['failed']:
        data['failed'].append('$season')
data['last_run'] = '$(date -Iseconds)'
with open('$PROGRESS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
}

echo "=============================================="
echo "NBA SEASON DATA COLLECTION"
echo "=============================================="
echo "Start year: $START_YEAR"
echo "End year: $END_YEAR"
echo "Output dir: $OUTPUT_DIR"
echo "Dry run: $DRY_RUN"
echo "=============================================="
echo ""

# Generate list of seasons
SEASONS=()
for year in $(seq $START_YEAR $END_YEAR); do
    next_year=$((year + 1))
    season="${year}-$(printf "%02d" $((next_year % 100)))"
    SEASONS+=("$season")
done

echo "Total seasons to collect: ${#SEASONS[@]}"
echo ""

# Check what's already done
COMPLETED_COUNT=0
for season in "${SEASONS[@]}"; do
    if is_completed "$season"; then
        ((COMPLETED_COUNT++))
    fi
done

echo "Already completed: $COMPLETED_COUNT"
echo "Remaining: $((${#SEASONS[@]} - COMPLETED_COUNT))"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN - Would collect these seasons:"
    for season in "${SEASONS[@]}"; do
        if is_completed "$season"; then
            echo "  ✓ $season (already completed)"
        else
            echo "  ○ $season (pending)"
        fi
    done
    exit 0
fi

# Collect seasons
DAY=1
for season in "${SEASONS[@]}"; do
    # Check if already completed
    if is_completed "$season"; then
        echo "[$DAY/${#SEASONS[@]}] Skipping $season (already completed)"
        ((DAY++))
        continue
    fi
    
    echo ""
    echo "=============================================="
    echo "[$DAY/${#SEASONS[@]}] COLLECTING SEASON: $season"
    echo "=============================================="
    echo ""
    
    # Run collection script
    if python3 collect_nba_season.py --season "$season" --output "$OUTPUT_DIR"; then
        echo ""
        echo "✓ Successfully collected $season"
        mark_completed "$season" "completed"
    else
        echo ""
        echo "✗ Failed to collect $season"
        mark_completed "$season" "failed"
        echo "Continuing to next season..."
    fi
    
    ((DAY++))
    
    # If not last season, wait before next collection
    if [ $DAY -le ${#SEASONS[@]} ]; then
        echo ""
        echo "Waiting 24 hours before next collection..."
        echo "Next: ${SEASONS[$DAY-1]}"
        echo "Press Ctrl+C to cancel"
        echo ""
        
        # Wait 24 hours (86400 seconds)
        # For testing, you can change this to 60 (1 minute)
        sleep 86400
    fi
done

echo ""
echo "=============================================="
echo "COLLECTION COMPLETE"
echo "=============================================="
echo ""

# Print summary
python3 -c "
import json
with open('$PROGRESS_FILE', 'r') as f:
    data = json.load(f)
print(f\"Completed: {len(data['completed'])} seasons\")
print(f\"Failed: {len(data['failed'])} seasons\")
if data['failed']:
    print(f\"\\nFailed seasons: {', '.join(data['failed'])}\")
"

echo ""
echo "All data collected to: $OUTPUT_DIR"
echo "Progress tracked in: $PROGRESS_FILE"
