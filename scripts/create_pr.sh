#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: CREATE PR ]======${NC}"

if ! command -v gh >/dev/null 2>&1; then
  echo -e "${RED}ERROR: GitHub CLI (gh) is not installed.${NC}"
  echo "Install with: brew install gh"
  exit 1
fi

# Accept optional title/body/reviewers/labels via env or args
PR_TITLE="${1:-}"
PR_BODY="${2:-}"
REVIEWERS="${3:-}"   # comma-separated
LABELS="${4:-}"      # comma-separated

cd "$(dirname "$0")/.." || exit 1

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ]; then
  echo -e "${RED}[FATAL] You're on 'main' — won't create a PR from main.${NC}"
  exit 1
fi

# Default title/body if not supplied
if [ -z "$PR_TITLE" ]; then
  PR_TITLE="Auto PR: $CURRENT_BRANCH"
fi
if [ -z "$PR_BODY" ]; then
  PR_BODY="Automated PR created by COURTDOMINION GIT WORKFLOW."
fi

echo -e "${YELLOW}>> Ensuring branch is pushed...${NC}"
git push --set-upstream origin "$CURRENT_BRANCH"

echo -e "${YELLOW}>> Creating PR (base: main, head: $CURRENT_BRANCH)${NC}"

# Build gh command with optional reviewers/labels
GH_CMD=(gh pr create --base main --head "$CURRENT_BRANCH" --title "$PR_TITLE" --body "$PR_BODY")

if [ -n "$REVIEWERS" ]; then
  IFS=',' read -ra RARR <<< "$REVIEWERS"
  for r in "${RARR[@]}"; do
    GH_CMD+=(--reviewer "$r")
  done
fi

if [ -n "$LABELS" ]; then
  IFS=',' read -ra LARR <<< "$LABELS"
  for l in "${LARR[@]}"; do
    GH_CMD+=(--label "$l")
  done
fi

"${GH_CMD[@]}"

echo -e "${GREEN}>> PR created successfully.${NC}"
echo -e "${GREEN}===========================================================${NC}"
