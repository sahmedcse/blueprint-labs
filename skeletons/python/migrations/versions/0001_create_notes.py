"""create notes

Revision ID: 0001
Revises:
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        create function set_updated_at() returns trigger
        language plpgsql as $$
        begin
            new.updated_at = now();
            return new;
        end;
        $$
        """
    )
    op.create_table(
        "notes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("length(body) between 1 and 500", name="notes_body_length"),
    )
    op.create_index("notes_created_at_idx", "notes", ["created_at"])
    op.execute(
        """
        create trigger notes_set_updated_at
            before update on notes
            for each row execute function set_updated_at()
        """
    )


def downgrade() -> None:
    # Migrations only go forward (conventions/postgres.md). Fix forward with a new revision.
    raise NotImplementedError("forward-only migration")
