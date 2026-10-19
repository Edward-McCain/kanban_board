from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_board"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "board_columns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("column_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("owner", sa.String(length=40), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high')", name="card_priority"),
        sa.ForeignKeyConstraint(["column_id"], ["board_columns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cards_column_id", "cards", ["column_id"])


def downgrade() -> None:
    op.drop_index("ix_cards_column_id", table_name="cards")
    op.drop_table("cards")
    op.drop_table("board_columns")
