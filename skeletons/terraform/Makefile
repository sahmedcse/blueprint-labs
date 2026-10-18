SHELL := /bin/sh
.DEFAULT_GOAL := gate

TERRAFORM ?= terraform
TFLINT    ?= tflint
ENVS      := $(wildcard envs/*)
MODULES   := $(wildcard modules/*)

# This Makefile never runs plan, apply or destroy. Applying is a human step.
.PHONY: gate fmt validate lint hooks

## gate: everything CI runs. scripts/gate.sh in the control repo calls this.
gate: fmt validate lint

## fmt: every .tf file must already be formatted.
fmt:
	$(TERRAFORM) fmt -check -recursive

## validate: init without a backend (no state, no credentials) and validate each root.
validate:
	@set -e; for dir in $(ENVS) $(MODULES); do \
		echo "== validate $$dir"; \
		$(TERRAFORM) -chdir=$$dir init -backend=false -input=false -no-color >/dev/null; \
		$(TERRAFORM) -chdir=$$dir validate -no-color; \
	done

## lint: tflint over every env and module, when tflint is installed.
lint:
	@if command -v $(TFLINT) >/dev/null 2>&1; then \
		set -e; \
		$(TFLINT) --init --config "$(CURDIR)/.tflint.hcl"; \
		$(TFLINT) --recursive --config "$(CURDIR)/.tflint.hcl"; \
		echo "tflint: no issues"; \
	else \
		echo "SKIP: tflint not installed, lint skipped (CI runs it)"; \
	fi

## hooks: use the repo's git hooks (commit-msg checks Conventional Commits).
hooks:
	git config core.hooksPath .githooks
