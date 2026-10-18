"""Integration tests against a real, ephemeral Postgres.

These are the only tests allowed to skip, and only when DATABASE_URL is unset (see the Makefile).
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession

from __PKG__.db.repositories import NoteRepository
from __PKG__.db.session import make_engine, make_sessionmaker
from __PKG__.main import create_app
from __PKG__.settings import Settings

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set: skipping integration test"
    ),
]

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def settings() -> Settings:
    """Apply every migration once (idempotent), then hand out the settings."""
    settings = Settings(database_url=os.environ["DATABASE_URL"])
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
    command.upgrade(config, "head")
    return settings


@pytest.fixture
async def session(settings: Settings) -> AsyncIterator[AsyncSession]:
    engine = make_engine(settings.database_url)
    try:
        async with make_sessionmaker(engine)() as session:
            yield session
            await session.rollback()
    finally:
        await engine.dispose()


async def test_note_round_trip(session: AsyncSession) -> None:
    repo = NoteRepository(session)

    created = await repo.create("  buy oat milk ")
    got = await repo.get(created.id)

    assert got is not None
    assert got == created
    assert got.body == "buy oat milk"
    assert got.created_at.tzinfo is not None

    await repo.delete(created.id)
    assert await repo.get(created.id) is None


async def test_healthz_with_real_database(settings: Settings) -> None:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
