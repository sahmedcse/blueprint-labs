# __NAME__

Python HTTP service (FastAPI, SQLAlchemy 2 async, Alembic) backed by Postgres, managed with uv.

## Run it

```sh
export DATABASE_URL='postgres://postgres:pw@localhost:5432/__NAME__'
make migrate        # alembic upgrade head
make run            # uvicorn on :8000 with reload
curl localhost:8000/healthz
```

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `DATABASE_URL` | yes | | Postgres URL. `postgres://` and `postgresql://` are rewritten for asyncpg. |
| `LOG_LEVEL` | no | `info` | Log level |

`GET /healthz` returns `200 {"status":"ok"}` when the database answers `select 1`, and
`503 {"status":"unavailable"}` when it does not.

## Develop

| Command | What it does |
|---|---|
| `make gate` | lint (ruff, mypy strict), test (pytest) and build: what CI runs |
| `make migrate` | apply Alembic migrations to `DATABASE_URL` |
| `uv run alembic revision -m "add orders"` | start a new migration in `migrations/versions/` |
| `make hooks` | enable the Conventional Commits `commit-msg` hook |

Integration tests in `tests/integration/` run only when `DATABASE_URL` is set. CI sets it with a
Postgres service container.

## Container

```sh
docker build -t __NAME__ .
docker run --rm -p 8000:8000 -e DATABASE_URL=... __NAME__
```
