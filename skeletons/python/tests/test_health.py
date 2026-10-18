from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy.exc import OperationalError

from __PKG__.db.session import get_session
from __PKG__.main import create_app
from __PKG__.settings import Settings


class FakeSession:
    def __init__(self, error: Exception | None) -> None:
        self._error = error

    async def execute(self, *_: object) -> None:
        if self._error is not None:
            raise self._error


@pytest.mark.parametrize(
    ("error", "want_status", "want_body"),
    [
        (None, 200, {"status": "ok"}),
        (OperationalError("select 1", {}, OSError("refused")), 503, {"status": "unavailable"}),
        (ConnectionRefusedError("refused"), 503, {"status": "unavailable"}),
    ],
    ids=["database reachable", "database error", "database unreachable"],
)
async def test_healthz(
    error: Exception | None, want_status: int, want_body: dict[str, str]
) -> None:
    app = create_app(Settings(database_url="postgresql://unused@localhost/unused"))

    async def fake_session() -> AsyncIterator[FakeSession]:
        yield FakeSession(error)

    app.dependency_overrides[get_session] = fake_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")

    assert response.status_code == want_status
    assert response.json() == want_body
