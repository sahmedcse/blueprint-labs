# __NAME__ (Go service)

A product repo managed from the blueprint-labs **control repo**. The binding rules live there in
`conventions/go.md` and `conventions/postgres.md`, and `principles/PRINCIPLES.md` applies to every
change. Read them before you start. This file only covers what is specific to this repo.

## Stack

Go 1.25, Chi router, pgx/v5, sqlc for queries, goose for migrations, `log/slog` for logs.

## Layout

| Path | What lives there |
|---|---|
| `cmd/__NAME__/main.go` | Wiring only: config from env, store, router, graceful shutdown. |
| `internal/config/` | Typed config loaded from env at startup. Fails fast on missing values. |
| `internal/http/` | Router, middleware, handlers and their DTOs. Handlers stay thin. |
| `internal/<domain>/` | Business logic. No HTTP or SQL types. Add one per bounded context. |
| `internal/store/` | sqlc-generated code (do not edit by hand) plus thin wrappers in `store.go`. |
| `db/migrations/` | goose migrations, forward only, embedded via `db/db.go`. |
| `db/queries/` | sqlc `.sql` files. Run `make generate` after editing them or a migration. |

## The gate

`make gate` runs `lint`, `test` and `build`. The control repo's `scripts/gate.sh` calls it and its
exit code is the only verdict.

- `lint`: `gofmt -l` must be empty, `go vet`, then `golangci-lint run` when it is installed.
- `test`: `go test -race ./...`. The integration test in `internal/store/` needs `DATABASE_URL`
  and skips without it. That is the only skip allowed. Never add another.
- `build`: compiles every package and `bin/__NAME__`.

To run the integration test locally against an ephemeral Postgres:

```sh
docker run -d --rm --name __NAME__-pg -p 55432:5432 -e POSTGRES_PASSWORD=pw postgres:16
export DATABASE_URL='postgres://postgres:pw@localhost:55432/postgres?sslmode=disable'
make migrate gate
docker stop __NAME__-pg
```

## Commits

Small, single-purpose Conventional Commits, about 200 changed lines at most. A behavior and its
test go in the same commit. Migrations, regenerated sqlc code and `go.sum` changes go in their own
commits. Run `make hooks` once so `.githooks/commit-msg` checks every message. Never amend,
squash, force-push or use `--no-verify`.
