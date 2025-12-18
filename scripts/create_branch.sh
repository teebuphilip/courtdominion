#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: CREATE BRANCH ]======${NC}"

if [ -z "${1:-}" ]; then
  echo -e "${RED}ERROR: Missing branch name.${NC}"
  echo "USAGE: ./scripts/create_branch.sh <branch-name>"
  exit 1
fi

BRANCH="$1"

# Move to repo root (script lives in scripts/)
cd "$(dirname "$0")/.." || exit 1

# Auto-sync main before creating branch (safety)
echo -e "${YELLOW}>> Ensuring origin/main is up to date (auto-sync)${NC}"
git fetch origin
# Ensure local main exists
if git rev-parse --verify main >/dev/null 2>&1; then
  git checkout main
  git pull --ff-only origin main || true
else
  echo -e "${YELLOW}>> No local main branch found; creating tracking branch main from origin/main${NC}"
  git checkout -b main --track origin/main
fi

echo -e "${YELLOW}>> Creating and switching to new branch: ${BRANCH}${NC}"
git checkout -b "$BRANCH"

echo -e "${GREEN}>> Branch created: $BRANCH${NC}"
echo -e "${GREEN}===========================================================${NC}"
