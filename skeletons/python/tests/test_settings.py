import pytest
from pydantic import ValidationError

from __PKG__.settings import Settings


@pytest.mark.parametrize(
    ("given", "want"),
    [
        ("postgres://app:pw@db:5432/app", "postgresql+asyncpg://app:pw@db:5432/app"),
        ("postgresql://app:pw@db/app", "postgresql+asyncpg://app:pw@db/app"),
        ("postgresql+asyncpg://app@db/app", "postgresql+asyncpg://app@db/app"),
        ("postgres://app@db/app?sslmode=disable", "postgresql+asyncpg://app@db/app?ssl=disable"),
    ],
)
def test_database_url_uses_asyncpg(given: str, want: str) -> None:
    assert Settings(database_url=given).database_url == want


def test_rejects_non_postgres_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="mysql://app@db/app")


def test_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
