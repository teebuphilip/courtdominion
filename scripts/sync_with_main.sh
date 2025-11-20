#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: SYNC WITH MAIN ]======${NC}"
cd "$(dirname "$0")/.." || exit 1

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo -e "${RED}[ERROR] You are on main — sync should be run from a feature branch.${NC}"
  exit 1
fi

echo -e "${YELLOW}>> Fetching origin...${NC}"
git fetch origin

echo -e "${YELLOW}>> Rebasing $CURRENT_BRANCH on origin/main${NC}"
git rebase origin/main

echo -e "${YELLOW}>> Pushing rebased branch with --force-with-lease${NC}"
git push --force-with-lease

echo -e "${GREEN}>> Sync complete.${NC}"
echo -e "${GREEN}===========================================================${NC}"
