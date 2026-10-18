"""SQLAlchemy models. Alembic migrations are the source of truth for the schema."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Text, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class NoteRow(Base):
    __tablename__ = "notes"
    __table_args__ = (CheckConstraint("length(body) between 1 and 500", name="notes_body_length"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
