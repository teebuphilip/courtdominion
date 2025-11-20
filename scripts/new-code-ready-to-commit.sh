#!/usr/bin/env bash
set -e

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
CYAN="\033[0;36m"
RESET="\033[0m"

cd "$(git rev-parse --show-toplevel)"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

chmod +x scripts/auto_merge_pr.sh

echo -e "${BLUE}=== COURTDOMINION GIT WORKFLOW: NEW CODE READY ===${RESET}"

echo -e "${CYAN}Step 1: Auto-merging old PR (if exists)...${RESET}"
scripts/auto_merge_pr.sh || true

echo -e "${CYAN}Step 2: Cleaning up old feature branch: ${YELLOW}$CURRENT_BRANCH${RESET}"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    git push origin --delete "$CURRENT_BRANCH" 2>/dev/null || true
    git branch -D "$CURRENT_BRANCH" 2>/dev/null || true
fi

echo -e "${CYAN}Step 3: Creating new feature branch...${RESET}"
NEW_BRANCH="feature-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$NEW_BRANCH"
echo -e "${GREEN}Created branch: $NEW_BRANCH${RESET}"

echo -e "${CYAN}Step 4: Adding changes...${RESET}"
git add .

TEMPLATE="Auto-update: $(date +'%Y-%m-%d %H:%M') | branch: $NEW_BRANCH"
git commit -m "$TEMPLATE"

echo -e "${CYAN}Step 5: Pushing...${RESET}"
git push -u origin "$NEW_BRANCH"

echo -e "${CYAN}Step 6: Opening PR...${RESET}"
gh pr create --fill

echo -e "${GREEN}✨ New PR created for $NEW_BRANCH${RESET}"
