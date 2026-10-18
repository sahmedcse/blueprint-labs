# Go service conventions

**Stack**: Go (latest stable), Chi router, pgx/v5, sqlc for queries, goose for migrations,
`log/slog` for logs, testify only where it truly helps.

## Layout
```
cmd/<service>/main.go     wiring only: config, deps, server start
internal/http/            handlers, middleware, request/response DTOs (JSON tags match contract)
internal/<domain>/        business logic. No HTTP or SQL types here.
internal/store/           sqlc-generated code + thin repository wrappers
db/migrations/            goose migrations
db/queries/               sqlc .sql files
```

## Rules
- Pass context everywhere. Never use package-level DB handles or mutable globals.
- Wrap errors: `fmt.Errorf("load cart %s: %w", id, err)`. Map them to HTTP status in one place.
- Handlers are thin: decode, validate, call the domain, encode.
- Read config from env vars at startup into a typed struct. Fail fast when something is missing.
- Tests: table-driven unit tests, plus integration tests against an ephemeral Postgres.
- Gate: `gofmt -l . (empty) && go vet ./... && golangci-lint run && go test -race ./...`.
