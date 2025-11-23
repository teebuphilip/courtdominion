#!/bin/bash

################################################################################
# Quick Rebuild and Start Script
#
# Purpose: Rebuild Docker containers and start the application
# Usage: ./rebuild.sh
#
# This script saves you from typing the same commands over and over
################################################################################

echo ""
echo "============================================================"
echo "COURTDOMINION - REBUILD AND START"
echo "============================================================"
echo ""

# Stop any running containers
echo "Step 1: Stopping containers..."
docker compose down
echo "✓ Containers stopped"
echo ""

# Rebuild with no cache (ensures fresh build)
echo "Step 2: Rebuilding containers (this takes ~60 seconds)..."
docker compose build --no-cache
echo "✓ Containers rebuilt"
echo ""

# Start the application
echo "Step 3: Starting application..."
echo ""
echo "Press Ctrl+C to stop"
echo ""
docker compose up

# If user pressed Ctrl+C, clean up
echo ""
echo "============================================================"
echo "STOPPED"
echo "============================================================"
echo ""
