"""Repositories map rows to domain objects so the domain never sees SQLAlchemy."""

from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from __PKG__.db.models import NoteRow
from __PKG__.domain.notes import Note, normalize_body


def _to_domain(row: NoteRow) -> Note:
    return Note(id=row.id, body=row.body, created_at=row.created_at, updated_at=row.updated_at)


class NoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, body: str) -> Note:
        stmt = insert(NoteRow).values(body=normalize_body(body)).returning(NoteRow)
        row = (await self._session.execute(stmt)).scalar_one()
        return _to_domain(row)

    async def get(self, note_id: UUID) -> Note | None:
        row = await self._session.scalar(select(NoteRow).where(NoteRow.id == note_id))
        return _to_domain(row) if row is not None else None

    async def delete(self, note_id: UUID) -> None:
        await self._session.execute(delete(NoteRow).where(NoteRow.id == note_id))
