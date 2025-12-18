SHELL := /bin/bash

.PHONY: new-code auto-merge

new-code:
	@chmod +x scripts/new-code-ready-to-commit.sh
	@scripts/new-code-ready-to-commit.sh

auto-merge:
	@chmod +x scripts/auto_merge_pr.sh
	@scripts/auto_merge_pr.sh
