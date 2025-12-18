#!/bin/bash
# Refresh NBA Stats Cache
# Run this nightly or when you want fresh data

set -e

echo "🏀 Refreshing NBA Stats Cache..."
echo ""
echo "This will take 20-30 minutes."
echo "You can run this in the background and forget about it."
echo ""

# Run cache builder
python3 build_cache.py

echo ""
echo "✅ Cache refresh complete!"
echo ""
echo "Your automation will now use the updated cache."
