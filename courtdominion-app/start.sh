#!/bin/bash

################################################################################
# Quick Start Script (No Rebuild)
#
# Purpose: Just start the application (no rebuild)
# Usage: ./start.sh
#
# Use this when you haven't changed any code and just want to run it again
# Use ./rebuild.sh if you changed code
################################################################################

echo ""
echo "============================================================"
echo "COURTDOMINION - START"
echo "============================================================"
echo ""

echo "Starting application..."
echo "Press Ctrl+C to stop"
echo ""

docker compose up

echo ""
echo "============================================================"
echo "STOPPED"
echo "============================================================"
echo ""
