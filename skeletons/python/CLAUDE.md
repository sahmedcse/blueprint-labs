# __NAME__ (Python service)

A product repo managed from the blueprint-labs **control repo**. The binding rules live there in
`conventions/python.md` and `conventions/postgres.md`, and `principles/PRINCIPLES.md` applies to
every change. Read them before you start. This file only covers what is specific to this repo.

## Stack

Python 3.12, uv, FastAPI, pydantic v2 + pydantic-settings, SQLAlchemy 2 (async, asyncpg), Alembic,
ruff, mypy (strict), pytest + httpx.

## Layout

| Path | What lives there |
|---|---|
| `src/__PKG__/main.py` | App factory (`create_app`) and router mounting only. |
| `src/__PKG__/settings.py` | pydantic-settings, loaded once and validated at startup. |
| `src/__PKG__/api/` | Routers and their pydantic request/response schemas (match the contract). |
| `src/__PKG__/domain/` | Business logic. No FastAPI or SQLAlchemy imports. |
| `src/__PKG__/db/` | Models, engine/session wiring (a FastAPI dependency) and repositories. |
| `migrations/` | Alembic, async `env.py`. Revisions go forward only. |
| `tests/` | Unit tests. `tests/integration/` needs a real Postgres. |

## The gate

`make gate` runs `lint`, `test` and `build`. The control repo's `scripts/gate.sh` calls it and its
exit code is the only verdict.

- `lint`: `ruff check`, `ruff format --check`, `mypy` (strict, over src, tests and migrations).
- `test`: `pytest`. Tests in `tests/integration/` need `DATABASE_URL` and skip without it. That is
  the only skip allowed. Never add another.
- `build`: `uv build` (wheel and sdist into `dist/`).

Every target runs `uv sync --locked` first, so a stale `uv.lock` fails the gate.

To run the integration tests locally against an ephemeral Postgres:

```sh
docker run -d --rm --name __NAME__-pg -p 55432:5432 -e POSTGRES_PASSWORD=pw postgres:16
export DATABASE_URL='postgres://postgres:pw@localhost:55432/postgres'
make migrate gate
docker stop __NAME__-pg
```

## Commits

Small, single-purpose Conventional Commits, about 200 changed lines at most. A behavior and its
test go in the same commit. Migrations and `uv.lock` changes go in their own commits. Run
`make hooks` once so `.githooks/commit-msg` checks every message. Never amend, squash, force-push
or use `--no-verify`.
