.PHONY: install branch sync commit pr merge tag workflow

install:
	@echo "Making scripts executable..."
	chmod +x scripts/*.sh
	chmod +x wrapper.sh
	@echo "Done."

branch:
	./scripts/create_branch.sh $(name)

sync:
	./scripts/sync_with_main.sh

commit:
	./scripts/commit_and_push.sh "$(msg)"

pr:
	./scripts/create_pr.sh

merge:
	./scripts/auto_merge_pr.sh

tag:
	./scripts/tag_release.sh $(tag)

workflow:
	./wrapper.sh $(name) "$(msg)"
