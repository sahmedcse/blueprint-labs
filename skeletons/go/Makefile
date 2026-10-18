SHELL := /bin/sh
.DEFAULT_GOAL := gate

BIN        := bin/__NAME__
GOOSE      ?= go run github.com/pressly/goose/v3/cmd/goose@v3.27.0
SQLC       ?= go run github.com/sqlc-dev/sqlc/cmd/sqlc@v1.31.1

.PHONY: gate lint test build generate migrate hooks

## gate: everything CI runs. scripts/gate.sh in the control repo calls this.
gate: lint test build

## lint: gofmt check, go vet, and golangci-lint when it is installed.
lint:
	@unformatted="$$(gofmt -l .)"; \
	if [ -n "$$unformatted" ]; then echo "gofmt needed on:"; echo "$$unformatted"; exit 1; fi
	go vet ./...
	@if command -v golangci-lint >/dev/null 2>&1; then \
		echo "golangci-lint run"; golangci-lint run; \
	else \
		echo "NOTE: golangci-lint not installed; ran gofmt and go vet only (CI runs it)"; \
	fi

## test: unit tests always; integration tests only when DATABASE_URL is set.
test:
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "SKIP: DATABASE_URL not set, integration tests will be skipped (unit tests still run)"; \
	else \
		echo "DATABASE_URL set: running unit and integration tests"; \
	fi
	go test -race -count=1 ./...

## build: compile every package and the service binary.
build:
	go build ./...
	CGO_ENABLED=0 go build -trimpath -o $(BIN) ./cmd/__NAME__

## generate: regenerate internal/store from db/queries and db/migrations.
generate:
	$(SQLC) generate

## migrate: apply goose migrations to DATABASE_URL.
migrate:
	@if [ -z "$$DATABASE_URL" ]; then echo "DATABASE_URL is required"; exit 1; fi
	$(GOOSE) -dir db/migrations postgres "$$DATABASE_URL" up

## hooks: use the repo's git hooks (commit-msg checks Conventional Commits).
hooks:
	git config core.hooksPath .githooks
