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

echo -e "${BLUE}=== COURTDOMINION GIT WORKFLOW: AUTO MERGE ===${RESET}"
echo -e "${CYAN}Checking for open PRs associated with branch: ${YELLOW}$CURRENT_BRANCH${RESET}"

PR_URL=$(gh pr list --head "$CURRENT_BRANCH" --json url --jq '.[0].url' || true)

if [[ -z "$PR_URL" ]]; then
    echo -e "${YELLOW}No PR found for branch ${CURRENT_BRANCH}. Nothing to merge.${RESET}"
    exit 0
fi

echo -e "${CYAN}Found PR: ${GREEN}$PR_URL${RESET}"

echo -e "${CYAN}Attempting squash merge...${RESET}"
if gh pr merge --squash --delete-branch "$PR_URL"; then
    echo -e "${GREEN}PR successfully merged with squash!${RESET}"

    TAG="v$(date +%Y.%m.%d-%H%M)"
    echo -e "${CYAN}Creating version tag: ${GREEN}$TAG${RESET}"

    git fetch origin main
    git checkout main
    git pull

    git tag "$TAG"
    git push origin "$TAG"

    echo -e "${GREEN}Tag $TAG pushed to origin.${RESET}"
else
    echo -e "${RED}Auto-merge failed or requires manual intervention. PR still exists.${RESET}"
    exit 1
fi
