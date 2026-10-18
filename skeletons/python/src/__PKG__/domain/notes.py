"""Notes: the example domain. Replace it with your first real one."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

MAX_BODY_LENGTH = 500


class InvalidNoteError(ValueError):
    """The note breaks a business rule."""


@dataclass(frozen=True, slots=True)
class Note:
    id: UUID
    body: str
    created_at: datetime
    updated_at: datetime


def normalize_body(body: str) -> str:
    """Trim whitespace and enforce the length rule the database also checks."""
    cleaned = body.strip()
    if not cleaned:
        raise InvalidNoteError("note body must not be empty")
    if len(cleaned) > MAX_BODY_LENGTH:
        raise InvalidNoteError(f"note body must be at most {MAX_BODY_LENGTH} characters")
    return cleaned
