#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: AUTO MERGE PR ]======${NC}"

if ! command -v gh >/dev/null 2>&1; then
  echo -e "${RED}ERROR: GitHub CLI (gh) is not installed.${NC}"
  exit 1
fi

cd "$(dirname "$0")/.." || exit 1

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo -e "${RED}[ERROR] You're on main — nothing to merge.${NC}"
  exit 1
fi

echo -e "${YELLOW}>> Looking up PR for branch: $CURRENT_BRANCH${NC}"
PR_JSON=$(gh pr list --head "$CURRENT_BRANCH" --state open --json number,url -q '.[0]')

if [ -z "$PR_JSON" ] || [ "$PR_JSON" = "null" ]; then
  echo -e "${RED}[ERROR] No open PR found for branch: $CURRENT_BRANCH${NC}"
  exit 1
fi

PR_NUMBER=$(echo "$PR_JSON" | awk -F'"' '/number/ {print $4}')
PR_URL=$(echo "$PR_JSON" | awk -F'"' '/url/ {print $4}')

echo -e "${YELLOW}>> Found PR #${PR_NUMBER}: ${PR_URL}${NC}"

# Attempt to merge with squash and delete remote branch
echo -e "${YELLOW}>> Merging PR (#${PR_NUMBER}) with squash...${NC}"
gh pr merge "$PR_NUMBER" --squash --delete-branch --admin

echo -e "${GREEN}>> PR merged and remote branch deleted.${NC}"

# Optionally delete local branch
echo -e "${YELLOW}>> Deleting local branch: $CURRENT_BRANCH${NC}"
git checkout main || true
git pull --ff-only origin main || true
git branch -D "$CURRENT_BRANCH" || true

echo -e "${GREEN}>> Local branch deleted.${NC}"
echo -e "${GREEN}===========================================================${NC}"
