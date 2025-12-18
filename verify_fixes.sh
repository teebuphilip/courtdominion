#!/bin/bash
# Verification Script - Check Current Code State
# Run from: ~/Downloads/courtdominion/

echo "=============================================="
echo "  CODE VERIFICATION SCRIPT"
echo "=============================================="
echo ""

echo "CHECK #1: Cache Path Fix (dbb2_projections.py line 17)"
echo "------------------------------------------------------"
CACHE_LINE=$(grep -n "CACHE_FILE = Path" ./courtdominion-app/automation/dbb2_projections.py)
echo "$CACHE_LINE"
echo ""

if echo "$CACHE_LINE" | grep -q "/data/outputs/player_stats_cache.json"; then
    echo "✅ CACHE PATH FIX: PRESENT"
else
    echo "❌ CACHE PATH FIX: MISSING"
fi
echo ""
echo ""

echo "CHECK #2: Generator Bug (generator.py line 106)"
echo "------------------------------------------------------"
UPSIDE_LINE=$(grep -n "p\['upside'\]" ./courtdominion-app/automation/generator.py)
echo "$UPSIDE_LINE"
echo ""

if [ -n "$UPSIDE_LINE" ]; then
    echo "❌ GENERATOR BUG: STILL PRESENT (needs fix)"
else
    echo "✅ GENERATOR BUG: FIXED"
fi
echo ""
echo ""

echo "=============================================="
echo "  SUMMARY"
echo "=============================================="
if echo "$CACHE_LINE" | grep -q "/data/outputs/player_stats_cache.json" && [ -z "$UPSIDE_LINE" ]; then
    echo "✅ ALL FIXES APPLIED - Ready to rebuild and test"
elif echo "$CACHE_LINE" | grep -q "/data/outputs/player_stats_cache.json"; then
    echo "⚠️  CACHE FIX OK - Generator needs fix on line 106"
elif [ -z "$UPSIDE_LINE" ]; then
    echo "⚠️  GENERATOR FIX OK - Cache path needs fix on line 17"
else
    echo "❌ BOTH FIXES NEEDED"
fi
echo ""
