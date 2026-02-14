#!/bin/bash
# WHY: Single entry point enforces consistent run order
# Every step must succeed before the next runs (set -e)
set -e

echo "=== DBB2 BETTING ENGINE ==="
echo "Date: $(date +%Y-%m-%d)"
echo ""

echo "[1/8] Fetching today's projections from DBB2..."
python src/odds_ingestion.py --fetch-projections

echo "[2/8] Fetching today's odds from The Odds API..."
python src/odds_ingestion.py --fetch-odds

echo "[3/8] Calculating Expected Value on all props..."
python src/ev_calculator.py

echo "[4/8] Applying Kelly sizing..."
python src/kelly_sizer.py --use-ledger

echo "[5/8] Generating bet slip..."
python src/bet_slip.py --source sportsbook

echo "[6/8] Fetching Kalshi markets..."
python src/kalshi_ingestion.py --fetch-markets

echo "[7/8] Calculating Kalshi EV..."
python src/kalshi_ev_calculator.py

echo "[8/8] Running bet placer (budget + CSV + combined slip)..."
python src/bet_placer.py

echo ""
echo "=== DONE. Bet slips saved to data/bet_slips/ ==="
echo "=== Master CSV: data/bets/master_bets.csv ==="
