.PHONY: lint typecheck test build gate hooks

lint:
	pnpm lint

typecheck:
	pnpm typecheck

test:
	pnpm test

build:
	pnpm build

# The gate the control repo's scripts call. Order matters: cheapest checks first.
gate:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	$(MAKE) build

# Point git at the committed hooks (commit-msg enforces Conventional Commits).
hooks:
	git config core.hooksPath .githooks
