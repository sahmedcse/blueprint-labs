SHELL := /bin/sh
.DEFAULT_GOAL := gate

UV ?= uv

.PHONY: gate install lint test build migrate run hooks

## gate: everything CI runs. scripts/gate.sh in the control repo calls this.
gate: lint test build

## install: create .venv from uv.lock exactly (fails if the lock is stale).
install:
	$(UV) sync --locked

## lint: ruff lint, ruff format check, mypy strict.
lint: install
	$(UV) run ruff check
	$(UV) run ruff format --check
	$(UV) run mypy

## test: unit tests always; integration tests only when DATABASE_URL is set.
test: install
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "SKIP: DATABASE_URL not set, integration tests will be skipped (unit tests still run)"; \
	else \
		echo "DATABASE_URL set: running unit and integration tests"; \
	fi
	$(UV) run pytest -rs

## build: build the wheel and sdist into dist/.
build: install
	$(UV) build --quiet

## migrate: apply Alembic migrations to DATABASE_URL.
migrate: install
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	$(UV) run alembic upgrade head

## run: start the API on :8000 with reload.
run: install
	$(UV) run uvicorn --factory __PKG__.main:create_app --reload

## hooks: use the repo's git hooks (commit-msg checks Conventional Commits).
hooks:
	git config core.hooksPath .githooks
