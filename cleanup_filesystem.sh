#!/bin/bash
# Filesystem Cleanup Script
# Organizes CourtDominion project before git baseline commit

echo "=============================================="
echo "  COURTDOMINION FILESYSTEM CLEANUP"
echo "=============================================="
echo ""

# Create docs directory for documentation
echo "Creating docs/ directory..."
mkdir -p docs/planning
mkdir -p docs/architecture
mkdir -p docs/context

# Move planning docs
echo "Moving planning documents..."
mv budget docs/planning/ 2>/dev/null
mv user_acquistion docs/planning/ 2>/dev/null
mv pmo docs/planning/ 2>/dev/null

# Move architecture docs
echo "Moving architecture documents..."
mv architecture docs/ 2>/dev/null

# Move context docs
echo "Moving context documents..."
mv chatgpt-context docs/context/ 2>/dev/null
mv claude-context docs/context/ 2>/dev/null

# Archive old frontend
echo "Archiving old frontend..."
mkdir -p archive
mv old-frontend-archive archive/ 2>/dev/null

# Remove duplicate docker-setup (already in courtdominion-app)
echo "Removing duplicate docker-setup..."
rm -rf docker-setup

# Remove junk files
echo "Removing junk files..."
rm -f junk.out
rm -f jjj.sh
rm -f cache-build.log
#rm -f wrapper.sh
#rm -f quick-start.sh

# Remove old shared-outputs (mock data)
echo "Removing old mock data..."
rm -rf courtdominion-app/shared-outputs

# Create data/outputs/.gitkeep (so directory exists in git)
echo "Creating data/outputs/.gitkeep..."
mkdir -p data/outputs
touch data/outputs/.gitkeep

echo ""
echo "=============================================="
echo "  CLEANUP COMPLETE"
echo "=============================================="
echo ""
echo "Organized:"
echo "  ✓ Planning docs → docs/planning/"
echo "  ✓ Architecture docs → docs/architecture/"
echo "  ✓ Context docs → docs/context/"
echo "  ✓ Old frontend → archive/"
echo ""
echo "Removed:"
echo "  ✓ Duplicate docker-setup/"
echo "  ✓ Junk files (junk.out, jjj.sh, etc.)"
echo "  ✓ Old mock data (shared-outputs/)"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Add files: git add ."
echo "  3. Commit: git commit -m 'Baseline: Production-ready backend'"
echo ""
