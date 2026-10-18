# blueprint-labs' own checks. Product repos have their own Makefiles (from skeletons/).
PYTEST = uv run -q --no-project --with pytest pytest -q

.PHONY: test commits check
test:            ## all factory tests: review system, scripts, hooks, bin
	$(PYTEST) review/tests scripts/tests .claude/hooks/tests bin/tests

commits:         ## small, conventional commits since main (or since the first commit on main)
	scripts/commit-check.sh . $${BASE:-$$(git merge-base origin/main HEAD 2>/dev/null || git rev-list --max-parents=0 HEAD)}

check: test commits
