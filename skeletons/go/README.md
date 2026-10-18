# __NAME__

Go HTTP service (Chi, pgx, sqlc, goose) backed by Postgres.

## Run it

```sh
export DATABASE_URL='postgres://postgres:pw@localhost:5432/__NAME__?sslmode=disable'
make migrate        # apply db/migrations with goose
make build
./bin/__NAME__      # listens on :8080
curl localhost:8080/healthz
```

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `DATABASE_URL` | yes | | Postgres connection string |
| `HTTP_ADDR` | no | `:8080` | Listen address |
| `LOG_LEVEL` | no | `info` | `debug`, `info`, `warn` or `error` |
| `SHUTDOWN_TIMEOUT` | no | `10s` | Grace period for in-flight requests |

`GET /healthz` returns `200 {"status":"ok"}` when the database answers a ping, and
`503 {"status":"unavailable"}` when it does not.

## Develop

| Command | What it does |
|---|---|
| `make gate` | lint, test and build: what CI runs |
| `make generate` | regenerate `internal/store` with sqlc |
| `make migrate` | apply migrations to `DATABASE_URL` |
| `make hooks` | enable the Conventional Commits `commit-msg` hook |

Integration tests run only when `DATABASE_URL` is set. CI sets it with a Postgres service container.

## Container

```sh
docker build -t __NAME__ .
docker run --rm -p 8080:8080 -e DATABASE_URL=... __NAME__
```
