#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m"

echo -e "${GREEN}======[ COURTDOMINION GIT WORKFLOW: TAG RELEASE ]======${NC}"

if [ -z "${1:-}" ]; then
  echo -e "${RED}ERROR: Missing tag. Usage: ./scripts/tag_release.sh v1.2.3${NC}"
  exit 1
fi

TAG="$1"
cd "$(dirname "$0")/.." || exit 1

echo -e "${YELLOW}>> Creating annotated tag: ${TAG}${NC}"
git tag -a "$TAG" -m "Release $TAG"

echo -e "${YELLOW}>> Pushing tag to origin${NC}"
git push origin "$TAG"

echo -e "${GREEN}>> Tag pushed: $TAG${NC}"
echo -e "${GREEN}===========================================================${NC}"
