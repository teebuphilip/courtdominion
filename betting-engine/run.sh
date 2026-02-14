#!/bin/bash
# WHY: Single entry point enforces consistent run order
# Every step must succeed before the next runs (set -e)
set -e

echo "=== DBB2 BETTING ENGINE ==="
echo "Date: $(date +%Y-%m-%d)"
echo ""

echo "[1/5] Fetching today's projections from DBB2..."
python src/odds_ingestion.py --fetch-projections

echo "[2/5] Fetching today's odds from The Odds API..."
python src/odds_ingestion.py --fetch-odds

echo "[3/5] Calculating Expected Value on all props..."
python src/ev_calculator.py

echo "[4/5] Applying Kelly sizing..."
python src/kelly_sizer.py

echo "[5/5] Generating bet slip..."
python src/bet_slip.py

echo ""
echo "=== DONE. Bet slip saved to data/bet_slips/ ==="
