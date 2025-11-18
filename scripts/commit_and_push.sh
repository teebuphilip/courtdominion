#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: COMMIT & PUSH ]======${NC}"

if [ -z "${1:-}" ]; then
  echo -e "${RED}ERROR: Missing commit message.${NC}"
  echo "USAGE: ./scripts/commit_and_push.sh "commit message""
  exit 1
fi

MESSAGE="$1"

cd "$(dirname "$0")/.." || exit 1

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Safety: prevent committing on main
if [ "$CURRENT_BRANCH" = "main" ]; then
  echo -e "${RED}[FATAL] Refusing to commit on 'main'. Switch to a feature branch.${NC}"
  exit 1
fi

echo -e "${YELLOW}>> Staging changes...${NC}"
git add .

# Check if there is anything to commit
if git diff --cached --quiet; then
  echo -e "${YELLOW}>> Nothing to commit.${NC}"
else
  echo -e "${YELLOW}>> Committing: ${MESSAGE}${NC}"
  git commit -m "$MESSAGE"
fi

echo -e "${YELLOW}>> Pushing branch: ${CURRENT_BRANCH}${NC}"
git push --set-upstream origin "$CURRENT_BRANCH"

echo -e "${GREEN}>> Commit & push complete.${NC}"
echo -e "${GREEN}===========================================================${NC}"
