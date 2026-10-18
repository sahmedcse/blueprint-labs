# Python service conventions

**Stack**: Python 3.12+, FastAPI, pydantic v2, SQLAlchemy 2 (async), Alembic, uv, ruff, mypy
(strict), pytest.

## Layout
```
src/<service>/main.py        app factory and router mounting only
src/<service>/api/           routers + request/response schemas (pydantic; match contract)
src/<service>/domain/        business logic; no FastAPI or SQLAlchemy imports
src/<service>/db/            models, session, repositories
migrations/                  alembic
tests/
```

## Rules
- Use FastAPI dependencies for DB sessions and auth. No module-level sessions.
- Settings come from `pydantic-settings`, loaded once and validated at startup.
- Use async all the way down. Never call blocking I/O in a request path.
- Tests: pytest + httpx AsyncClient, with Postgres in an ephemeral container.
- Gate: `uv run ruff check && uv run ruff format --check && uv run mypy && uv run pytest`.
