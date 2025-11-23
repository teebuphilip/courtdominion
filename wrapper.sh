#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: FULL PIPELINE ]======${NC}"

if [ -z "${1:-}" ]; then
  echo -e "${RED}ERROR: Missing branch name.${NC}"
  echo "USAGE: ./wrapper.sh <branch-name> [commit-message] [--tag vX.Y.Z] [--reviewers a,b] [--labels x,y]"
  exit 1
fi

BRANCH="$1"
COMMIT_MSG="${2:-Update on $BRANCH}"
shift 2 || true

# parse remaining optional args
TAG=""
REVIEWERS=""
LABELS=""
while [ "${1:-}" != "" ]; do
  case "$1" in
    --tag)
      TAG="$2"; shift 2;;
    --reviewers)
      REVIEWERS="$2"; shift 2;;
    --labels)
      LABELS="$2"; shift 2;;
    *)
      shift;;
  esac
done

# Step 1: create branch (create_branch auto-syncs main)
echo -e "${YELLOW}>> Step 1: Creating branch: $BRANCH${NC}"
./scripts/create_branch.sh "$BRANCH"

echo ""
echo -e "${YELLOW}>> Step 2: PAUSE — edit your files. Press ENTER when done...${NC}"
read -r

# Step 3: Sync before commit (optional safety)
echo -e "${YELLOW}>> Step 3: Syncing with main (rebase)${NC}"
./scripts/sync_with_main.sh || true

# Step 4: Commit & push
echo -e "${YELLOW}>> Step 4: Commit & push${NC}"
./scripts/commit_and_push.sh "$COMMIT_MSG"

# Step 5: Create PR (pass reviewers/labels if provided)
echo -e "${YELLOW}>> Step 5: Create PR${NC}"
if [ -n "$REVIEWERS" ] || [ -n "$LABELS" ]; then
  ./scripts/create_pr.sh "" "" "$REVIEWERS" "$LABELS"
else
  ./scripts/create_pr.sh
fi

# Step 6: Try to auto-merge (best-effort)
echo -e "${YELLOW}>> Step 6: Attempt auto-merge${NC}"
./scripts/auto_merge_pr.sh || echo -e "${YELLOW}>> Auto-merge failed or requires manual intervention. PR still exists.${NC}"

# Step 7: Optional tag
if [ -n "$TAG" ]; then
  echo -e "${YELLOW}>> Step 7: Tagging release: $TAG${NC}"
  ./scripts/tag_release.sh "$TAG"
fi

echo ""
echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW COMPLETE ]======${NC}"
echo -e "${GREEN}You can go back to watching basketball. 🏀${NC}"
