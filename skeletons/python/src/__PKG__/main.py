"""App factory and router mounting only."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from __PKG__.api import health
from __PKG__.db.session import make_engine, make_sessionmaker
from __PKG__.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Run with: uvicorn --factory __PKG__.main:create_app"""
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings.database_url)
        app.state.sessionmaker = make_sessionmaker(engine)
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(title="__NAME__", lifespan=lifespan)
    app.include_router(health.router)
    return app
